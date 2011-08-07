#    Assignment Collector/Grader - a Django app for collecting and grading code
#    Copyright (C) 2010,2011  Anthony Rossi <anro@acm.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from assignmentcollectorgrader.collector.models import Course, CourseAdminForm, Assignment, AssignmentAdminForm, Submission
from django.contrib import admin
from django import forms



class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    fieldsets = (
        ('Course Information', {
            'fields': ('course_num', 'course_title',)
        }),
        ('Course Description', {
#            'classes': ('collapse',),
            'fields': ('description',)
        }),
        ('Course Passkey', {
            'fields': ('passkey',)
        }),
        ('Year and Term', {
            'fields':('year', 'term',)
        }),
    )
    list_display = ('__unicode__', 'course_num', 'term', 'year', )
    list_filter = ('year', 'term', 'course_num',)
#    list_display_links = ('__unicode__', 'course_num', 'term', 'year', )
    search_fields = ('^course_num', )



class AssignmentAdmin(admin.ModelAdmin):
    form = AssignmentAdminForm
    fieldsets = (
        ('Assignment Information', {
            'fields': ('course', 'name', 'start_date', 'due_date', )
        }),
        ('Submission Settings', {
            'fields': ('max_submissions', 'allow_late',)
        }),
        ('Assignment Instructions', {
#            'classes': ('collapse',),
            'fields': ('instructions',)
        }),
        ('Assignment Passkey', {
            'fields': ('passkey',)
        }),
        ('Test File', {
            'fields':('test_file', )
        }),
    )
    list_display = ('__unicode__', 'course', 'due_date', )
    list_filter = ('course', 'due_date')
    search_fields = ('name', )
    actions = ['display_grades']
    def display_grades(self, request, queryset):
        from django.shortcuts import render_to_response
        import datetime
        grades = []
        # Show grades for every assignment selected
        for assn in queryset:
            # Only add assignments that have started. No point showing assignments that can't even be turned in yet.
            if assn.start_date < datetime.datetime.now():
                warning = None
                # Get all names submitted to this assignment
                names = assn.submission_set.values_list('last_name', 'first_name').distinct()
                # Get the newest submission for each name and store it in a list
                submissions = []
                for name in names:
                    submissions.append(Submission.objects.filter(last_name=name[0], first_name=name[1], assignment=assn).latest('submission_time'))
                # Display a warning if grades are being retrieved before the due date. 
                if datetime.datetime.now() < assn.due_date:
                    warning = "These grades are preliminary. The assignment is not due yet."
                # Add the assignment, the latest unique submissions, and warnings (if any) to the output
                grades.append([assn, submissions, warning])
        return render_to_response('collector/grades.html', {'grades':grades,})
    display_grades.short_description = "Generate gradesheet"
    


class SubmissionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Submission Information', {
            'fields': ('first_name', 'last_name', 'submission_time', 'course', 'assignment', )
        }),
        ('Submitted File', {
            'fields':('file', 'grade_log',)
        }),
        ('Grade', {
            'fields':('grade',)
        }),
    )
    list_display = ('__unicode__', 'last_name', 'first_name', 'course', 'assignment', 'submission_time', 'grade')
    list_filter = ('course', 'assignment', 'submission_time', 'last_name',)
    readonly_fields = ('first_name', 'last_name', 'assignment', 'course', 'submission_time', 'grade',)
    actions = ['lowercase_names']
    def lowercase_names(self, request, queryset):
        for sub in queryset:
            sub.first_name = sub.first_name.lower()
            sub.last_name = sub.last_name.lower()
            sub.save()
            # Terrible, inefficient code. 
            # But queryset.update(first_name=first_name.lower(), last_name=last_name.lower()) doesn't seem to want to work.
            # Also, it will only be used once, so it's acceptable.
    lowercase_names.short_description = "Convert student names to Lowercase"

admin.site.register(Course, CourseAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)