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

# Delete old tries
rm ./ins/*
rm ./res/*

echo -e "Number of tries:" > $TRIES_FILE


for (( global_counter=1; global_counter <= GLOBAL_RUNS; global_counter++ ))
do
    NUMBER_OF_TRIES=0
    echo -e "[*] Starting try number $global_counter"
    for (( counter=1; counter <= ITERATIONS; counter++ ))
    do
        python3 randomsearch.py -n $NOISE
        ./kernel_sieve
        if [ $? -ne 0 ]; 
        then
            echo -e "${RED} Error in kernel_sieve${NC}"
            exit
        fi
        for res in $RESULT_FILES
        do
            NUMBER_OF_TRIES=$((NUMBER_OF_TRIES + 1))
            dist=$(<$res)
            if [[ "$dist" -eq TARGET_DISTANCE ]];
            then
                echo -e "${GREEN}Found solution in $res after $NUMBER_OF_TRIES tries.${NC}"
                echo -e "$NUMBER_OF_TRIES" >> $TRIES_FILE
                continue 3
            fi
            abs_dist=${dist#-}
            if [[ abs_dist -lt CURRENT_BEST ]];
            then
                CURRENT_BEST=$dist
            fi
        done
        echo -e "Going into next gen, current best: $CURRENT_BEST after $NUMBER_OF_TRIES tries"
    done
    echo -e "${RED}Couldn't find solution, best was $CURRENT_BEST${NC}"
    echo -e "-1" >> $TRIES_FILE
done

