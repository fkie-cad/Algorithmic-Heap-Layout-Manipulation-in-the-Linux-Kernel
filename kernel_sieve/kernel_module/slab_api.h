
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/uaccess.h>

#define SLAB_KMALLOC 1000
#define SLAB_KCALLOC 1001
#define SLAB_KREALLOC 1002
#define SLAB_KFREE 1003
#define SLAB_GET_MAX_ALLOCS 1004
#define SLAB_KFREE_ALL 1005
#define SLAB_DEFRAG_ALLOC 1006
#define SLAB_DEFRAG_FREE_ALL 1007
#define SLAB_ALLOC_FST 1008
#define SLAB_ALLOC_SND 1009
#define SLAB_CREATE_CACHE 1010
#define SLAB_DESTROY_CACHE 1011

#define MAX_ALLOCS 2048
#define ALLOC_SIZE 95

typedef uint id_t;
typedef unsigned long addr_t;

typedef struct slab_params {
    size_t size;
    id_t ID;
    size_t nmemb;
    id_t oldID;
    addr_t addr;
} slab_params_t;

struct alloc_struct {
    char filler[ALLOC_SIZE];
};
