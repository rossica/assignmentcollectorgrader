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

from collector.models import Course, CourseForm, JavaAssignment, JavaAssignmentForm, JavaSubmission
from grader.models import JavaGrade
from django.contrib import admin
from django import forms



class CourseAdmin(admin.ModelAdmin):
    form = CourseForm
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
        ('Owner', {
            'classes':('collapse',),
            'fields':('creator',)
        }),
    )
    list_display = ('__unicode__', 'course_num', 'term', 'year', )
    list_filter = ('year', 'term', 'course_num',)
#    list_display_links = ('__unicode__', 'course_num', 'term', 'year', )
    search_fields = ('^course_num', )
    
    def save_model(self, request, obj, form, change):
        # If creating this object (not UPDATEing it)
        if change == False:
            obj.creator = request.user # save the current user as creator
        obj.save()
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        # For all objects being saved
        for instance in instances:
            # If this object is being created
            if change == False:
                # set the creator as the current user
                instance.creator = request.user
            instance.save()
    
    def queryset(self, request):
        qs = super(CourseAdmin, self).queryset(request)
        # Allow superusers to see all Courses
        if request.user.is_superuser:
            return qs
        # otherwise, show only Courses created by current user
        return qs.filter(creator=request.user)


class AssignmentAdmin(admin.ModelAdmin):
    form = JavaAssignmentForm
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
        ('Advanced', {
            'classes': ('collapse',),
            'fields':('java_cmd', 'javac_cmd', 'options', 'watchdog_wait', 'creator')
        }),
#        ('Owner', {
#            'classes':('collapse',),
#            'fields':('creator',)
#        }),
    )
    list_display = ('__unicode__', 'course', 'due_date', )
    list_filter = ('course', 'due_date')
    search_fields = ('name', )
    actions = ['display_grades']
    
    def save_model(self, request, obj, form, change):
        # If creating this object (not UPDATEing it)
        if change == False:
            # save the current user as creator
            obj.creator = request.user
        obj.save()
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        # For all objects being saved
        for instance in instances:
            # If this object is being created
            if change == False:
                # set the creator as the current user
                instance.creator = request.user
            instance.save()
    
    def queryset(self, request):
        qs = super(AssignmentAdmin, self).queryset(request)
        # Allow superusers to see all Assignments
        if request.user.is_superuser:
            return qs
        # otherwise, show only Assignments created by current user
        return qs.filter(creator=request.user)
    
    def display_grades(self, request, queryset):
        from django.shortcuts import render_to_response
        import datetime
        grades = []
        # Show grades for every assignment selected
        for assn in queryset.order_by('course'):
            # Only add assignments that have started. No point showing assignments that can't even be turned in yet.
            if assn.start_date < datetime.datetime.now():
                warning = ""
                # Get all names submitted to this assignment
                names = assn.javasubmission_set.values_list('last_name', 'first_name').distinct()
                # Get the newest submission for each name and store it in a list
                submissions = []
                for name in names:
                    submissions.append(JavaSubmission.objects.filter(last_name=name[0], first_name=name[1], assignment=assn).order_by('-javagrade__tests_passed', '-submission_time')[0])
                # Display a warning if grades are being retrieved before the due date. 
                if datetime.datetime.now() < assn.due_date:
                    warning = "These grades are preliminary. The assignment is not due yet."
                # Display a warning if late assignments are allowed and it's after the due date
                if assn.allow_late and assn.due_date < datetime.datetime.now():
                    warning = "Submissions after the due date are allowed."
                # Add the assignment, the latest unique submissions, and warnings (if any) to the output
                grades.append([assn, submissions, warning])
        return render_to_response('grades.html', {'grades':grades,})
    display_grades.short_description = "Generate gradesheet"
    


class SubmissionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Submission Information', {
            'fields': ('first_name', 'last_name', 'submission_time', 'assignment', )
        }),
        ('Submitted File', {
            'fields':('file', )
        }),
#        ('Grade', {
#            'fields':('javagrade',)
#        }),
    )
    list_display = ('__unicode__', 'last_name', 'first_name', 'assignment', 'submission_time', 'javagrade')
    list_filter = ('assignment', 'assignment__course', 'submission_time', 'last_name',)
    readonly_fields = ('first_name', 'last_name', 'assignment', 'submission_time', 'javagrade')
    

admin.site.register(Course, CourseAdmin)
admin.site.register(JavaAssignment, AssignmentAdmin)
admin.site.register(JavaSubmission, SubmissionAdmin)