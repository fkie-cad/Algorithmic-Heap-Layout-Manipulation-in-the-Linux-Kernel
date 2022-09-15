#define _GNU_SOURCE
#include <dirent.h>
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

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

#define BUFSIZE 256

#define SLAB_API_PATH "/dev/slab_api_dev"

//#define USE_CUSTOM
#define USE_REAL

typedef uint id_t;
typedef unsigned long addr_t;

typedef struct slab_params {
    size_t size;
    id_t ID;
    size_t nmemb;
    id_t oldID;
    addr_t addr;
} slab_params_t;

typedef struct cmd {
    unsigned long code;
    slab_params_t params;
    struct cmd *next;
} cmd_t;

static addr_t fst = 0;
static addr_t snd = 0;

void fatal(char *str) {
    fprintf(stderr, "[-] %s\n", str);
    exit(EXIT_FAILURE);
}

//Taken from phrack article (http://phrack.org/issues/64/6.html), reads /proc/slabinfo and calculates offset for allocations
int calculate_slaboff(char *name) {
    FILE *fp;
    char slab[BUFSIZE], line[BUFSIZE];
    int ret;
    /* UP case */
    int active_obj, total;

    bzero(slab, BUFSIZE);
    bzero(line, BUFSIZE);

    fp = fopen("/proc/slabinfo", "r");
    if (fp == NULL)
        fatal("error opening /proc for slabinfo");

    fgets(slab, sizeof(slab) - 1, fp);
    do {
        ret = 0;
        if (!fgets(line, sizeof(line) - 1, fp))
            break;
        ret = sscanf(line, "%s %u %u", slab, &active_obj, &total);
    } while (strcmp(slab, name));

    close(fileno(fp));
    fclose(fp);

    return ret == 3 ? total - active_obj : -1;
}

//bind thread to single cpu, taken from Attacking the core book
static int bindcpu() {
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(0, &set);
    if (sched_setaffinity(0, sizeof(cpu_set_t), &set) < 0) {
        perror("setaffinity");
        return (-1);
    }
    return (0);
}

static cmd_t *read_instructions(char *path) {
    FILE *fp;
    char *line = NULL;
    char buffer[BUFSIZE];
    size_t len = 0;
    ssize_t ret;
    cmd_t *head = NULL, *current = NULL;

    fp = fopen(path, "r");
    if (fp == NULL) {
        fatal("Failed to open instruction file");
    }
    while ((ret = getline(&line, &len, fp)) != -1) {
        cmd_t *cmd = malloc(sizeof(cmd_t));
        if (strncmp(line, "kmalloc", strlen("kmalloc")) == 0) {
            cmd->code = SLAB_KMALLOC;
            ret = sscanf(line, "%*s %lu %u", &(cmd->params.size), &(cmd->params.ID));
        } else if (strncmp(line, "kcalloc", strlen("kcalloc")) == 0) {
            cmd->code = SLAB_KCALLOC;
            ret = sscanf(line, "%*s %lu %lu %u", &(cmd->params.nmemb), &(cmd->params.size), &(cmd->params.ID));
        } else if (strncmp(line, "kfree", strlen("kfree")) == 0) {
            cmd->code = SLAB_KFREE;
            ret = sscanf(line, "%*s %u", &(cmd->params.ID));
        } else if (strncmp(line, "krealloc", strlen("krealloc")) == 0) {
            cmd->code = SLAB_KREALLOC;
            ret = sscanf(line, "%*s %u %lu %u", &(cmd->params.oldID), &(cmd->params.size), &(cmd->params.ID));
        } else if (strncmp(line, "fst", strlen("fst")) == 0) {
            cmd->code = SLAB_ALLOC_FST;
            ret = sscanf(line, "%*s %lu", &(cmd->params.size));
        } else if (strncmp(line, "snd", strlen("snd")) == 0) {
            cmd->code = SLAB_ALLOC_SND;
            ret = sscanf(line, "%*s %lu", &(cmd->params.size));
        } else {
            fprintf(stderr, "[-] Instruction does not start with valid keyword\n");
            return NULL;
        }
        if (head == NULL) {
            head = cmd;
            current = head;
            current->next = NULL; //Have to set this for use after free protextion
        } else {
            current->next = cmd;
            current = current->next;
            current->next = NULL; //Have to set this for use after free protextion
        }
    }

    fclose(fp);
    if (line)
        free(line);
    return head;
}

