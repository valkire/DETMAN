# Create your views here.
from sedge.DET.models import Detention, Meeting, Slot
from sedge.accounts.models import Teacher, Student, Contact
from sedge.DET.forms import MeetingForm
from django.contrib.auth.models import User,Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import Context, RequestContext, loader
from operator import itemgetter, attrgetter
from django.core.mail import send_mail
from django.db.models import Q
from django.db import connection, transaction
from datetime import date, datetime, timedelta
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
import ldap
import calendar
import sys
import os
import csv
import time
import re
import subprocess

### USER TESTS ####
def in_staff_group(user):
    if user:
        return user.groups.filter(name='amstaff').count() == True
    return False

def in_ss_group(user):
    if user:
        return user.groups.filter(name='amss').count() == True
    return False

def in_faculty_group(user):
    if user:
        return user.groups.filter(name='amfaculty').count() == True
    return False

def in_host_group(user):
    if user:
        return user.groups.filter(name='amhost').count() == True
    return False

###############
### HELPERS ###
###############
def check_state():
   detentions = Detention.objects.filter(deleted=False)
   meetings = Meeting.objects.filter(is_history=False)
   meeting_detentions = []
   for m in meetings:
       dlist = m.detentions.all()
       if not dlist:
           m.delete()
       else:
           for d in dlist:
               meeting_detentions.append(d)
   unmatched_d = [d for d in detentions if d not in meeting_detentions]
   for det in unmatched_d:
       det.issued = False
       det.save()

def select_calendar(month=None, year=None):
   now = datetime.now()
   day = now.day
   cal = calendar.HTMLCalendar()
   cal.setfirstweekday(6)
   month_table = cal.formatmonth(year, month)
   soup = BeautifulSoup(month_table)
   outfile = open("myHTML.html", 'w')

   for data in soup.findAll('td'):
      if data['class'] != "noday":
        days = data.findAll(text=True)
        for oneday in days:
          day = NavigableString(oneday)
          oneday.extract()
          addatag = Tag(soup, 'input')
          addatag['type']="submit"
          addatag['name']="meetingday"
          addatag['value']=day
          data.insert(0, addatag)

   outfile.write(soup.prettify())
   outfile.close()
   infile = open("myHTML.html", 'r')
   calfile = ""
   for line in infile:
      calfile =  calfile + line
   infile.close()

   return calfile

def valid_meeting(meeting):
  detentions = meeting.detentions.all()
  for d in detentions:
    if not d.deleted:
      return True
  return False
      
######################
##### Start views ####
######################
## MEETING SCHEDULE ##
######################

@login_required
def schedule_meeting(request):
   post_error = None
   if request.method == "POST":
      meetingday = request.POST['meetingday']
      meetingmonth = request.POST['meetingmonth']
      meetingyear = request.POST['meetingyear']
      meetingdate = date(int(meetingyear), int(meetingmonth), int(meetingday))
      slotid = request.POST['slot_id']
      slot = Slot.objects.get(pk=slotid)
      marked = Detention.objects.filter(marked=True)      
      dlist = []

      ## Remove old meeting detention associations if they exist
      live_meetings = Meeting.objects.filter(is_history=False)
      if live_meetings:
         for meeting in live_meetings:
            dlist = meeting.detentions.all() 
            matched_d = [d for d in marked if d in dlist]
            for det in matched_d:
               meeting.detentions.remove(det)
               meeting.save()
      
      ## Create a new meeting to hold the marked detentions
      ## Or consolidate with an existing meeting
      try: 
         m = Meeting.objects.get(timeslot=slot, meetingdate = meetingdate)
      except:
         m = Meeting(timeslot=slot, meetingdate=meetingdate, meetingday=slot.dayofweek, is_history=False)
         m.save()

      ## Add the marked detentions to the new meeting
      for detention in marked:
         m.detentions.add(detention) # add the detention
         detention.marked = False
         if m.timeslot.timeofday == 'FirstLunch' or m.timeslot.timeofday == 'SecondLunch':
             detention.mode = 'Lunch'
         elif m.timeslot.timeofday == 'AfterSchool':
             detention.mode = 'In-House'
         else:
             detention.mode = 'Weekend'
         detention.issued = True
         detention.issuestamp = datetime.now()
         detention.save()
      m.save()

   else:
      post_error = "No post data found"
   now = datetime.now()
   user = request.user
   if marked:
      request.user.message_set.create(message = "Meeting successfully scheduled" )
   else:
      request.user.message_set.create(message = "No detention records were selcted, Please try again")
      
   return HttpResponseRedirect(reverse('sedge.DET.views.records'))

