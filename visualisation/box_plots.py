#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import argparse


  


def create_blox_plot(kevoheap, prs,candidate_file):

    
    fig, ax = plt.subplots()
    
    c = "blue"
    bp1 =ax.boxplot(kevoheap,positions=[1], boxprops=dict(color=c),
            capprops=dict(color=c),
            whiskerprops=dict(color=c),
            flierprops=dict(color=c, markeredgecolor=c),
            medianprops=dict(color=c))

    r = "red"
    bp2 =ax.boxplot(prs,positions=[2], 
                     boxprops=dict(color=r),
            capprops=dict(color=r),
            whiskerprops=dict(color=r),
            flierprops=dict(color=r, markeredgecolor=r),
            medianprops=dict(color=r))
   
    
    ax2 = ax.twinx()
    ax2.set_ylim(0,35)
    ax2.set_ylabel('Generations')
    ax.set_ylabel('Candidates')
    plt.title('Box plot illustrating the distribution of numbers of candidates generated: %s' %candidate_file)
    plt.xticks(np.arange(2)+1, ('KEvoHeap', 'Pseudo-random search'))
    plt.legend([bp1["boxes"][0], bp2["boxes"][0]], ['KEvoHeap', 'Pseudo-random search'], loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=5)
    
    
    plt.show()


# data to plot
kevoheap=[]
prs=[]


# Here it begins
parser = argparse.ArgumentParser(description="Create a box plot based on the results!")
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
    
    

create_blox_plot(kevoheap, prs,candidate_file)


