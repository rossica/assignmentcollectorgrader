from django.conf.urls.defaults import *
from assignmentcollectorgrader.collector.views import *

urlpatterns = patterns('',
    # Example:
    # (r'^AssignmentCollectorGrader/', include('AssignmentCollectorGrader.foo.urls')),
    
    (r'^$', course_index),
    (r'^(?P<course_id>[A-Za-z]{1,4}\d{3}[A-Za-z]?)/$', view_course), #
    (r'^(?P<course_id>[A-Za-z]{1,4}\d{3}[A-Za-z]?)/(?P<assn_name>[A-Za-z][A-Za-z0-9_\-]*)/$', view_assignment),
    (r'^(?P<course_id>[A-Za-z]{1,4}\d{3}[A-Za-z]?)/(?P<assn_name>[A-Za-z][A-Za-z0-9_\-]*)/submit/$', submit_assignment),
)