#############
## RECORDS ##
#############
@login_required
@user_passes_test(in_ss_group, login_url='DET/denied/')
def records(request, sorter=None, nextmonth=None, nextyear=None):
   sortstate=['id_ascending', 'sname_descending', 'type_ascending']
   check_state()
   if sorter is not None:

      if sorter == 'idA':
         detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('id')
         sortstate =['id_ascending', 'sname_descending', 'type_descending']

      elif sorter == 'idD':
         detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('id').reverse()
         sortstate =['id_descending', 'sname_descending', 'type_descending']

      elif sorter == 'snameA':
         detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('student__last_name')
         sortstate =['id_descending', 'sname_ascending', 'type_descending']

      elif sorter == 'snameD':
         detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('student__last_name').reverse()
         sortstate =['id_descending', 'sname_descending', 'type_descending']

      elif sorter == 'typeA':
         detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('type')
         sortstate =['id_descending', 'sname_descending', 'type_ascending']

      elif sorter == 'typeD':
         detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('type').reverse()
         sortstate =['id_descending', 'sname_descending', 'type_descending']

      elif sorter == 'lunch':
         detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('student__firstlunch')
         sortstate =['id_descending', 'sname_descending', 'type_descending']

   else:
      detentions = Detention.objects.filter(deleted=False).exclude(type='Gum').order_by('id')

   gummy = Detention.objects.filter(deleted=False,type='Gum')

   ### Ensure we have no residual marked detentions
   marked = Detention.objects.filter(marked=True)
   if marked:
      for d in marked:
          d.marked = False
          d.save()

   now = datetime.now()
   textdate = now.strftime("%A, %B %d, %I:%M %p")
   thisday = now.day
   thismonth = now.month
   thisyear = now.year
   if nextmonth is not None:
      if nextmonth == "12":
            day = thisday
            month = 1
            year = eval(nextyear) + 1
      else:
        day = thisday
        month = eval(nextmonth) + 1
        year = eval(nextyear)
   else:
      day = thisday
      month = thismonth
      year = thisyear

   calfile = select_calendar(month, year)

   user = request.user
   return render_to_response('DET/records.html', {'textdate': textdate, 'sortstate': sortstate,
                             'request': request, 'detentions': detentions, 'calfile': calfile,
                             'now': now, 'day': day, 'month': month, 'year': year,},
                             context_instance = RequestContext(request))


