# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 15:29:26 2020

@author: super
"""

from itertools import groupby

def calc_freq(times):
    times2 = [t for t in times if t is not None]
    time_f = [len(list(group)) for key, group in groupby(sorted(times2))]
    nr_instruments = max(time_f)
    freq_array = time_f*nr_instruments
    freq_array2 = []
    offset = 0
    for i,t in enumerate(times):
        if t is None:
            freq_array2.append(0)
            offset += 1
        else:
            freq_array2.append(freq_array[i-offset])
    return freq_array2

def fix_staff_relations(staffs):
    times = [s.nr_timewise for s in staffs]
    instruments = [s.nr_instrument for s in staffs if s.nr_instrument is not None]
    nr_instruments = max(instruments)
    
    freq_array2 = calc_freq(times)
            
    added_times = []
    for i in range(len(freq_array2)):
        if freq_array2[i] == 0:
            if freq_array2[i-1] == nr_instruments:
                times[i] = times[i-nr_instruments]+1
                added_times.append(times[i])
            else:
                times[i] = times[i-1]
            freq_array2 = calc_freq(times)
        else:
            times[i] = times[i] + len(list(set(added_times)))
    
    instrs = []
    ini = 0
    inst = 0
    for i in range(len(times)):
        if times[i] == ini:
            inst += 1
        else:
            inst = 1
            ini = times[i]
        instrs.append(inst)
        staffs[i].nr_timewise = times[i]
        staffs[i].nr_instrument = inst
    
    return instrs
        