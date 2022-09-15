#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

TARGET_DISTANCE=-96
NOISE=3
ITERATIONS=1000
RESULT_FILES=./res/*
TRIES_FILE=./tries.log
CURRENT_BEST=999999999
NUMBER_OF_TRIES=0

GLOBAL_RUNS=100


echo -e "Number of generations:" > $TRIES_FILE


for (( global_counter=1; global_counter <= GLOBAL_RUNS; global_counter++ ))
do
    NUMBER_OF_TRIES=0
    # Delete old tries
    rm ./ins/*
    rm ./res/*
    rm ./raw/*
    echo -e "[*] Starting try number $global_counter"
    for (( counter=1; counter <= ITERATIONS; counter++ ))
    do
        python3 ./evoheap.py -a ksieve -n $NOISE
        
        if [ $? -ne 0 ]; 
        then
            echo -e "$NUMBER_OF_TRIES" >> $TRIES_FILE
            continue 2
        fi
        ./kernel_sieve
        if [ $? -ne 0 ]; 
        then
            echo -e "${RED} Error in kernel_sieve${NC}"
            exit
        fi
        NUMBER_OF_TRIES=$((NUMBER_OF_TRIES + 1))
        echo -e "Going into next gen after $NUMBER_OF_TRIES tries"
    done
    echo -e "${RED}Couldn't find solution${NC}"
    echo -e "-1" >> $TRIES_FILE
done

