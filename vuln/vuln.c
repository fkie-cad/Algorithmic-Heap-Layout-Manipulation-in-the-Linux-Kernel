#include "vuln.h"

#define DEVICE_NAME "vuln_dev"
#define CLASS_NAME "vuln_class"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Max Ufer");
MODULE_DESCRIPTION(
    "Example vulnerable kernel module");
MODULE_VERSION("0.01");

static int majorNumber;
static int open_count = 0;
static struct class *vuln_class;
static struct device *vuln_device;

static int my_dev_uevent(struct device *, struct kobj_uevent_env *);
static int vuln_open(struct inode *, struct file *);
static int vuln_release(struct inode *, struct file *);
static ssize_t vuln_read(struct file *, char *, size_t, loff_t *);
static ssize_t vuln_write(struct file *, const char *, size_t, loff_t *);
static long vuln_unlocked_ioctl(struct file *, unsigned int, unsigned long);
static void vuln_copy_buf(vuln_params_t params);
static void vuln_print_buf(void);
static void trigger_call(void);
static void trigger_alloc_overflow(void);
static void trigger_alloc_target(void);
static void failure_func(void);
static void debug_info(void);
static void check_write_dist(void);
static void write_distance_to_tmp(void);

static struct file_operations fops = {
    .open = vuln_open,
    .read = vuln_read,
    .write = vuln_write,
    .release = vuln_release,
    .unlocked_ioctl = vuln_unlocked_ioctl,
};

static target_t *the_target;
static char *noise0;
static char *noise1;
static char *noise2;
static char *noise3;
static char *noise4;
static char *noise5;
static char *buffer;

static int __init vuln_init(void) {
    printk(KERN_INFO "[vuln] loaded! \n");
    majorNumber = register_chrdev(0, DEVICE_NAME, &fops);
    if (majorNumber < 0) {
        printk(KERN_ALERT "[vuln] problem registering device...\n");
        return majorNumber;
    }
    printk(KERN_INFO "[vuln] device registered successfully\n");
    vuln_class = class_create(THIS_MODULE, CLASS_NAME);

    if (IS_ERR(vuln_class)) {
        unregister_chrdev(majorNumber, DEVICE_NAME);
        printk(KERN_ALERT "[vuln] failed to register device\n");
        return PTR_ERR(vuln_class);
    }
    vuln_class->dev_uevent = my_dev_uevent;
    vuln_device = device_create(
        vuln_class, NULL, MKDEV(majorNumber, 0), NULL, DEVICE_NAME);
    if (IS_ERR(vuln_device)) {
        class_destroy(vuln_class);
        unregister_chrdev(majorNumber, DEVICE_NAME);
        printk(KERN_ALERT "[vuln] failed to register device\n");
        return PTR_ERR(vuln_class);
    }
    printk(KERN_INFO "[vuln] device has been successfully created \n");
    return 0;
}

static void __exit vuln_exit(void) {
    if(buffer != NULL) {
        kfree(buffer);
    }
    if(the_target != NULL){
        kfree(the_target);
    }
    if(noise0 != NULL){
        kfree(noise0);
    }
    if(noise1 != NULL){
        kfree(noise1);
    }
    if(noise2 != NULL){
        kfree(noise2);
    }
    if(noise3 != NULL){
        kfree(noise3);
    }
    if(noise4 != NULL){
        kfree(noise4);
    }
    if(noise5 != NULL){
        kfree(noise5);
    }

    device_destroy(vuln_class, MKDEV(majorNumber, 0));
    class_unregister(vuln_class);
    class_destroy(vuln_class);
    unregister_chrdev(majorNumber, DEVICE_NAME);
    printk(KERN_INFO "[vuln] unloaded and device destroyed...\n");
}

static int my_dev_uevent(struct device *dev, struct kobj_uevent_env *env)
{
    add_uevent_var(env, "DEVMODE=%#o", 0666);
    return 0;
}

static int vuln_open(struct inode *inode, struct file *filep) {
    //printk(KERN_INFO "[vuln] device opened \n");
    open_count++;
    return 0;
}

static ssize_t vuln_read(struct file *filep, char *buffer, size_t len,
                        loff_t *offset) {
    printk(KERN_ALERT "[vuln] Read operation not defined...\n");
    return -EPERM;
}

static ssize_t vuln_write(struct file *filep, const char *buffer, size_t len,
                         loff_t *offset) {
    printk(KERN_ALERT "[vuln] Write operation not defined...\n");
    return -EPERM;
}

static int vuln_release(struct inode *inodep, struct file *filep) {
    //printk(KERN_INFO "[vuln] device released \n");
    open_count--;
    return 0;
}

