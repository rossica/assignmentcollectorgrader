#    Assignment Collector/Grader - a Django app for collecting and grading code
#    Copyright (C) 2010,2011  Anthony Rossi <anro@acm.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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