######################
## SUBMIT DETENTION ##
######################
@login_required
def submit_detention(request):
   warn1 = ''
   d = None
   if request.method == 'POST':
      tid = request.POST['t_id']  
      sid = request.POST['s_id']
      if tid and sid:
         teacher = Teacher.objects.get(pk=tid)
         student = Student.objects.get(pk=sid)
         code = request.POST['CODEKEY']
         atcode = request.POST['ATCODEKEY']
         duration = request.POST['DURATION']
         summary = request.POST['description']
         sslist = []
         users = User.objects.all()
         sslist.append(teacher.email) 
         subject = "AMHS Notice regarding " + student.first_name + " " + student.last_name
         for u in users:
            if in_ss_group(u):
               sslist.append(u.email)
               

         if not atcode and not code:
            return render_to_response('DET/det_tryagain.html', {'teacher': teacher,
                                }, context_instance = RequestContext(request))

         if atcode and not code:
            if atcode == 'UA':
               ac = "UA"
               type = 'Unexcused'
               code = 'Attendance'
               student.save()
               d = Detention(student=student, teacher=teacher, atcode=atcode, code=code, type=type, duration=duration,
                          summary=summary, mode='Default')
               d.dtcount = student.atcount
               d.save()
               atcode = d.get_atcode_display()

            elif atcode == 'T1':
               ac = "T1"
               type = 'TardyFirst'
               code = 'Attendance'
               student.atcount = student.atcount + 1
               student.save()
               d = Detention(student=student, teacher=teacher, atcode=atcode, code=code, type=type, duration=duration,
                          summary=summary, mode='Default')
               d.dtcount = student.atcount
               d.save()
               atcode = d.get_atcode_display()
            else:
               type = 'Tardy'
               ac = "T"
               code = 'Attendance'
               d = Detention(student=student, teacher=teacher, atcode=atcode, code=code, type=type, duration=duration,
                       summary=summary, mode='Pending')
               d.save()
               atcode = d.get_atcode_display()


         if code != "Attendance":
            if code == 'Gum':
               ac = "Gum"
               type = 'Gum'
               d = Detention(student=student, teacher=teacher, code=code, type=type, duration=duration,
                       summary=summary, mode='Fine')
            else:
               type = 'Behavioral'
               ac = "B"
               d = Detention(student=student, teacher=teacher, code=code, type=type, duration=duration,
                       summary=summary, mode='Pending')
            d.save()
            code = d.get_code_display()

         contacts = Contact.objects.filter(student=d.student)
         for contact in contacts:
            sslist.append(contact.email) 
         
         user = request.user
         request.user.message_set.create(message = "Detention created successfully")

         ##### Uncomment the two lines below to activate sending of mail to contacts ########
         send_mail(subject , get_submit_message(teacher,student,d,ac), 'Student_Services@am-hs.org',
                                        sslist, fail_silently=False)

      else:
         warn1 = "You must select both a Teacher and a Student to submit a detention"

   now = datetime.now()
   user = request.user
   return render_to_response('DET/det_submitted.html', {'detention': d,
                             'student': student, 'teacher': teacher, 'now': now, 'warn1': warn1,
                             'code': code, 'summary': summary, 'type': type, 'sslist': sslist,
                             'atcode': atcode,}, context_instance = RequestContext(request))

############################
## MESSAGE at SUBMIT TIME ##
############################
def get_submit_message(teacher,student,detention,action_code):
   textdate = detention.substamp.strftime("%A, %B %d, %I:%M %p")
   tn = teacher.first_name + " " + teacher.last_name
   sn = student.first_name + " " + student.last_name
   by = "By: " + tn + "\n"
   regarding = "Regarding: " + sn + "\n"
   reason = "Reason: " + detention.code + "\n"
   hr = "========================================================\n"
   action_rule = "============== Present Action/Recommendations ================\n"
   linkset = """
For questions regarding attendance, please reference the AMHS Student Handbook (page 39).
A copy of the handbook is available from: http://am-hs.org/resources/student-handbook

The quick reference guide is available from: http://am-hs.org/student-life/attendance. 
"""
   notes = detention.summary

   if action_code == "Gum":
      intro = "The following gum fine action was filed on " + textdate + ":\n"
      action = "A Gum Fine will be issued"

   elif action_code == "UA":
      intro = "The following attendance record was filed on " + textdate + ":\n"
      action = "Unexcused Absence Reported"

   elif action_code == "T":
      intro = "The following attendance record was filed on " + textdate + ":\n"
      action = "A detention will be issued for Tardiness"

   elif action_code == "T1":
      if student.atcount > 9:
         intro = "The following attendance record was filed on " + textdate + ":\n"
         action = "This notice brings the current T1 Count (first period of the day) for " + sn + " to: " \
                   + str(student.atcount) + "\n A Parent/Teacher meeting will be arranged \n" 
      elif student.atcount > 3:
         intro = "The following attendance record was filed on " + textdate + ":\n"
         action = "This notice brings the current T1 Count (first period of the day) for " + sn + " to: " \
                   + str(student.atcount) + "\n A Detention will be issued for Tardiness \n\n" + linkset
      else:
         intro = "The following attendance record was filed on " + textdate + ":\n"
         action = "This notice brings the current T1 Count (first period of the day) for " + sn + " to: " \
                   + str(student.atcount) + "\n No Detention will be issued \n\n" + linkset
   else:
      intro = "The following disciplinary action was filed on " + textdate + ":\n"
      action = "A Behavioral Detention will be issued \n" 

   sm = intro + hr + "By: " + tn + "\nRegarding: " + sn + "\n\n" \
        + "Reason: " + detention.get_code_display() + "\n\n" + action_rule \
        + "\n" + action + "\n\n\n" + " Notes:\n" + hr + notes
   return sm

