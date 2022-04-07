#include "slab_api.h"

#define DEVICE_NAME "slab_api_dev"
#define CLASS_NAME "slab_api_class"

//#define SLAB_API_DEBUG
// Comment this out to use the custom cache solution
#define USE_REAL

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Max Ufer");
MODULE_DESCRIPTION(
    "IOCTL api for allocating/deallocating objects in kernel space");
MODULE_VERSION("0.01");

static int majorNumber;
static int open_count = 0;
static struct class *slab_api_class;
static struct device *slab_api_device;
static void *allocations[MAX_ALLOCS];
static void *defrag_allocations[MAX_ALLOCS];
static void *fst;
static void *snd;

// Your own personal test_cache
static struct kmem_cache *test_cache;

static int dev_open(struct inode *, struct file *);
static int dev_release(struct inode *, struct file *);
static ssize_t dev_read(struct file *, char *, size_t, loff_t *);
static ssize_t dev_write(struct file *, const char *, size_t, loff_t *);
static long dev_unlocked_ioctl(struct file *, unsigned int, unsigned long);

static long slab_api_kmalloc(slab_params_t *params);
static long slab_api_kcalloc(slab_params_t *params);
static long slab_api_krealloc(slab_params_t *params);
static long slab_api_kfree(slab_params_t *params);
static long slab_api_kfree_all(void);
static long slab_api_defrag_free_all(void);
static long slab_api_defrag_alloc(slab_params_t *params);
static long slab_api_alloc_fst(slab_params_t *params);
static long slab_api_alloc_snd(slab_params_t *params);
static long slab_api_create_cache(void);
static long slab_api_destroy_cache(void);

static struct file_operations fops = {
    .open = dev_open,
    .read = dev_read,
    .write = dev_write,
    .release = dev_release,
    .unlocked_ioctl = dev_unlocked_ioctl,
};

static int __init slab_api_init(void) {
    printk(KERN_INFO "[slab_api] loaded! \n");
    majorNumber = register_chrdev(0, DEVICE_NAME, &fops);
    if (majorNumber < 0) {
        printk(KERN_ALERT "[slab_api] problem registering device...\n");
        return majorNumber;
    }
    printk(KERN_INFO "[slab_api] device registered successfully\n");
    slab_api_class = class_create(THIS_MODULE, CLASS_NAME);

    if (IS_ERR(slab_api_class)) {
        unregister_chrdev(majorNumber, DEVICE_NAME);
        printk(KERN_ALERT "[slab_api] failed to register device\n");
        return PTR_ERR(slab_api_class);
    }
    slab_api_device = device_create(
        slab_api_class, NULL, MKDEV(majorNumber, 0), NULL, DEVICE_NAME);
    if (IS_ERR(slab_api_device)) {
        class_destroy(slab_api_class);
        unregister_chrdev(majorNumber, DEVICE_NAME);
        printk(KERN_ALERT "[slab_api] failed to register device\n");
        return PTR_ERR(slab_api_class);
    }
    printk(KERN_INFO "[slab_api] device has been successfully created \n");
    #ifdef SLAB_API_DEBUG
    printk(KERN_ALERT "[slab_api] Debug mode, enabled debug output. Might change behaviour \n");
    #endif
#ifdef USE_REAL
    printk(KERN_INFO "[slab_api] Using actual kmalloc allocations\n");
#else
    printk(KERN_INFO "[slab_api] Using custom_cache\n");
#endif
    return 0;
}

static void __exit slab_api_exit(void) {
    device_destroy(slab_api_class, MKDEV(majorNumber, 0));
    class_unregister(slab_api_class);
    class_destroy(slab_api_class);
    unregister_chrdev(majorNumber, DEVICE_NAME);
    slab_api_kfree_all();
    slab_api_defrag_free_all();
    printk(KERN_INFO "[slab_api] unloaded and device destroyed...\n");
}

static int dev_open(struct inode *inode, struct file *filep) {
    //printk(KERN_INFO "[slab_api] device opened \n");
    open_count++;
    return 0;
}

static ssize_t dev_read(struct file *filep, char *buffer, size_t len,
                        loff_t *offset) {
    printk(KERN_ALERT "[slab_api] Read operation not defined...\n");
    return -EPERM;
}

