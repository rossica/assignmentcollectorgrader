from django.conf.urls.defaults import *
from assignmentcollectorgrader.collector.views import course_index, specific_term_course_index, view_course, view_assignment, view_submission, submit_assignment

urlpatterns = patterns('',
    # Example:
    # (r'^AssignmentCollectorGrader/', include('AssignmentCollectorGrader.foo.urls')),
    
    (r'^$', course_index),
    (r'^(?P<year>\d{4})/(?P<term>(?i)(summer|spring|winter|fall))/$', specific_term_course_index),
    (r'^(?P<year>\d{4})/(?P<term>(?i)(summer|spring|winter|fall))/(?P<course_id>[A-Za-z]{1,4}\d{3}[A-Za-z]?)/$', view_course), #
    (r'^(?P<year>\d{4})/(?P<term>(?i)(summer|spring|winter|fall))/(?P<course_id>[A-Za-z]{1,4}\d{3}[A-Za-z]?)/(?P<assn_name>[A-Za-z][A-Za-z0-9_\-]*)/$', view_assignment),
    (r'^(?P<year>\d{4})/(?P<term>(?i)(summer|spring|winter|fall))/(?P<course_id>[A-Za-z]{1,4}\d{3}[A-Za-z]?)/(?P<assn_name>[A-Za-z][A-Za-z0-9_\-]*)/submissions/(?P<sub_id>\d+)/$', view_submission),
    (r'^(?P<year>\d{4})/(?P<term>(?i)(summer|spring|winter|fall))/(?P<course_id>[A-Za-z]{1,4}\d{3}[A-Za-z]?)/(?P<assn_name>[A-Za-z][A-Za-z0-9_\-]*)/submit/$', submit_assignment),
)