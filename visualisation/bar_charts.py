#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import argparse


def change_alpha_value_of_column(rects, start_value):
    children_id = start_value
    while (children_id < 7):
        rects.get_children()[children_id].set_alpha(0.1)
        children_id += 1

def extrapolate_prs_candidates(prs,prs_len):
    while (prs_len < 7):
        prs.append(100000)
        prs_len += 1
     
    return prs
    


def create_plot(n_groups, kevoheap, prs,candidate_file):
    
    prs_len= len(prs)
    extrapolate_prs_candidates(prs,prs_len)
    
    
    # create plot
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.25
    opacity = 0.8
    
    rects1 = plt.bar(index, kevoheap, bar_width,
                     alpha=opacity,
                     color='b',
                     label='KEvoHeap')
    
    rects2 = plt.bar(index + bar_width, prs, bar_width,
                     alpha=0.9,
                     color='r',
                     label='Pseudo-random search')

        
    change_alpha_value_of_column(rects2, prs_len)  
    
    
    plt.xlabel('Noise')
    plt.ylabel('Candidates')
    plt.title('Bar chart showing the average generations needed in both algorithms with respect to the level of noise: %s' %candidate_file)
    plt.xticks(index + bar_width, ('0', '1', '2', '3', '4', '5','6'))
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=5)
    plt.tight_layout()
    
    ax2 = ax.twinx()
    ax2.set_ylim(0,250)
    ax2.set_ylabel('Generations')
    
    plt.show()


# data to plot
n_groups = 7 #number of max noise
kevoheap=[]
prs=[]


# Here it begins
parser = argparse.ArgumentParser(description="Plot a bar chart based on the results!")
parser.add_argument("candidates", type=str, nargs=1, help="The candidat list to use")
args = parser.parse_args()

candidate_file = args.candidates[0]

with open(candidate_file) as f:
    candidates = f.readlines()
    for candidate in candidates:
        if candidate.split(' ')[1].startswith("prs"):
            prs.append(int(candidate.split(' ')[0]))
        else:
            kevoheap.append(int(candidate.split(' ')[0]))
    
    

create_plot(n_groups, kevoheap, prs,candidate_file)