static ssize_t dev_write(struct file *filep, const char *buffer, size_t len,
                         loff_t *offset) {
    printk(KERN_ALERT "[slab_api] Write operation not defined...\n");
    return -EPERM;
}

static int dev_release(struct inode *inodep, struct file *filep) {
    //printk(KERN_INFO "[slab_api] device released \n");
    open_count--;
    return 0;
}

static long dev_unlocked_ioctl(struct file *file, unsigned int cmd,
                               unsigned long arg) {
    int error = 0;
    slab_params_t params;
    //printk(KERN_INFO "[slab_api] ioctl cmd: %u\n", cmd);
    if ((slab_params_t *)arg != NULL &&
        copy_from_user(&params, (slab_params_t *)arg,
                       sizeof(slab_params_t))) {
        printk(KERN_ALERT "[slab_api] Failed to import parameters\n");
        return -EFAULT;
    }
    switch (cmd) {
        case SLAB_KMALLOC:
            error = slab_api_kmalloc(&params);
            break;
        case SLAB_KCALLOC:
            error = slab_api_kcalloc(&params);
            break;
        case SLAB_KREALLOC:
            error = slab_api_krealloc(&params);
            break;
        case SLAB_KFREE:
            error = slab_api_kfree(&params);
            break;
        case SLAB_GET_MAX_ALLOCS:
            return MAX_ALLOCS;
        case SLAB_KFREE_ALL:
            error = slab_api_kfree_all();
            break;
        case SLAB_DEFRAG_ALLOC:
            error = slab_api_defrag_alloc(&params);
            break;
        case SLAB_DEFRAG_FREE_ALL:
            error = slab_api_defrag_free_all();
            break;
        case SLAB_ALLOC_FST:
            error = slab_api_alloc_fst(&params);
            break;
        case SLAB_ALLOC_SND:
            error = slab_api_alloc_snd(&params);
            break;
        case SLAB_CREATE_CACHE:
            error = slab_api_create_cache();
            break;
        case SLAB_DESTROY_CACHE:
            error = slab_api_destroy_cache();
            break;
        default:
            error = -EINVAL;
            break;
    }
    if (error == 0) {
        error = copy_to_user((slab_params_t *)arg, &params,
                             sizeof(slab_params_t));
    }
    return error;
}

static long slab_api_kmalloc(slab_params_t *params) {
    if (params->ID >= MAX_ALLOCS) {
        printk(KERN_ALERT
               "[slab_api] kmalloc: ID %d is to high, maximum ID is %d\n",
               params->ID, MAX_ALLOCS);
        return -EINVAL;
    }
    if (allocations[params->ID] != NULL) {
        printk(KERN_ALERT
               "[slab_api] kmalloc: ID %d is already in use\n",
               params->ID);
        return -EINVAL;
    }
#ifdef USE_REAL
    allocations[params->ID] = kmalloc(params->size, GFP_KERNEL);
#else
    allocations[params->ID] = kmem_cache_alloc(test_cache, GFP_KERNEL);
#endif
    if (allocations[params->ID] != NULL) {
        #ifdef SLAB_API_DEBUG
        //printk(KERN_INFO "[slab_api] kmalloc: Allocation for ID %d of size %ld, addresss %llx\n", params->ID, params->size, allocations[params->ID]);
        printk(KERN_INFO "[slab_api] test_cache kmalloc: Allocation for ID %d of size %ld, addresss %llx\n", params->ID, sizeof(struct alloc_struct), allocations[params->ID]);
        #endif
        params->addr = (unsigned long)allocations[params->ID];
        return 0;
    } else {
        printk(KERN_ALERT
               "[slab_api] kmalloc: Allocation for ID %d of size %ld failed!\n",
               params->ID, params->size);
        return -EFAULT;
    }
}

