#    Assignment Collector/Grader - a Django app for collecting and grading code
#    Copyright (C) 2010,2011,2012  Anthony Rossi <anro@acm.org>
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

from collector.models import *
from grader.models import *
from django.contrib import admin
from django import forms


class JavaGradeAdmin(admin.ModelAdmin):
    fieldsets = (
                  ('Submission', {
                    'fields': ('submission', ),
                    }),
                  ('Error Information', {
                    'classes': ('collapse',),
                    'fields': ('error', 'error_text', 'junit_return',),
                    }),
                  ('Grade information', {
                    'fields': ('tests_passed', 'total_tests', 'tests_failed', 'test_errors', 'grade_log',),
                    }),
     )
    list_display = ('submission', 'tests_passed', 'total_tests', 'tests_failed', 'test_errors', 'error_text', 'junit_return')
    list_filter = ('submission__assignment', 'submission__assignment__course')
    readonly_fields = ('submission', 'error', 'error_text', 'total_tests', 'tests_passed', 'tests_failed', 'test_errors', 'junit_return', )#'grade_log')

admin.site.register(JavaGrade, JavaGradeAdmin)