##############====================== Stemp ==============================
### =========================== Detention method =================================

def get_detention_message(teacher,student,detention,action_code):
   textdate = detention.substamp.strftime("%A, %B %d, %I:%M %p")
   tn = teacher.first_name + " " + teacher.last_name
   sn = student.first_name + " " + student.last_name
   by = "By: " + tn + "\n"
   regarding = "Regarding: " + sn + "\n"
   reason = "Reason: " + detention.code + "\n"
   hr = "========================================================\n"
   action_rule = "============== Present Action/Recommendations ================\n"
   notes = detention.summary

   intro = "The following disciplinary action was filed on " + textdate + ":\n"
   action = "A Behavioral Detention will be issued \n" 

   sm = intro + hr + "By: " + tn + "\nRegarding: " + sn + "\n\n" \
        + "Reason: " + detention.get_code_display() + "\n" + action_rule \
        + "\n" + action + "\n\n\n" + " Notes:\n" + hr + notes
   return sm

### =========================== Attendance method =================================

def get_attendance_message(teacher,student,detention,action_code):
   textdate = detention.substamp.strftime("%A, %B %d, %I:%M %p")
   tn = teacher.first_name + " " + teacher.last_name
   sn = student.first_name + " " + student.last_name
   by = "By: " + tn + "\n"
   regarding = "Regarding: " + sn + "\n"
   reason = "Reason: " + detention.code + "\n"
   hr = "========================================================\n"
   action_rule = "============== Present Action/Recommendations ================\n"
   notes = detention.summary
   postscript = """For questions regarding attendance, please reference the AMHS Student Handbook(page 39)

The handbook is available on-line from: http://am-hs.org/resources/student-handbook

"""

   if action_code == "Gum":
      intro = "The following gum fine action was filed on " + textdate + ":\n"
      action = "A Gum Fine will be issued"

   elif action_code == "UA":
      intro = "The following attendance record was filed on " + textdate + ":\n"
      action = "Unexcused Absence Reported"

   elif action_code == "T":
      intro = "The following attendance record was filed on " + textdate + ":\n"
      action = "A detention will be issued for Tardiness"

   elif action_code == "T1":
      if student.atcount > 11:
         intro = "The following attendance record was filed on " + textdate + ":\n"
         action = "This notice brings the current T1 Count(first period of the day) for " + sn + " to: " \
                   + str(student.atcount) + "\n A Parent/Teacher meeting will be arranged \n" 
      elif student.atcount > 2:
         intro = "The following attendance record was filed on " + textdate + ":\n"
         action = "This notice brings the current T1 Count(first period of the day) for " + sn + " to: " \
                   + str(student.atcount) + "\n A Detention will be issued for Tardiness \n" 
      else:
         intro = "The following attendance record was filed on " + textdate + ":\n"
         action = "This notice brings the current T1 Count(first period of the day) for " + sn + " to: " \
                   + str(student.atcount) + "\n No Detention will be issued \n" 

   sm = intro + hr + "By: " + tn + "\nRegarding: " + sn + "\n\n" \
        + "Reason: " + detention.get_code_display() + "\n\n" + action_rule \
        + "\n\n" + action + "\n\n\n" + " Notes:\n" + hr + notes + hr + postscript

   return sm

################==================== Etemp =======================

@login_required
def detention_form(request):
   metadata = request.META.items()
   metadata.sort()
   tlist = Teacher.objects.all().order_by('last_name')
   slist = Student.objects.all().order_by('last_name')
   codes = Detention.get_codes()
   atcodes = Detention.get_atcodes()
   duration = Detention.get_duration()
   alphalist = []
   for s in slist:
      entuple = {'id': s.id, 'first_name': s.first_name, 'last_name': s.last_name, 'alpha': s.last_name[:1].upper()}
      alphalist.append(entuple)
   now = datetime.now()
   user = request.user
   return render_to_response('DET/detention_form.html', {'user': user,
                             'request': request, 'now': now, 'codes': codes,
                             'tlist': tlist, 'slist': slist, 'alphalist': alphalist, 'atcodes': atcodes, 'duration': duration,},
                             context_instance = RequestContext(request))
   
def import_results(request):
   metadata = request.META.items()
   metadata.sort()
   return render_to_response('DET/import_results.html', {'metadata': metadata, 'request': request,})