void write_result(char *ifile_name) {
    FILE *fp;
    char resultfile[BUFSIZE];
    sprintf(resultfile, "./res/%s", ifile_name);
    fp = fopen(resultfile, "w");
    if (fp == NULL) {
        fatal("Failed to open/create result file");
    }
    if (fst == 0 || snd == 0) {
        fprintf(fp, "error\n");
    }else{
        long long distance = (long long)fst - (long long)snd;
        fprintf(fp, "%lld\n", distance);
    }
    fclose(fp);
}

static void free_list(cmd_t *head) {
    cmd_t *next;
    while (head != NULL) {
        next = head->next;
        free(head);
        head = next;
    }
}

static int execute(int fd, cmd_t *cmd_list) {
    int res;
    cmd_t *cur = cmd_list;
    while (cur != NULL) {
        res = ioctl(fd, cur->code, &(cur->params));
        //printf("Request: %lu Error: %d\n", cur->code, res);
        if (res != 0) {
            //ioctl(fd, SLAB_KFREE_ALL, NULL);

            //ioctl(fd, SLAB_DEFRAG_FREE_ALL, NULL);
            //fprintf(stderr, "[-] Failed to execute, kernel error. Instruction: %lu Error: %d\n", cur->code, res);
            //exit(EXIT_FAILURE);
            return -1;

        }
        if (cur->code == SLAB_ALLOC_FST) {
            fst = cur->params.addr;
        } else if (cur->code == SLAB_ALLOC_SND) {
            snd = cur->params.addr;
        }
        cur = cur->next;
    }
    return 0;
}


static void alternate_defragment(int fd, char *slabname, size_t size){
    int diff, cnt, i;
    slab_params_t params;
    params.size = size;
    params.ID = 0;
    diff = calculate_slaboff(slabname);
    cnt = diff * 10;
    for(i = 0; i < cnt; i++){
        diff = calculate_slaboff(slabname);
        if(diff == 0){
            return;
        }else if(diff < 0){
            ioctl(fd, SLAB_DEFRAG_FREE_ALL, NULL);
            close(fd);
            fatal("Failed to calculate diff");
        }
        params.ID = i;
        if (ioctl(fd, SLAB_DEFRAG_ALLOC, &params) != 0){
            ioctl(fd, SLAB_DEFRAG_FREE_ALL, NULL);
            close(fd);
            fatal("Error in kernel while defragging");
        }
    }
    if(diff != 0){
            ioctl(fd, SLAB_DEFRAG_FREE_ALL, NULL);
            close(fd);
            fatal("Failed to defrag slubs");
    }
}


static void defragment(char *slabname, size_t size, uint iterations) {
    int fillup, id, iter, highest = 0;
    int fd = open(SLAB_API_PATH, O_RDONLY);
    if (fd < 0) {
        fatal("Cannot open device file...\n");
    }
    slab_params_t params;
    params.size = size;
    params.ID = 0;

    for (iter = 0; iter < iterations; iter++) {
        fillup = calculate_slaboff(slabname);
        //printf("Fillup is %d\n", fillup);
        fillup += 16;  //give it a little extra
        if (fillup > 0) {
            for (id = 0; id < fillup; id++) {
                params.ID = id + highest + 1;
                if (ioctl(fd, SLAB_DEFRAG_ALLOC, &params) != 0){
                    ioctl(fd, SLAB_DEFRAG_FREE_ALL, NULL);
                    fatal("IOCTL Error\n");
                }
            }
            highest = params.ID;
        }
    }
}

