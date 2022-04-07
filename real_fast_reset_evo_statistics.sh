#!/bin/bash

function command_netcat(){
    RES=$( echo "./exec/$(basename $cand) && cat /tmp/dist" | nc -nN 127.0.0.1 44444 )
    if [ -z $RES ]
    then
        echo "error" > ./res/$(basename $cand)
    else
        echo $RES > ./res/$(basename $cand)

    fi
}

function quit_vm(){
    echo "quit" | nc -N 127.0.0.1 55555 >/dev/null && ./qemu_startup_qcow2.sh 2>&1 >/dev/null &
}


RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

TARGET_DISTANCE=-96
ITERATIONS=1000
RESULT_FILES=./res/*
TRIES_FILE=./tries.log
CURRENT_BEST=999999999
NUMBER_OF_TRIES=0

#GLOBAL_RUNS=100
GLOBAL_RUNS=1


echo -e "Number of generations:" > $TRIES_FILE

./qemu_startup_qcow2.sh &
#echo "savevm savestate" | nc -N 127.0.0.1 55555
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
        python3 ./algorithms/evoheap.py
        if [ $? -ne 0 ]; 
        then
            echo -e "$NUMBER_OF_TRIES" >> $TRIES_FILE
            continue 2
        fi
        #compile candidates
        CANDIDATES="./ins"/* 
        for cand in $CANDIDATES
        do
            python3 ./compile_candidate.py -t ./hlm.template ./ins/$(basename $cand)
            if [ $? -ne 0 ];
            then
                echo -e "${RED}Failed to compile $cand!${NC}"
                exit
            fi
        done
        #copy candidates to vm and save state
        ssh -i ./bullseye.id_rsa -p 10021 root@localhost -o "StrictHostKeyChecking no" "rm -rf ./exec" && scp -i ./bullseye.id_rsa -P 10021 -r -o "StrictHostKeyChecking no" ./exec root@localhost:/root/ > /dev/null && \
            echo "savevm savestate" | nc -N 127.0.0.1 55555 > /dev/null
        for cand in $CANDIDATES
        do
            #ssh -i ../../kernel_virtualisation/linux-5.9.7/image/bullseye.id_rsa -p 10021 root@localhost -o "StrictHostKeyChecking no" "cd /home/ && ./kernel_sieve $cand > res/$(basename $cand)" > /dev/null 
            command_netcat
            #scp -i ../../kernel_virtualisation/linux-5.9.7/image/bullseye.id_rsa -P 10021 -r -o "StrictHostKeyChecking no" root@localhost:/home/res/$(basename $cand) ./res/$(basename $cand) > /dev/null 
            #echo "cat res/$(basename $cand)" | nc -nN 127.0.0.1 44444 > ./res/$(basename $cand)
            quit_vm
            echo "Ping..."
            sleep 0.05s
        done

        
        NUMBER_OF_TRIES=$((NUMBER_OF_TRIES + 1))
        echo -e "Going into next gen after $NUMBER_OF_TRIES tries"
    done
    echo -e "${RED}Couldn't find solution${NC}"
    echo -e "-1" >> $TRIES_FILE
done
