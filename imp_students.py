#!/usr/bin/env python
#############
##   fields = [number, last_name, first_name, classof, primary_email, secondary_email, firstlunch,]
#############
## process student data from the PS export file, outputs a reformatted file
## Vince Alkire 2011
#############

import subprocess
import os
import sys
import csv

homedir = '/home/valkire/django/sedge/DET/'
pydir = os.path.join(homedir, 'extra/python/')
datdir = os.path.join(homedir, 'extra/python/dat/')
rawfile = '/home/valkire/simport.csv'
infile = os.path.join(pydir, 'simport.csv')
postfile = os.path.join(pydir, 'current_students.csv')
outfile = open(postfile,'w')

com = ','
celldefault = '999.222.1111'

## Add students to the remlist that you do not want in the drop-down student list
remlist = ['Test Name',]
impfields = ['number', 'last_name', 'first_name', 'classof', 'primary_email', 'secondary_email', 'firstlunch',]


if os.path.isfile(rawfile):
   subprocess.call(["cp", rawfile, infile])

simplist = csv.reader(open(infile)) # the student import list

for field in impfields[0:-1]:
  outfile.write(field + com)
outfile.write(impfields[6])
outfile.write('\n')

for student in simplist:
   testname = student[2] + " " + student[1]
   if testname not in remlist:
      outfile.write(student[0] + com + student[1] + com + student[2] + com + student[3] + 
                                                com + student[4] + com + student[5] + com)
      if student[6] == '1':
         outfile.write('1' + '\n')
      else:
         outfile.write('0' + '\n')

outfile.close()