def denied(request):
   metadata = request.META.items()
   metadata.sort()
   return render_to_response('DET/denied.html', {'metadata': metadata, 'request': request,})

def show_browser(request):
    metadata = request.META.items()
    if "HTTP_USER_AGENT" in request.META:
        return HttpResponse("You are using:  %s" % \
            request.META["HTTP_USER_AGENT"])
    else:
        return HttpResponse("You don't have a username cookie yet, you better get one")

#########################
## PDF DETENTION SLIPS ##
#########################
def get_issue_list(request):
   homedir = '/home/valkire/django/sedge/DET/'
   texdir = os.path.join(homedir, 'extra/latex/')
   project_dir = '/home/valkire/django/sedge'
   outfile = os.path.join(texdir, 'for_issue.tex')
   newsch = os.path.join(texdir, 'issuable.csv')
   pdffile = os.path.join(texdir, 'for_issue.pdf')
#   issuable = Detention.objects.filter(issued = True, served=False)
   texout = '-output-directory=' + texdir
   com = ", "

   meetings = Meeting.objects.filter(is_history=False)
   newsi = open(newsch, 'w')

   if request.method == 'POST':
      if request.POST.get('gum'):
         glist = Detention.objects.filter(type='Gum', deleted=False).order_by('student__last_name')
         for gummy in glist:
            mtextdate = "Monday - Friday"
            student = gummy.student.first_name + " " + gummy.student.last_name
            teacher = gummy.teacher.first_name + " " + gummy.teacher.last_name
            itextdate = gummy.substamp.strftime("%b/%d/%Y")
            id = str(gummy.id)
            newsi.write(student + com + "Chewing Gum in Class" + com + teacher +
                               com + mtextdate + com + "8 AM - 4 PM" + com + "Student Services" + com + id + com + itextdate + '\n')
         newsi.close()
         
      if request.POST.get('detention'):
         for m in meetings:
            mtextdate = m.meetingdate.strftime("%b/%d/%Y")
            dlist = m.detentions.all()
            host = m.timeslot.host
            tslot = m.timeslot.get_timeofday_display()
            room = str(host.room)
            for d in dlist:
               reason = ""
               student = d.student.first_name + " " + d.student.last_name
               teacher = d.teacher.first_name + " " + d.teacher.last_name
               itextdate = d.substamp.strftime("%b/%d/%Y")
               id = str(d.id)
               if d.atcode:
                  code = d.get_atcode_display()
               else:
                  code = d.get_code_display()
###         if d.issued == False: ## we may want to later test for previously issued 
               newsi.write(student + com + code + com + teacher +
                               com + mtextdate + com + str(tslot) + com + room + com + id + com + itextdate + '\n')
   
         newsi.close()


   subprocess.call([texdir + "issue.py"])
   subprocess.call(["latex", texout, outfile])
   subprocess.call(["pdflatex", texout, outfile])

   fullpath = os.path.join(texdir, pdffile)
   response = HttpResponse(file(fullpath).read())
   response['Content-Type'] = 'application/pdf'
   response['Content-Disposition'] = 'attachment; filename=IssueList.pdf'
   return response

def update_teacher_list(request):
   homedir = '/home/valkire/django/sedge/DET/'
   pydir = os.path.join(homedir, 'extra/python/')
   datdir = os.path.join(homedir, 'extra/python/dat/')
   rawfile = '/home/valkire/timport.csv'
   infile = os.path.join(pydir, 'timport.csv')
   postfile = os.path.join(pydir, 'current_teachers.csv')
   outfile = open(postfile,'w')
   com = ','
   nonteacher = '999'

### Add teachers to the remlist that you do not want in the drop-down teacher list
   remlist = ['Volunteer', 'Admin', 'Vanderpool', 'Serwold', 'Daviscourt',]
   impfields = ['staff_status', 'teacher_number', 'last_name', 'first_name', 'email', 'room', 'username']

   if os.path.isfile(rawfile):
      subprocess.call(["cp", rawfile, infile])