void single_run(char* path){
    cmd_t *cmd_list;
    int fd = open("/dev/slab_api_dev", O_RDONLY);
    if (fd < 0) {
        fatal("Cannot open device file...\n");
    }
    cmd_list = read_instructions(path);
#ifdef USE_REAL
    alternate_defragment(fd, "kmalloc-96", 96);
#else
    ioctl(fd, SLAB_CREATE_CACHE, NULL);
#endif
    int res = execute(fd, cmd_list);
    if(fst == 0 || snd == 0 || res != 0){
        printf("error\n");
    }else{
        long long distance = (long long)fst - (long long)snd;
        printf("%lld\n", distance);
    }
    ioctl(fd, SLAB_KFREE_ALL, NULL);
#ifdef USE_REAL
    ioctl(fd, SLAB_DEFRAG_FREE_ALL, NULL);
#else
    ioctl(fd, SLAB_DESTROY_CACHE, NULL);
#endif
    fst = 0;
    snd = 0;
    free_list(cmd_list);
    exit(EXIT_SUCCESS);
}

int main(int argc, char *argv[]) {
    bindcpu();
    if(argc == 2){
        single_run(argv[1]);
    }

    struct dirent *de;
    DIR *dr = opendir("./ins/");
    cmd_t *cmd_list;
    if (dr == NULL) {
        fatal("Failed to open directory with instructions");
    }
    int fd = open("/dev/slab_api_dev", O_RDONLY);
    if (fd < 0) {
        fatal("Cannot open device file...\n");
    }
    while ((de = readdir(dr)) != NULL) {
        if (strncmp(de->d_name, ".", 1) != 0) {
            char path[BUFSIZE];
            sprintf(path, "./ins/%s", de->d_name);
            cmd_list = read_instructions(path);
            if(cmd_list == NULL){
                fst = 0;
                snd = 0;
            }
            else{
#ifdef USE_REAL
                defragment("kmalloc-256", 256,1);
#else
                ioctl(fd, SLAB_CREATE_CACHE, NULL);
#endif
                int res = execute(fd, cmd_list);
                if (res == -1){
                    fst = 0;
                    snd = 0;
                }
            }
            write_result(de->d_name);
            ioctl(fd, SLAB_KFREE_ALL, NULL);
#ifdef USE_REAL
            ioctl(fd, SLAB_DEFRAG_FREE_ALL, NULL);
#else
            ioctl(fd, SLAB_DESTROY_CACHE, NULL);
#endif
            fst = 0;
            snd = 0;
            free_list(cmd_list);
        }
    }
    close(fd);
    exit(EXIT_SUCCESS);
}
int basic_test() {
    bindcpu();
    int fillup, i;
    addr_t a1, a2, a3, a4, a5, a6, a7, a8;
    int fd = open("/dev/slab_api_dev", O_RDONLY);
    if (fd < 0) {
        fatal("Cannot open device file...\n");
    }
    fillup = calculate_slaboff("kmalloc-512");
    printf("Fillup is %d\n", fillup);
    fillup += 10;
    slab_params_t params;
    params.size = 511;
    params.ID = 0;
    if (fillup > 0) {
        for (i = 0; i < fillup; i++) {
            params.ID = i;
            if (ioctl(fd, SLAB_KMALLOC, &params) != 0) fatal("IOCTL Error\n");
        }
    }
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a1 = params.addr;
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a2 = params.addr;
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a3 = params.addr;
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a4 = params.addr;
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a5 = params.addr;
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a6 = params.addr;
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a7 = params.addr;
    params.ID++;
    ioctl(fd, SLAB_KMALLOC, &params);
    a8 = params.addr;
    printf("%llx\n%llx\n%llx\n%llx\n%llx\n%llx\n%llx\n%llx\n", a1, a2, a3, a4, a5, a6, a7, a8);
    ioctl(fd, SLAB_KFREE_ALL, NULL);
    close(fd);
    return 0;
}
