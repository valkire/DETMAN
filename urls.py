from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
#    (r'^$', 'sedge.DET.views.index'),
    (r'^records/$', 'sedge.DET.views.records'),
    (r'^gum_records/$', 'sedge.DET.views.gum_records'),
#    (r'^clearattn/$', 'sedge.DET.views.clearattn'),
    url(r'^records/(?P<sorter>(idA|idD|snameA|snameD|typeA|typeD|lunch))/$', 'sedge.DET.views.records'),
    url(r'^gum_records/(?P<sorter>(idA|idD|snameA|snameD|typeA|typeD|lunch))/$', 'sedge.DET.views.gum_records'),
    (r'^records/(?P<nextmonth>\d+)/(?P<nextyear>\d+)/$', 'sedge.DET.views.records'),
    (r'^detention_view/(?P<rid>\d+)/$', 'sedge.DET.views.detention_view'),
    (r'^change_duration/(?P<det_id>\d+)/$', 'sedge.DET.views.change_duration'),
    (r'^submit_detention/$', 'sedge.DET.views.submit_detention'),
    (r'^report_served/$', 'sedge.DET.views.report_served'),
    (r'^detform/$', 'sedge.DET.views.detention_form'),
    (r'^host/$', 'sedge.DET.views.host'),
    (r'^me_host/(?P<host_id>\d+)/$', 'sedge.DET.views.me_host'),
#    (r'^pwchangeinfo/$', 'sedge.DET.views.pwchangeinfo'),
#    (r'^pwchangeform/$', 'sedge.DET.views.pwchangeform'),
#    (r'^pwchange/$', 'sedge.DET.views.pwchange'),
    (r'^schedule_meeting/', 'sedge.DET.views.schedule_meeting'),
    (r'^delete_meeting/', 'sedge.DET.views.delete_meeting'),
    (r'^record_action/', 'sedge.DET.views.record_action'),
    (r'^get_issue_list/', 'sedge.DET.views.get_issue_list'),
    (r'^show_browser/', 'sedge.DET.views.show_browser'),
    (r'^denied/', 'sedge.DET.views.denied'),
    (r'^logout/$', 'django.contrib.auth.views.logout'),
#    (r'^admin/(.*)', admin.site.root),
    url(r'^admin/', include(admin.site.urls)),
)