static long slab_api_defrag_alloc(slab_params_t *params) {
    if (params->ID >= MAX_ALLOCS) {
        printk(KERN_ALERT
               "[slab_api] defrag kmalloc: ID %d is to high, maximum ID is %d\n",
               params->ID, MAX_ALLOCS);
        return -EINVAL;
    }
    if (defrag_allocations[params->ID] != NULL) {
        printk(KERN_ALERT
               "[slab_api] defrag kmalloc: ID %d is already in use\n",
               params->ID);
        return -EINVAL;
    }
    defrag_allocations[params->ID] = kmalloc(params->size, GFP_KERNEL);
    if (defrag_allocations[params->ID] != NULL) {
        //printk(KERN_INFO "[slab_api] defrag kmalloc: Allocation for ID %d of size %ld, addresss %llx\n", params->ID, params->size, allocations[params->ID]);
        params->addr = (unsigned long)defrag_allocations[params->ID];
        return 0;
    } else {
        printk(KERN_ALERT
               "[slab_api] defrag kmalloc: Allocation for ID %d of size %ld failed!\n",
               params->ID, params->size);
        return -EFAULT;
    }
}

static long slab_api_kcalloc(slab_params_t *params) {
    if (params->ID >= MAX_ALLOCS) {
        printk(KERN_ALERT
               "[slab_api] kcalloc: ID %d is to high, maximum ID is %d\n",
               params->ID, MAX_ALLOCS);
        return -EINVAL;
    }
    if (allocations[params->ID] != NULL) {
        printk(KERN_ALERT
               "[slab_api] kcalloc: ID %d is already in use\n",
               params->ID);
        return -EINVAL;
    }
    allocations[params->ID] =
        kcalloc(params->nmemb, params->size, GFP_KERNEL);
    if (allocations[params->ID] != NULL) {
        //printk(KERN_INFO "[slab_api] kcalloc: Allocation for ID %d of size %ld with %ld members\n", params->ID, params->size, params->nmemb);
        return 0;
    } else {
        printk(KERN_ALERT
               "[slab_api] kcalloc: Allocation for ID %d of size %ld with %ld members failed!\n",
               params->ID, params->size, params->nmemb);
        return -EFAULT;
    }
}
static long slab_api_krealloc(slab_params_t *params) {
    if (params->ID >= MAX_ALLOCS) {
        printk(KERN_ALERT
               "[slab_api] krealloc: ID %d is to high, maximum ID is %d\n",
               params->ID, MAX_ALLOCS);
        return -EINVAL;
    }
    if (allocations[params->oldID] == NULL) {
        printk(KERN_ALERT
               "[slab_api] krealloc: oldID %d is not in use so it can't be reallocated\n",
               params->ID);
        return -EINVAL;
    }
    if (allocations[params->ID] != NULL) {
        printk(KERN_ALERT
               "[slab_api] krealloc: ID %d is already in use\n",
               params->ID);
        return -EINVAL;
    }
    allocations[params->ID] =
        krealloc(allocations[params->oldID], params->size, GFP_KERNEL);
    if (allocations[params->ID] == NULL) {
        printk(KERN_ALERT
               "[slab_api] krealloc: Reallocation for ID %d, oldID %d of size %ld failed!\n",
               params->ID, params->oldID, params->size);
        return -EINVAL;
    } else {
        allocations[params->oldID] = NULL;
        //printk(KERN_INFO "[slab_api] krealloc: Reallocated ID %d, oldID %d of size %ld\n", params->ID, params->oldID, params->size);
        return 0;
    }
}
static long slab_api_kfree(slab_params_t *params) {
    if (params->ID >= MAX_ALLOCS) {
        printk(KERN_ALERT
               "[slab_api] kfree: ID %d is to high, maximum ID is %d\n",
               params->ID, MAX_ALLOCS);
        return -EINVAL;
    }
    if (allocations[params->ID] == NULL) {
        printk(KERN_ALERT "[slab_api] kfree: ID %d is not in use\n",
               params->ID);
        return -EINVAL;
    }
#ifdef USE_REAL
    kfree(allocations[params->ID]);
#else
    kmem_cache_free(test_cache, allocations[params->ID]);
#endif
    #ifdef SLAB_API_DEBUG
    printk(KERN_INFO "[slab_api] kfree: Freed ID %d Address: %llx\n", params->ID, allocations[params->ID]);
    #endif
    allocations[params->ID] = NULL;
    return 0;
}

