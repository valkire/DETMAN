from django import forms
from django.forms import ModelForm, Textarea
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from models import Meeting, Teacher
from datetime import datetime, timedelta

class MeetingForm(forms.ModelForm):
#    timeslot = forms.ModelChoiceField(queryset=Slot.objects.filter(hidden=False))
#    is_history = forms.BooleanField(required=False)
    class Meta:
        model = Meeting
#        fields = ('timeslot', 'meetingday', 'meetingtime',)

#class DetentionForm(forms.ModelForm):
#    timeslot = forms.ModelChoiceField(queryset=Slot.objects.filter(hidden=False))
#    is_history = forms.BooleanField(required=False)
#    class Meta:
#        model = Meeting
#        fields = ('timeslot', 'meetingday', 'meetingtime',)



#class Detention(models.Model):
#   student = models.ForeignKey(Student)
#   teacher = models.ForeignKey(Teacher)
#   substamp = models.DateTimeField(default=datetime.now)
#   issuestamp = models.DateTimeField(null=True, blank=True)
#   servestamp = models.DateTimeField(null=True, blank=True)
#   mode = models.CharField(max_length=20, choices=MODES)
#   summary = models.TextField(editable=True, blank=True)
#   type = models.CharField(max_length=20, choices=TYPES)
#   code = models.CharField(max_length=200, choices=CODES)
#   issued = models.BooleanField('issued')
#   served = models.BooleanField('inactive (has served)')
#   deleted = models.BooleanField('inactive (Served)')
#   marked = models.BooleanField('Marked for Action')