### rewrite the headers and then write out the data to a new list
   for field in impfields[0:-1]:
      outfile.write(field + com)
   outfile.write(impfields[6])
   outfile.write('\n')

   tlist = csv.reader(open(infile)) # the teacher import list
   for teacher in tlist:
      if eval(teacher[0]) == 1 and teacher[3] not in remlist:
         if teacher[6] != "":
            outfile.write(teacher[1] + com + teacher[2] + com + teacher[3] + com + teacher[4] +
                          com + teacher[5] + com + teacher[6] + com + teacher[7] + '\n')
         else:
            outfile.write(teacher[1] + com + teacher[2] + com + teacher[3] + com + teacher[4] +
                          com + teacher[5] + com + nonteacher + com + teacher[7] + '\n')
   outfile.close()

### Write the data to the database and create the Teacher objects and account if needed
   timplist = csv.DictReader(open(postfile)) # the processed teacher import list
   for teacher in timplist:
      try:
         t = Teacher.objects.get(username=teacher['username'])
      except:
         t = Teacher(first_name=teacher['first_name'], last_name=teacher['last_name'],
                      teacher_number=eval(teacher['teacher_number']), email=teacher['email'],
                      staff_status=eval(teacher['staff_status']), room=eval(teacher['room']), cell_phone='cell_phone',
                      is_host=False, username=teacher['username'],)
         t.save()
      try:
         tacct = User.objects.get(username=teacher['username'])
      except:
         sgroup = Group.objects.get(name='amstaff')
         tacct = User.objects.create_user(teacher["username"], teacher['email'], '!') 
         tacct.first_name = teacher['first_name']
         tacct.last_name = teacher['last_name']
         tacct.groups.add(sgroup)
         tacct.save()

#   subprocess.call(["mv", postfile, datdir])
#   subprocess.call(["mv", infile, datdir])
   return HttpResponseRedirect(reverse('sedge.DET.views.import_results',))

###############################
### Detention Record Actions###
###############################
@login_required
def record_action(request):
   if request.method == 'POST':
      now = datetime.now()
      user = request.user
      metadata = request.META.items()
      metadata.sort()
      det_id_list = request.POST.getlist('det_id')  
      records = []
      for id in det_id_list:
         d = Detention.objects.get(pk=id)
         records.append(d) 

      if request.POST.get('view'):
         return render_to_response('DET/list_view.html', {'metadata': metadata,
                             'records': records, 'now': now, 'user': user,},
                             context_instance = RequestContext(request))

      if request.POST.get('remove'):
         for record in records: 
            record.deleted = True
            record.save()
         return HttpResponseRedirect(reverse('sedge.DET.views.records',))

      if request.POST.get('meetingday'):
         meetings = Meeting.objects.filter(is_history=False)
         now = datetime.now()
         textdate = now.strftime("%A, %B %d %I:%M%p")

         ### Remove any residual marked detentions
         marked = Detention.objects.filter(marked=True)
         if marked:
            for d in marked:
                d.marked = False
                d.save()

         if request.method == "POST":
            meetingday = request.POST['meetingday']
            meetingmonth = request.POST['meetingmonth']
            meetingyear = request.POST['meetingyear']
         else:
            posterror = "No post data found"

         det_id_list = request.POST.getlist('det_id')  
         for id in det_id_list:
            d = Detention.objects.get(pk=id)
            d.marked = True
            d.save()

         marked = Detention.objects.filter(marked=True)
         meetingdate = date(int(meetingyear),int(meetingmonth),int(meetingday))
         mtextdate = meetingdate.strftime("%A,  %B %d %Y")

         requestday =  meetingdate.weekday()
         timeslots = Slot.objects.filter(dayofweek=requestday, hidden=False)
         return render_to_response("DET/meeting_validate.html", {'metadata': metadata, 'now': now, 'timeslots': timeslots,
                                                           'user': user, 'meetingdate': meetingdate, 'records': marked,
                                                           'textdate': textdate, 'mtextdate': mtextdate,},
                                                            context_instance = RequestContext(request))
