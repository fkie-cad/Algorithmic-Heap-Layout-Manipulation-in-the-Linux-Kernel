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
#include <linux/fs.h>

#define VULN_ALLOC_TARGET 1001
#define VULN_ALLOC_OVERFLOW 1002

/* per-instance private data */
struct my_data {
	bool trace;
};

static bool fst_triggered = false;
static bool snd_triggered = false;
static uint fst_position = 3;
static uint snd_position = 1;
static uint fst_counter = 0;
static uint snd_counter = 0;
static unsigned long fst_addr;
static unsigned long snd_addr;


static void write_distance_to_tmp(void){
	struct file *f = NULL;
	char buf[20];
	pr_info("[infoleak] Writing distance to file");
	sprintf(buf, "%lld\n", (long long)fst_addr - (long long)snd_addr);

	f = filp_open("/tmp/dist", O_WRONLY | O_CREAT, S_IRWXUGO);
	if(IS_ERR(f)){
		pr_info("[infoleak] Failed to open /tmp/dist!");
		return;
	}
	kernel_write(f, buf, strlen(buf), 0);
	filp_close(f, NULL);
	return;
}

static int entry_handler_kmalloc(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	struct my_data *data;
	size_t size;

	if (!current->mm)
		return 1;	/* Skip kernel threads */

	data = (struct my_data *)ri->data;
	size = (size_t) regs->di;
	if(fst_triggered || snd_triggered) {
		pr_info("[infoleak] Hit kmalloc with size %lu", size);
		if(fst_triggered){
			fst_counter++;
			if(fst_counter == fst_position)
				data->trace = true;
			else
				data->trace = false;
		}
		else{
			snd_counter++;
			if(snd_counter == snd_position)
				data->trace = true;
			else
				data->trace = false;
		}

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
		if(fst_triggered){
			pr_info("[infoleak] vuln at %lx\n", retval);
			fst_addr = retval;
		}
		else{
			pr_info("[infoleak] target at %lx\n", retval);
			snd_addr = retval;
		}
		if(fst_addr != 0 && snd_addr != 0){
			write_distance_to_tmp();
			fst_addr = 0;
			snd_addr = 0;
		}
	}
	return 0;
}
NOKPROBE_SYMBOL(ret_handler_kmalloc);

static int entry_handler_ioctl(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	if (!current->mm)
		return 1;	/* Skip kernel threads */
	if(regs->si == VULN_ALLOC_OVERFLOW){
		fst_triggered = true;
	}else if(regs->si == VULN_ALLOC_TARGET){
		snd_triggered = true;
	}
	return 0;
}
NOKPROBE_SYMBOL(entry_handler_ioctl);

static int ret_handler_ioctl(struct kretprobe_instance *ri, struct pt_regs *regs)
{
	fst_triggered = false;
	snd_triggered = false;
	fst_counter = 0;
	snd_counter = 0;
	return 0;
}
NOKPROBE_SYMBOL(ret_handler_ioctl);


static struct kretprobe kmalloc_kretprobe = {
	.handler		= ret_handler_kmalloc,
	.entry_handler	= entry_handler_kmalloc,
	.data_size		= sizeof(struct my_data),
	/* Probe up to 20 instances concurrently. */
	.maxactive		= 20,
};

static struct kretprobe ioctl_kretprobe = {
	.handler		= ret_handler_ioctl,
	.entry_handler	= entry_handler_ioctl,
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
		pr_err("[infoleak] register_kretprobe failed for kvmalloc_node, returned %d\n", ret);
		return -1;
	}
	pr_info("[infoleak] Planted return probe at %s: %p\n",
			kmalloc_kretprobe.kp.symbol_name, kmalloc_kretprobe.kp.addr);

	ioctl_kretprobe.kp.symbol_name = "vuln_unlocked_ioctl";
	ret = register_kretprobe(&ioctl_kretprobe);
	if (ret < 0) {
		pr_err("[infoleak] register_kretprobe failed for ioctl, returned %d\n", ret);
		return -1;
	}
	pr_info("[infoleak] Planted return probe at %s: %p\n",
			ioctl_kretprobe.kp.symbol_name, ioctl_kretprobe.kp.addr);

	return 0;
}

static void __exit kretprobe_exit(void)
{
	unregister_kretprobe(&kmalloc_kretprobe);
	pr_info("[infoleak] kretprobe at %p unregistered\n", kmalloc_kretprobe.kp.addr);

	/* nmissed > 0 suggests that maxactive was set too low. */
	pr_info("[infoleak] Missed probing %d instances of %s\n",
		kmalloc_kretprobe.nmissed, kmalloc_kretprobe.kp.symbol_name);

	unregister_kretprobe(&ioctl_kretprobe);
	pr_info("[infoleak] kretprobe at %p unregistered\n", ioctl_kretprobe.kp.addr);

	/* nmissed > 0 suggests that maxactive was set too low. */
	pr_info("[infoleak] Missed probing %d instances of %s\n",
		ioctl_kretprobe.nmissed, ioctl_kretprobe.kp.symbol_name);
}

module_init(kretprobe_init)
module_exit(kretprobe_exit)
MODULE_LICENSE("GPL");
