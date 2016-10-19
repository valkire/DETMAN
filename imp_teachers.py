#!/usr/bin/python


#############
## import file form from PS: 1,1,110,Clapp,John,jclapp@am-hs.org,206,
##   fields = [status, staff_status, teacher_number, last_name, first_name, email, room,]
#############
## Vince Alkire 2011
#############

import subprocess
import os
import sys
import csv

project_dir = '/home/valkire/django/sedge'
fromfile = '/home/valkire/timport.csv'
tofile = project_dir + '/data/imp/timport.csv'
outfile = open('current_teachers.csv','w')
com = ','
nonteacher = '999'

## Add teachers to the remlist that you do not want in the drop-down teacher list
remlist = ['Volunteer', 'Admin', 'Vanderpool', 'Serwold', 'Daviscourt',]
impfields = ['staff_status', 'teacher_number', 'last_name', 'first_name', 'email', 'room', 'username']


if os.path.isfile(fromfile):
   subprocess.call(["mv", fromfile, tofile])
#else:
#   print ""
#   print "I am sorry Vince, I couldn't find the PS com file; using last good known version"
#   print ""

timplist = csv.reader(open(project_dir + '/data/imp/timport.csv')) # the teacher import list

for field in impfields[0:-1]:
  outfile.write(field + com)
outfile.write(impfields[6])
outfile.write('\n')

for teacher in timplist:
   print teacher[7]
   if eval(teacher[0]) == 1 and teacher[3] not in remlist:
      if teacher[6] != "":
         outfile.write(teacher[1] + com + teacher[2] + com + teacher[3] + com + teacher[4] + 
                       com + teacher[5] + com + teacher[6] + teacher[7] + '\n')
      else:
         outfile.write(teacher[1] + com + teacher[2] + com + teacher[3] + com + teacher[4] + 
                       com + teacher[5] + com + nonteacher + teacher[7] + '\n')

outfile.close()
