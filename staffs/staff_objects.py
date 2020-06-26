# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 15:16:26 2020

@author: super
"""

import cv2
import math


class Staff:
    def __init__(self, img_bar):
        self.image = img_bar
        firstlines = self.detect_stafflines(img_bar)
        self.dist = self.calc_avg_distance(firstlines)
        self.lines = sorted(self.calc_higher_lines(self.calc_lower_lines(firstlines,self.dist,img_bar.shape[1]),self.dist,img_bar.shape[1]), key=lambda x: x[1])
        self.divisions = 12
        self.nr_timewise = float('NaN')
        self.nr_instrument = float('NaN')

    def set_bar_nrs(self, nr_timewise, nr_instrument):
        # moet dan voor het splitsen naar maten gedaan worden
        self.nr_timewise = nr_timewise
        self.nr_instrument = nr_instrument

    def calc_avg_distance(self,lines):
        s = [x[1] for x in lines]
        e = [x[3] for x in lines]
        diff_s = [j-i for i, j in zip(s[:-1], s[1:])]
        diff_e = [j-i for i, j in zip(e[:-1], e[1:])]
        ds = sum(diff_s)/len(diff_s)
        de = sum(diff_e)/len(diff_e)
        return(int((ds+de)/2))

    def calc_lower_lines(self,lines,dist,width):
        # create all(4) the lines below the bar
        s = [x[1] for x in lines]
        e = [x[3] for x in lines]

        s_bottom = max(s)
        e_bottom = max(e)

        new_lines = lines.copy()
        for i in range(1,5):
            new_line = [0,s_bottom+(i*dist),width,e_bottom+(i*dist)]
            new_lines.append(new_line)

        return new_lines

    def calc_higher_lines(self,lines,dist,width):
        # create all(4) the lines above the bar
        s = [x[1] for x in lines]
        e = [x[3] for x in lines]

        s_top = min(s)
        e_top = min(e)

        new_lines = lines.copy()
        for i in range(1,5):
            new_line = [0,s_top-(i*dist),width,e_top-(i*dist)]
            new_lines.append(new_line)

        return new_lines

    def calc_y(self,line,x):
        x1 = line[0]
        y1 = line[1]
        x2 = line[2]
        y2 = line[3]

        y = x*(y2-y1)/(x2-x1) + ((x2*y1 - x1*y2)/(x2-x1))
        return int(y)

    def detect_stafflines(self, img_bar):
        height,width = img_bar.shape[:2]
        img_copy = img_bar.copy()

        # Canny edge detection

        img_struct_hor = img_copy.copy()
        hor_size = round(img_struct_hor.shape[1]/30)
        hor_struct = cv2.getStructuringElement(cv2.MORPH_RECT, (hor_size,1))

        img_struct_hor3 = cv2.dilate(img_struct_hor, hor_struct, 1)
        eroted = cv2.erode(img_struct_hor3, hor_struct, 3)

        gray = cv2.cvtColor(eroted, cv2.COLOR_BGR2GRAY)
        (thresh, img_bw) = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        gray2 = cv2.cvtColor(img_bw, cv2.COLOR_GRAY2BGR)

        edges2 = cv2.Canny(gray2, 100,200)

        # Find Hough lines

        # getallen nog aanpassen naar schaalbaar tov img size
        lines = cv2.HoughLinesP(edges2, 1, math.pi/2, 1, None, 50, 10)
#        lines = cv2.HoughLines(edges2, 1, math.pi/2, 1, None)

        # Label useless lines for removal and combine consecutive lines

        for i, linearr in enumerate(lines):
            line = linearr[0]
            pt1 = (line[0],line[1])
            pt2 = (line[2],line[3])
            xlen1 = pt2[0]-pt1[0]
            ylen1 = pt2[1]-pt1[1]
            rot1 = math.degrees(math.atan(ylen1/xlen1))
        #         print('start = %d,%d, end = %d,%d, xlen = %d, ylen = %d'%(pt1[0],pt1[1],pt2[0],pt2[1],xlen1,ylen1))
        #         print(rot1)
            if abs(rot1)>=3:
                lines[i] = [[0,0,0,0]]

        for i, linearr in enumerate(lines):
        #         print(linearr)
            line = linearr[0]
            pt1 = (line[0],line[1])
            pt2 = (line[2],line[3])
            for j, linearr2 in enumerate(lines):
                line2 = linearr2[0]
                pt3 = (line2[0],line2[1])
                pt4 = (line2[2],line2[3])
                if (pt3[0] in range(pt1[0]+1,pt2[0]+2) and pt3[1] in range(pt2[1]-1,pt2[1]+2)):
                    if pt4[0]>pt2[0]:
                        xlen1 = pt2[0]-pt1[0]
                        ylen1 = pt2[1]-pt1[1]
                        xlen2 = pt4[0]-pt3[0]
                        ylen2 = pt4[1]-pt3[1]
                        rot1 = math.degrees(math.atan(ylen1/xlen1))
                        rot2 = math.degrees(math.atan(ylen2/xlen2))
            #             print('%f vs. %f'%(rot1,rot2))
                        if abs(rot1-rot2)<3:
                            lines[j] = [[pt1[0], pt1[1], pt4[0], pt4[1]]]
                            lines[i] = [[0,0,0,0]]
                            break
                    else:
                        lines[j] = [[0,0,0,0]]

        for i, linearr in enumerate(lines):
            line = linearr[0]
            pt1 = (line[0],line[1])
            pt2 = (line[2],line[3])
            xlen1 = pt2[0]-pt1[0]
            if xlen1 < width/4:
                lines[i] = [[0,0,0,0]]

        # Remove labeled lines

        new_lines = []
        for linearr in lines:
            line = linearr[0]
            if line.all() == 0:
                continue
            new_lines.append(line)

        # Stretch lines across entire image

        long_lines = []

        for n, line in enumerate(new_lines):
            new_p1_x = 0
            new_p1_y = self.calc_y(line,new_p1_x)

            new_p2_x = width
            new_p2_y = self.calc_y(line,new_p2_x)

            long_lines.append([new_p1_x, new_p1_y, new_p2_x, new_p2_y])

        # Remove (semi-)duplicate lines

        long_lines = sorted(long_lines, key=lambda x: x[1])
        unique_lines = []

        for i,l in enumerate(long_lines):
            if i==0: continue
            if l[1]-long_lines[i-1][1]>3:
                unique_lines.append(long_lines[i-1])
                if i==len(long_lines)-1:
                    unique_lines.append(l)
            elif i==len(long_lines)-1:
                unique_lines.append(long_lines[i-1])

        for i in range(len(unique_lines)):
            unique_lines[i][1] = unique_lines[i][1]+1
            unique_lines[i][3] = unique_lines[i][3]+1

        return unique_lines

    def set_divisions(self,div):
        self.divisions = div


class Staff_measure:
    Gnotes = ['G','F','E','D','C','B','A']
    Goctave = 6

    def __init__(self, staff, nr, start, end):
        self.lines = staff.lines
        self.dist = staff.dist
        self.measure = nr
        self.start = start
        self.end = end
        self.clef = 'G'
        self.clef_line = 2
        self.key = 0
        self.beats = 4
        self.beat_type = 4
        self.notes = self.Gnotes
        self.octave = self.Goctave
        self.divisions = staff.divisions
        self.staff = staff

    def set_clef(self, clef):
        self.clef = clef

    def set_clef_line(self, clef_line):
        self.clef_line = clef_line

    def set_key(self, key):
        self.key = key

    def set_beats(self, beats):
        self.beats = beats

    def set_beat_type(self, beat_type):
        self.beat_type = beat_type

    def set_time(self, time):
        self.beats = time.beats
        self.beat_type = time.beat_type

    def update_clefnotes(self):
        if self.clef=='G':
            self.clef_line = 2
            self.notes = self.Gnotes
            self.octave = self.Goctave
        elif self.clef=='C':
            self.clef_line = 3
            self.notes = self.Gnotes[6:]+self.Gnotes[:6]
            self.octave = self.Goctave - 1
        elif self.clef=='F':
            self.clef_line = 4
            self.notes = self.Gnotes[5:]+self.Gnotes[:5]
            self.octave = self.Goctave - 2

    def set_divisions(self,div):
        self.divisions = div


class Bar_line:
    def __init__(self,x,y,template):
        self.x = x
        self.y = y
        self.h = template.h
        self.w = template.w


def split_measures(barlines, staff): #barlines sorted on x
    x1, x2 = (0, 0)
    measures = []
    for i in range(0,len(barlines)+1):
        if i==len(barlines): x2 = staff.lines[0][2]
        else: x2 = barlines[i].x
        measures.append(Staff_measure(staff,i,x1,x2))
        x1 = x2


def find_measure(measures, x):
    for measure in measures:
        if x>measure.start and x<measure.end:
            return measure
    return None


class Clef:
    def __init__(self,x,y,template):
        self.x = x
        self.y = y
        self.type = template.name
        self.h = template.h
        self.w = template.w


class Key:
    def __init__(self,grouped_accidentals):
        self.x, self.y, self.h, self.w = self.find_rect(grouped_accidentals) if len(grouped_accidentals)>0 else (0,0,0,0)
        self.type = grouped_accidentals[0].type if len(grouped_accidentals)>0 else 'normal'
        self.key = self.find_key(grouped_accidentals)
        self.accidentals = grouped_accidentals

    def find_rect(self,group):
        minx, miny = (group[0].x, group[0].y)
        maxx, maxy = (minx, miny)
        for acc in group:
            minx = min(minx, acc.x)
            maxx = max(maxx, acc.x + acc.w)
            miny = min(miny, acc.y)
            maxy = max(maxy, acc.y + acc.h)
        w = maxx - minx
        h = maxy - miny
        return minx, miny, w, h

    def find_key(self,group):
        amount = len(group)
        if self.type == 'flat':
            return -1*amount
        elif self.type == 'sharp':
            return amount
        elif amount==0:
            return 0
        else:
            return float('NaN')


class Time:
    timedict = {'3/4 time':(3,4),'3/8 time':(3,8),'4/4 time':(4,4),'5/4 time':(5,4),'5/8 time':(5,8),'6/4 time':(6,4),'6/8 time':(6,8),'7/8 time':(7,8),'9/8 time':(9,8),'12/8 time':(12,8),'4/4 time C':(4,4)}

    def __init__(self, x, y, template):
        self.beats, self.beat_type = self.timedict[template.name]
        self.x = x
        self.y = y
        self.w = template.w
        self.h = template.h