static long vuln_unlocked_ioctl(struct file *file, unsigned int cmd,
                               unsigned long arg) {
    int error = 0;
    vuln_params_t params;
    switch (cmd) {
        case VULN_ALLOC_TARGET:
            trigger_alloc_target();
            break;
        case VULN_ALLOC_OVERFLOW:
            trigger_alloc_overflow();
            break;
        case VULN_CALL:
            trigger_call();
            break;
        case VULN_COPY_TO_BUF:
            if ((vuln_params_t *)arg != NULL &&
                copy_from_user(&params, (vuln_params_t *)arg,
                               sizeof(vuln_params_t))) {
                printk(KERN_ALERT "[vuln] Failed to import parameters\n");
                return -EFAULT;
            }
            vuln_copy_buf(params); 
            break;
        case VULN_PRINT_BUF:
            vuln_print_buf();
            break;
        case VULN_DEBUG:
            debug_info();
            break;
        default:
            error = -EINVAL;
            break;
    }
    return error;
}

static void vuln_copy_buf(vuln_params_t params){
    printk("[vuln] Len: %lu. Buf addr: %lx\n", params.len, (unsigned long)params.input);
    if(copy_from_user(buffer, params.input, params.len)){
        printk(KERN_ALERT "[vuln] Failed to import input\n");
    };
    return;
}

static void vuln_print_buf(void){
    printk(KERN_INFO "[vuln] Content of buffer: %s", buffer);
    return;
}

static void trigger_alloc_overflow(void){
    if(buffer != NULL) {
        kfree(buffer);
    }
    if(noise0 != NULL){
        kfree(noise0);
    }
    if(noise1 != NULL){
        kfree(noise1);
    }
    if(noise2 != NULL){
        kfree(noise2);
    }
    if(noise3 != NULL){
        kfree(noise3);
    }
    if(noise4 != NULL){
        kfree(noise4);
    }
    if(noise5 != NULL){
        kfree(noise5);
    }
    noise0 = kmalloc(sizeof(char)*256, GFP_KERNEL);
    noise1 = kmalloc(sizeof(char)*256, GFP_KERNEL);
    buffer = kmalloc(256*sizeof(char), GFP_KERNEL);
    noise4 = kmalloc(sizeof(char)*256, GFP_KERNEL);
    noise5 = kmalloc(sizeof(char)*256, GFP_KERNEL);
    pr_info("[vuln] fst at: %lx", (unsigned long) buffer);
    //check_write_dist();
    return;
}

static void trigger_alloc_target(){
    if(the_target != NULL){
        kfree(the_target);
    }
    the_target = kmalloc(sizeof(target_t), GFP_KERNEL);
    the_target->some_func = failure_func;
    strcpy(the_target->some_data, "This is data.");
    pr_info("[vuln] snd at: %lx", (unsigned long) the_target);
    //check_write_dist();
    return;
}

static void trigger_call(void){
    if(the_target != NULL){
        printk(KERN_INFO "[vuln] Calling function with address %lx\n", (unsigned long)the_target->some_func);
        the_target->some_func();
    }else{
        printk(KERN_INFO "[vuln] Structure has not been allocated yet.\n");
    }
}

static void failure_func(void){
    printk(KERN_INFO "[vuln] Oooopsie, seems like you failed!\n");
}

static void debug_info(void){
    printk(KERN_INFO "[vuln] Address of noise0: %lx\n", (unsigned long)noise0);
    printk(KERN_INFO "[vuln] Location of buffer: %lx\n", (unsigned long)buffer);
    printk(KERN_INFO "[vuln] Addresse of noise1: %lx\n", (unsigned long)noise1);
    printk(KERN_INFO "[vuln] Location of target: %lx\n", (unsigned long)the_target);
    printk(KERN_INFO "[vuln] Address of target function: %lx\n", (unsigned long)the_target->some_func);
    printk(KERN_INFO "[vuln] Content of some_data: %s", the_target->some_data);
    printk(KERN_INFO "[vuln] Size of target: %ld", sizeof(target_t));
    return;
}

static void check_write_dist(void){
    if(buffer != NULL && the_target != NULL){
        write_distance_to_tmp();
    }
}

static void write_distance_to_tmp(void){
	struct file *f = NULL;
	char buf[20];
	pr_info("[vuln] Writing distance to /tmp/dist");
	sprintf(buf, "%lld\n", (long long)buffer - (long long)the_target);

	f = filp_open("/tmp/dist", O_WRONLY | O_CREAT, S_IRWXUGO);
	if(IS_ERR(f)){
		pr_info("[vuln] Failed to open /tmp/dist!");
		return;
	}
	kernel_write(f, buf, strlen(buf), 0);
	filp_close(f, NULL);
	return;
}

module_init(vuln_init);
module_exit(vuln_exit);
