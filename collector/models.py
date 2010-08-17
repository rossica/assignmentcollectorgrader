from django.db import models
from django.forms import ModelForm, Form


class Course(models.Model):
    course_num = models.CharField("Course Number", max_length=8, unique=True, help_text='For example: CS260.')
    course_title = models.CharField("Course Title", max_length=25, help_text='For example: Data Structures.')
    description = models.CharField(max_length=255, blank=True, verbose_name='Course Description')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access.')
    year = models.IntegerField(default=2010, help_text='The year this course is offered.')
    term = models.CharField(max_length=6, help_text='The term this course if offered. Valid values are: Fall, Winter, Spring, Summer.')
    
class Assignment(models.Model):
    def testfileurl(self, filename):
        import os.path
        extension = os.path.splitext(filename)
        return "tests/%s/%s%s/%s%s" % (self.course.course_num, self.course.term, self.course.year, self.name, extension[1])
    
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=25, help_text='No spaces allowed. Example: lab1-linkedlist.')
    instructions = models.CharField(max_length=255, blank=True)
    start_date = models.DateTimeField(blank=True, help_text='Date and time to begin allowing submission of assignments.')
    due_date = models.DateTimeField(blank=True, help_text='Date and time to stop allowing submission of assignments.')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access.')
    max_submissions = models.IntegerField(default=0, help_text='Maximum allowed submissions per student. 0 for unlimited.')
    test_file = models.FileField(upload_to=testfileurl, blank=True)
    
class Submission(models.Model):
    def fileurl(self, filename):
        import os.path
        extension = os.path.splitext(filename)
        return "submissions/%s/%s%s/%s_%s%s" % (self.assignment.course.course_num, self.assignment.course.term, self.assignment.course.year, self.last_name, self.first_name, extension[1])
    
    assignment = models.ForeignKey(Assignment)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    file = models.FileField(upload_to=fileurl)
    submission_time = models.DateTimeField(auto_now_add=True)
    
################
###   Forms  ###
################

class SubmissionForm(ModelForm):
    
    #def clean(self):
    #    pass
    
    class Meta:
        model = Submission
        #exclude = ('','')