static long slab_api_kfree_all() {
    uint index, count = 0;
    for (index = 0; index < MAX_ALLOCS; index++) {
        if (allocations[index] != NULL) {
#ifdef USE_REAL
            kfree(allocations[index]);
#else
            kmem_cache_free(test_cache, allocations[index]);
#endif
            allocations[index] = NULL;
            count++;
        }
    }
    if (fst != NULL) {
#ifdef USE_REAL
        kfree(fst);
#else
        kmem_cache_free(test_cache, fst);
#endif
        fst = NULL;
        count++;
    }
    if (snd != NULL) {
#ifdef USE_REAL
        kfree(snd);
#elif
        kmem_cache_free(test_cache, snd);
#endif
        snd = NULL;
        count++;
    }
    #ifdef SLAB_API_DEBUG
    printk(KERN_INFO "[slab_api] Freed all objects (%d in total)\n", count);
    #endif
    return 0;
}

static long slab_api_defrag_free_all() {
    uint index, count = 0;
    for (index = 0; index < MAX_ALLOCS; index++) {
        if (defrag_allocations[index] != NULL) {
            kfree(defrag_allocations[index]);
            defrag_allocations[index] = NULL;
            count++;
        }
    }
    #ifdef SLAB_API_DEBUG
    printk(KERN_INFO "[slab_api] Freed all defrag objects (%d in total)\n",
           count);
    #endif
    return 0;
}

static long slab_api_alloc_fst(slab_params_t *params) {
    if (fst != NULL) {
        printk(KERN_ALERT
               "[slab_api] alloc fst: Already in use\n");
        return -EINVAL;
    }
#ifdef USE_REAL
    fst = kmalloc(params->size, GFP_KERNEL);
#else
    fst = kmem_cache_alloc(test_cache, GFP_KERNEL);
#endif
    if (fst != NULL) {
        #ifdef SLAB_API_DEBUG
        //printk(KERN_INFO "[slab_api] alloc fst: Allocation of size %ld, addresss %llx\n", params->size, fst);
        printk(KERN_INFO "[slab_api] test_cache alloc fst: Allocation of size %ld, addresss %llx\n", sizeof(struct alloc_struct), fst);
        #endif
        params->addr = (unsigned long)fst;
        return 0;
    } else {
        printk(KERN_ALERT
               "[slab_api] alloc fst: Allocation of size %ld failed!\n",
               params->size);
        return -EFAULT;
    }
}
static long slab_api_alloc_snd(slab_params_t *params) {
    if (snd != NULL) {
        printk(KERN_ALERT
               "[slab_api] alloc snd: Already in use\n");
        return -EINVAL;
    }
#ifdef USE_REAL
    snd = kmalloc(params->size, GFP_KERNEL);
#else
    snd = kmem_cache_alloc(test_cache, GFP_KERNEL);
#endif
    if (snd != NULL) {
        #ifdef SLAB_API_DEBUG
        //printk(KERN_INFO "[slab_api] alloc snd: Allocation of size %ld, addresss %llx\n", params->size, snd);
        printk(KERN_INFO "[slab_api] test_cache alloc snd: Allocation of size %ld, addresss %llx\n", sizeof(struct alloc_struct), snd);
        #endif
        params->addr = (unsigned long)snd;
        return 0;
    } else {
        printk(KERN_ALERT
               "[slab_api] alloc snd: Allocation of size %ld failed!\n",
               params->size);
        return -EFAULT;
    }
}
static long slab_api_create_cache(){
    test_cache = KMEM_CACHE(alloc_struct, SLAB_PANIC);
    if(test_cache == NULL){
        printk(KERN_ALERT "Failed to create cache");
        return -EFAULT;
    }
    #ifdef SLAB_API_DEBUG
    printk(KERN_INFO "[slab_api] allocated test cache");
    #endif
    return 0;
}

static long slab_api_destroy_cache(){
    kmem_cache_destroy(test_cache);
    test_cache = NULL;
    #ifdef SLAB_API_DEBUG
    printk(KERN_INFO "[slab_api] destroyed test cache");
    #endif
    return 0;

}


module_init(slab_api_init);
module_exit(slab_api_exit);
