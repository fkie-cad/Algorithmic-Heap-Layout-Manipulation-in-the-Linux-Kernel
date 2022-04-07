// SPDX-License-Identifier: GPL-2.0-only
/*
 * kretprobe.c
 *
 * This kretprobe observes all allocations in the target cache 
 * and creations of new slabs
 */

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/ktime.h>
#include <linux/limits.h>
#include <linux/sched.h>
#include <linux/slab.h>


/* per-instance private data */
struct my_data {
	bool trace;
};

static int entry_handler_kmalloc(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	struct my_data *data;

	if (!current->mm)
		return 1;	/* Skip kernel threads */

	data = (struct my_data *)ri->data;
	size_t size = (size_t) regs->di;
	if(size == 256 || size == 255){
		data->trace = true;
	}else{
		data->trace = false;
	}
	return 0;
}
NOKPROBE_SYMBOL(entry_handler_kmalloc);

static int ret_handler_kmalloc(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	unsigned long retval = regs_return_value(regs);
	struct my_data *data = (struct my_data *)ri->data;
	if(data->trace){
		pr_info("kmalloc returned %lx\n", retval);
	}
	return 0;
}
NOKPROBE_SYMBOL(ret_handler_kmalloc);

static int entry_handler_newslab(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	if (!current->mm)
		return 1;	/* Skip kernel threads */

	struct kmem_cache *cache = (struct kmem_cache*) regs->di;
	if(kmem_cache_size(cache) == 256){
		pr_info("New slab with size: %d\n", kmem_cache_size(cache));
	}
	//pr_info("New slab\n");
	return 0;
}
NOKPROBE_SYMBOL(entry_handler_newslab);

static int ret_handler_newslab(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	//Not needed right now, just in case
	return 0;
}
NOKPROBE_SYMBOL(ret_handler_newslab);

static struct kretprobe kmalloc_kretprobe = {
	.handler		= ret_handler_kmalloc,
	.entry_handler	= entry_handler_kmalloc,
	.data_size		= sizeof(struct my_data),
	/* Probe up to 20 instances concurrently. */
	.maxactive		= 20,
};

static struct kretprobe newslab_kretprobe = {
	.handler		= ret_handler_newslab,
	.entry_handler	= entry_handler_newslab,
	.data_size		= sizeof(struct my_data),
	/* Probe up to 20 instances concurrently. */
	.maxactive		= 20,
};

static int __init kretprobe_init(void)
{
	int ret;

	kmalloc_kretprobe.kp.symbol_name = "kvmalloc_node";
	ret = register_kretprobe(&kmalloc_kretprobe);
	if (ret < 0) {
		pr_err("register_kretprobe failed for kmalloc, returned %d\n", ret);
		return -1;
	}
	pr_info("Planted return probe at %s: %p\n",
			kmalloc_kretprobe.kp.symbol_name, kmalloc_kretprobe.kp.addr);
	newslab_kretprobe.kp.symbol_name = "allocate_slab";
	ret = register_kretprobe(&newslab_kretprobe);
	if (ret < 0){
		pr_err("register_kretprobe failed for allocate_slab, returned %d\n", ret);
		return -1;
	}
	pr_info("Planted return probe at %s: %p\n",
			newslab_kretprobe.kp.symbol_name, newslab_kretprobe.kp.addr);
	
	return 0;
}

static void __exit kretprobe_exit(void)
{
	unregister_kretprobe(&kmalloc_kretprobe);
	pr_info("kretprobe at %p unregistered\n", kmalloc_kretprobe.kp.addr);

	/* nmissed > 0 suggests that maxactive was set too low. */
	pr_info("Missed probing %d instances of %s\n",
		kmalloc_kretprobe.nmissed, kmalloc_kretprobe.kp.symbol_name);
}

module_init(kretprobe_init)
module_exit(kretprobe_exit)
MODULE_LICENSE("GPL");