#############
# HOST PAGE #   
#############
@login_required
def host(request):
   now = datetime.now()
   textdate = now.strftime("%A, %B %d %I:%M%p")
   user = request.user
   empty = []
   
   ## It is important (but not difficult) to maintain alignment with the teacher email and the teacher user email ##
   umail = request.user.email
   host = Teacher.objects.get(email=umail)

   ## Validate meetings
   vmeetings = Meeting.objects.filter(is_history=False)
   for meet in vmeetings:
     if not valid_meeting(meet):
       empty.append(meet.id)
       m = Meeting.objects.get(pk=meet.id)
       m.delete()
       transaction.commit()

   if user.is_staff:
     meetings = Meeting.objects.filter(is_history=False)
   elif in_faculty_group(user): 
     meetings = Meeting.objects.filter(timeslot__host=host, is_history=False)

   
   return render_to_response('DET/host.html', { 'meetings': meetings, 'now': now, 'user': user,
                             'host': host, 'textdate': textdate, 'empty': empty,}, context_instance = RequestContext(request))

def me_host(request, host_id):
   now = datetime.now()
   textdate = now.strftime("%A, %B %d %I:%M%p")
   user = request.user
   
   host = Teacher.objects.get(pk=host_id)

   if user.is_staff:
     meetings = Meeting.objects.filter(timeslot__host=host, is_history=False)

   return render_to_response('DET/me_host.html', { 'meetings': meetings, 'now': now, 'user': user,
                             'host': host, 'textdate': textdate,}, context_instance = RequestContext(request))


@login_required
def delete_meeting(request):
   if request.method == 'POST':
      del_list = request.POST.getlist('delete_meeting')  
      for id in del_list:
          m = Meeting.objects.get(pk=id)
          m.delete()
   now = datetime.now()
   textdate = now.strftime("%A, %B %d %I:%M%p")
   user = request.user
   umail = request.user.email
   host = Teacher.objects.get(email=umail)
   meetings = Meeting.objects.filter(is_history=False)
   return render_to_response('DET/host.html', { 'meetings': meetings, 'now': now, 'user': user,
                             'host': host, 'textdate': textdate,}, context_instance = RequestContext(request))

@login_required
def report_served(request):
   thisday = date.today()
   now = datetime.now()
   textdate = now.strftime("%A, %B %d %I:%M%p")
   user = request.user
   username = user.first_name
   anachronistic = False
   if request.method == 'POST':
      serve_list = request.POST.getlist('DETID')  
      allmeetinglist = request.POST.getlist('ALL')  
      nonemeetinglist = request.POST.getlist('NONE')  

      if nonemeetinglist:
         for id in nonemeetinglist:
            m = Meeting.objects.get(pk=id)
            mday = date(m.meetingdate.year, m.meetingdate.month, m.meetingdate.day)
            if thisday < mday:
              return render_to_response('DET/anachronism.html', {}, context_instance = RequestContext(request))
            m.is_history = True
            m.save()

      if allmeetinglist:
         for id in allmeetinglist:
            m = Meeting.objects.get(pk=id)
            mday = date(m.meetingdate.year, m.meetingdate.month, m.meetingdate.day)
            if thisday < mday:
              return render_to_response('DET/anachronism.html', {}, context_instance = RequestContext(request))
            detentions = m.detentions.all()
            for d in detentions:
               d.servestamp = now
               d.served = True
               d.deleted = True
               d.save()
            m.is_history = True
            m.save()
      
      for id in serve_list:
         d = Detention.objects.get(pk=id)
         meetings = d.meeting_set.all()
         for m in meetings:
            mday = date(m.meetingdate.year, m.meetingdate.month, m.meetingdate.day)
            if thisday < mday:
              return render_to_response('DET/anachronism.html', {}, context_instance = RequestContext(request))
            m.is_history = True
            m.save()
         d.served = True
         d.servestamp = now
         d.deleted = True
         d.save()
   request.user.message_set.create(message = "Thank You " + username + ", have a nice day")
   return HttpResponseRedirect(reverse('sedge.DET.views.host',))

def pwchangeinfo(request):
   return render_to_response('DET/pwchangeinfo.html', {}, context_instance = RequestContext(request))

def pwchangeform(request):
   return render_to_response('DET/pwchangeform.html', {}, context_instance = RequestContext(request))

def pwchange(request):
   error = ""
   if request.method == 'POST':
      username = request.user.username
      current_pw = request.POST['current_pw']
      new_pw_1 = request.POST['new_pw_1']
      new_pw_2 = request.POST['new_pw_2']

      if new_pw_1 == new_pw_2:
         try:
            dn = 'uid=' + username + ',' + 'ou=users,dc=am-hs,dc=org'
            usr = ldap.initialize('ldap://10.0.128.2')
            usr.simple_bind_s( dn, current_pw )
            usr.passwd_s( dn, current_pw, new_pw_2 )
         except:
            error =  "Password change failed, please try again"
      else:
         error = "Sorry, new passwords don't match"

   return render_to_response('DET/pwchangeinfo.html', {'error': error,}, context_instance = RequestContext(request))

