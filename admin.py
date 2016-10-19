from models import Teacher, Detention, Meeting, Slot
from django.contrib import admin

class DetentionAdmin(admin.ModelAdmin):
    fields = ['student', 'teacher', 'code', 'type', 'mode', 'issued', 'summary', 'deleted']
    list_display = ('id', 'student', 'substamp', 'servestamp', 'code', 'mode', 'issued', 'deleted')
    search_fields = ['student__first_name', 'student__last_name']

class SlotAdmin(admin.ModelAdmin):
    ordering = ('host__last_name', 'host__first_name')
    pass

class MeetingAdmin(admin.ModelAdmin):
    pass
    list_display = ('timeslot','meetingdate', 'is_history',)
    search_fields = ['detentions__student__first_name', 'detentions__student__last_name',]

admin.site.register(Detention, DetentionAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Slot, SlotAdmin)
