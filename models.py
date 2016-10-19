from django.db import models
from sedge.accounts.models import Student, Teacher
from datetime import datetime, timedelta
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

ACTIONS = (
   ('remove', 'Remove'),
   ('view', 'View'),
   ('schedule', 'Schedule Detention'),
)

ATCODES = (
   ('T', 'Tardy'),
   ('T1', 'Tardy First Meeting'),
   ('UA', 'Unexcused Absence'),
)

CODES = (
   ('Gum', 'Gum Rule Violation'),
   ('B1', 'Dress Code Violation'),
   ('B2', 'Rude/Discourteous Behavior'),
   ('B3', 'Classroom Violation'),
   ('B4', 'Verbal Abuse/Harassment'),
   ('B5', 'Vulgar Language or Gestures'),
   ('B6', 'Facial Hair Infraction'),
   ('B7', 'Misuse of Digital Appliance'),
   ('B8', 'Littering'),
   ('B9', 'Fighting'),
#   ('B10', 'Other (Use text box for description)'),
)

MODES = (
   ('Lunch', 'Lunch'),
   ('Weekend', 'Weekend'),
   ('In-House', 'In-House'),
   ('Fine', 'Gum Fine'),
   ('Referral', 'Referral'),
   ('Pending', 'Pending'),
)

TYPES = (
   ('Behavioral', 'Behavioral Detention'),
   ('Attendance', 'Attendance Detention'),
   ('Tardy', 'Tardy'),
   ('TardyFirst', 'Tardy First Meeting'),
   ('Unexcused', 'Unexcused Absence'),
   ('Gum', 'Gum Fine'),
)

DAYS = (
   ('0', 'Monday'),
   ('1', 'Tuesday'),
   ('2', 'Wednesday'),
   ('3', 'Thursday'),
   ('4', 'Friday'),
   ('5', 'Saturday'),
   ('6', 'Sunday'),
)

DURATION = (
   ('30', '30 Minute Detention'),
   ('60', '60 Minute Detention'),
   ('R2D', 'Refer to Dean of Students'),
)


TIMES = (
   ('default', 'unassigned'),
   ('FirstLunch', 'First Lunch'),
   ('SecondLunch', 'Second Lunch'),
   ('AfterSchool', 'After School'),
   ('800', '8:00 AM'),
   ('830', '8:30 AM'),
   ('900', '9:00 AM'),
   ('930', '9:30 AM'),
   ('1000', '10:00 AM'),
   ('1030', '10:30 AM'),
   ('1100', '11:00 AM'),
   ('1130', '11:30 AM'),
   ('1200', '12:00 PM'),
   ('1230', '12:30 PM'),
   ('1300', '1:00 PM'),
   ('1330', '1:30 PM'),
   ('1400', '2:00 PM'),
   ('1430', '2:30 PM'),
   ('1500', '3:00 PM'),
   ('1530', '3:30 PM'),
   ('1600', '4:00 PM'),
   ('1630', '4:30 PM'),
   ('1700', '5:00 PM'),
)
   
class Detention(models.Model):
   student = models.ForeignKey(Student)
   teacher = models.ForeignKey(Teacher)
   substamp = models.DateTimeField(default=datetime.now)
   issuestamp = models.DateTimeField(null=True, blank=True)
   servestamp = models.DateTimeField(null=True, blank=True)
   mode = models.CharField(max_length=20, choices=MODES)
   summary = models.TextField(editable=True, blank=True)
   type = models.CharField(max_length=20, choices=TYPES)
   code = models.CharField(max_length=30, choices=CODES)
   atcode = models.CharField(max_length=30, choices=ATCODES)
   duration = models.CharField(max_length=4, choices=DURATION)
   issued = models.BooleanField('issued')
   served = models.BooleanField('inactive (has served)')
   deleted = models.BooleanField('inactive (deleted)')
   marked = models.BooleanField('Marked for Action')
   dtcount = models.IntegerField('DET Attendance Count', default=0)

   @staticmethod
   def get_codes():
      return CODES

   @staticmethod
   def get_atcodes():
      return ATCODES

   @staticmethod
   def get_duration():
      return DURATION

   def get_modes(self):
      return MODES

   def get_types(self):
      return TYPES

   def __unicode__(self):
      return self.student.last_name + " " + self.student.first_name

class Slot(models.Model):
   host = models.ForeignKey(Teacher)
   label = models.CharField(max_length=50)
   dayofweek = models.CharField(max_length=20, choices=DAYS)
   timeofday = models.CharField(max_length=20, choices=TIMES)
   hidden = models.BooleanField('hide from list')

   @staticmethod
   def get_times():
      times = []
      for t in TIMES:
         times.append(t[1])
      return times

   def __unicode__(self):
      return self.label + " In Room " + str(self.host.room) + " with " + str(self.host)

class Meeting(models.Model):
   timeslot = models.ForeignKey(Slot)
   detentions = models.ManyToManyField(Detention)
   meetingdate = models.DateTimeField(null=True, blank=True)
   meetingday = models.CharField(max_length=20, choices=DAYS)
   is_history = models.BooleanField('Submitted by Host')

   def __unicode__(self):
      return str(self.meetingdate.strftime("%A, %B %d") + ", " + str(self.timeslot.timeofday))