@login_required
def detention_view(request, rid):
   detention = Detention.objects.get(pk=rid)
   student = Student.objects.get(pk=detention.student.id)
   other_d = Detention.objects.filter(student = student).exclude(id=rid).order_by('substamp')
   duration = Detention.get_duration()
   return render_to_response('DET/detention_view.html', {'rid': rid, 'detention': detention, 'duration': duration,
                                                        'other_d': other_d,}, context_instance = RequestContext(request))

@user_passes_test(in_ss_group, login_url='DET/denied/')
def gum_records(request, sorter=None, nextmonth=None, nextyear=None):
   sortstate=['id_ascending', 'sname_descending', 'type_ascending']
   check_state()
   if sorter is not None:

      if sorter == 'idA':
         detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('id')
         sortstate =['id_ascending', 'sname_descending', 'type_descending']

      elif sorter == 'idD':
         detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('id').reverse()
         sortstate =['id_descending', 'sname_descending', 'type_descending']

      elif sorter == 'snameA':
         detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('student__last_name')
         sortstate =['id_descending', 'sname_ascending', 'type_descending']

      elif sorter == 'snameD':
         detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('student__last_name').reverse()
         sortstate =['id_descending', 'sname_descending', 'type_descending']

      elif sorter == 'typeA':
         detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('type')
         sortstate =['id_descending', 'sname_descending', 'type_ascending']

      elif sorter == 'typeD':
         detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('type').reverse()
         sortstate =['id_descending', 'sname_descending', 'type_descending']

      elif sorter == 'lunch':
         detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('student__firstlunch')
         sortstate =['id_descending', 'sname_descending', 'type_descending']

   else:
      detentions = Detention.objects.filter(deleted=False,type='Gum').order_by('id')

   ### Remove any residual marked detentions
   marked = Detention.objects.filter(marked=True)
   if marked:
      for d in marked:
          d.marked = False
          d.save()

   now = datetime.now()
   textdate = now.strftime("%A, %B %d, %I:%M %p")
   thisday = now.day
   thismonth = now.month
   thisyear = now.year
   if nextmonth is not None:
      if nextmonth == "12":
            day = thisday
            month = 1
            year = eval(nextyear) + 1
      else:
        day = thisday
        month = eval(nextmonth) + 1
        year = eval(nextyear)
   else:
      day = thisday
      month = thismonth
      year = thisyear

   calfile = select_calendar(month, year)

   user = request.user
   return render_to_response('DET/gum_records.html', {'textdate': textdate, 'sortstate': sortstate,
                             'request': request, 'detentions': detentions, 'calfile': calfile,
                             'now': now, 'day': day, 'month': month, 'year': year,},
                             context_instance = RequestContext(request))


def change_duration(request, det_id):
   if request.method == 'POST':
      now = datetime.now()
      user = request.user
      d = Detention.objects.get(pk=det_id)
      
      if request.POST.get('DURATION'):
         new_duration = request.POST['DURATION']
         d.duration = new_duration
         d.save()
         return HttpResponseRedirect('/DET/records/') # Redirect after POST

      else:
         request.user.message_set.create(message = "Request cannot be blank")
         return HttpResponseRedirect('/DET/detention_view/{{ det_id }}/') # Redirect after POST

#def clearattn(request):
#   if request.method == 'POST':
#      now = datetime.now()
#      user = request.user
#      d = Detention.objects.all()
#   else:
#      return HttpResponseRedirect('/DET/clearattn/') # Redirect after POST
      
#      if request.POST.get('DURATION'):
#         new_duration = request.POST['DURATION']
#         d.duration = new_duration
#         d.save()
#         return HttpResponseRedirect('/DET/records/') # Redirect after POST
#
#      else:
#         request.user.message_set.create(message = "Request cannot be blank")
#         return HttpResponseRedirect('/DET/detention_view/{{ det_id }}/') # Redirect after POST

