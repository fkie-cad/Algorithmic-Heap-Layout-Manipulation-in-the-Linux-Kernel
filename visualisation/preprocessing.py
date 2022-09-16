#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import math

def get_sorted_logs(file_list,do_box_plot):
    sorted_file_list = []
    file_name = os.path.basename(file_list[0])
    num_of_delimiters = len(file_name.split('_'))

    if num_of_delimiters != 3 and num_of_delimiters != 4:
        if num_of_delimiters == 5 and do_box_plot:
            cnt = file_list[0].count("_") - 1
            return sorted(file_list, key=lambda x: os.path.splitext(x.split('_')[cnt])[0])
            
        print("Error: unknown format\nExiting....")
        exit()
    
    if num_of_delimiters == 3:
        sorted_file_list = sorted(file_list, key=lambda x: os.path.splitext(x.split('_')[2])[0])
    else:
        sorted_file_list = sorted(file_list, key=lambda x: os.path.splitext(x.split('_')[3])[0])
        
    return sorted_file_list
    


def get_file_list(dir_path,do_box_plot):
    file_list = []
    directory = os.fsencode(dir_path)
    
    sorted_dir_list = os.listdir(directory)
    sorted_dir_list.sort()
    
    for file in sorted_dir_list:
        filename = os.fsdecode(file)
        if filename.endswith(".log") and filename[0].isnumeric():
            file_list.append(os.path.join(str(directory,"utf-8"), filename))
            continue
        else:
            continue
        
    file_list = get_sorted_logs(file_list,do_box_plot)
    return file_list
    


def get_average_candidate_solutions(log_file_wihtout_header, candidates):
    average_candidate_solutions = 0
    for candidate_line in log_file_wihtout_header:
        average_candidate_solutions = average_candidate_solutions + int(candidate_line) * candidates
    
    average_candidate_solutions = average_candidate_solutions / len(log_file_wihtout_header)
    return int(math.ceil(average_candidate_solutions))
    


def print_average_candidate_solutions(log_file_wihtout_header,type, candidate_multiplier):
    average_candidate_solutions = get_average_candidate_solutions(log_file_wihtout_header,candidate_multiplier)
    print(f"{average_candidate_solutions} {type}")
    

        
    

# main
type = "unknown"
candidate_multiplier = 1
result_list = []
do_box_plot = False
parser = argparse.ArgumentParser(description="Preprocessing ")
parser.add_argument("logfolder", type=str, nargs=1, help="The folder of the tries.log files")
parser.add_argument("-f", dest="format", metavar="format", type=str, required=False, default="bar", help="Choose which plotting format should be generated: bar (bar chart: default) or box (box plot)")
args = parser.parse_args()


path = args.logfolder[0]

if os.path.isdir(path) == False:
    print(f"Error: {path} does not exist.\nExiting.....")
    
if args.format.lower() == "box":
    do_box_plot = True
    
file_list = get_file_list(path,do_box_plot)


for solution_file in file_list:
    with open(solution_file) as current_log_file:
        log_file = current_log_file.readlines()
        if log_file[0].endswith("tries:\n"):
            candidate_multiplier = 1
            type = "prs"
        else:
            candidate_multiplier = 400
            type = "kevo"
        
        print_average_candidate_solutions(log_file[1:],type,candidate_multiplier)
        



