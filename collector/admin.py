from assignmentcollectorgrader.collector.models import Course, Assignment, Submission
from django.contrib import admin

class CourseAdmin(admin.ModelAdmin):
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
        })
    )
    list_display = ('__unicode__', 'course_num', 'term', 'year', )
    list_filter = ('year', 'term', 'course_num',)
#    list_display_links = ('__unicode__', 'course_num', 'term', 'year', )
    search_fields = ('^course_num', )


class AssignmentAdmin(admin.ModelAdmin):
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
        })
    )
    list_display = ('__unicode__', 'course', 'due_date', )
    list_filter = ('course', 'due_date')

class SubmissionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Submission Information', {
            'fields': ('first_name', 'last_name', 'submission_time', 'assignment', )
        }),
#        ('Assignment Passkey', {
#            'fields': ('passkey',)
#        }),
        ('Submitted File', {
            'fields':('file', 'grade_log')
        }), 
    )
    list_display = ('__unicode__', 'last_name', 'first_name', 'assignment', 'submission_time')
    list_filter = ('assignment', 'submission_time',)
    readonly_fields = ('assignment', 'submission_time',)

admin.site.register(Course, CourseAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)