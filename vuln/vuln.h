#include <linux/device.h>
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/mm.h>

#define VULN_ALLOC_TARGET 1001
#define VULN_ALLOC_OVERFLOW 1002
#define VULN_CALL 1003
#define VULN_COPY_TO_BUF 1004
#define VULN_PRINT_BUF 1005
#define VULN_DEBUG 1006

typedef struct target {
    void (*some_func)(void);
    char some_data[248];
} target_t;

typedef struct vuln_params {
    char *input;
    size_t len;
} vuln_params_t;
