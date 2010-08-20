from django.db import models
from django.forms import ModelForm, Form, ValidationError
from assignmentcollectorgrader.settings import MEDIA_ROOT


##################
###   Models   ###
##################
# TODO: Create Generic Assignment and Submssion objects, and sublcass them to make JAR-specific versions

class Course(models.Model):
    def __unicode__(self):
        return self.course_num
    course_num = models.CharField("Course Number", max_length=8, unique=True, help_text='For example: CS260.')
    course_title = models.CharField("Course Title", max_length=25, help_text='For example: Data Structures.')
    description = models.CharField(max_length=255, blank=True, verbose_name='Course Description')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access.')
    year = models.IntegerField(default=2010, help_text='The year this course is offered.')
    term = models.CharField(max_length=6, help_text='The term this course if offered. Valid values are: Fall, Winter, Spring, Summer.')
    
class Assignment(models.Model):
    # TODO: Rename to JARAssignment
    def testfileurl(self, filename):
        import os.path
        extension = os.path.splitext(filename)
        return "tests/%s/%s%s/%s%s" % (self.course.course_num, self.course.term, self.course.year, self.name, extension[1])
    
    def __unicode__(self):
        return self.course.__unicode__() + ": " + self.name
    
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=25, help_text='No spaces allowed. Example: lab1-linkedlist.')
    instructions = models.CharField(max_length=255, blank=True)
    start_date = models.DateTimeField(blank=True, help_text='Date and time to begin allowing submission of assignments.')
    due_date = models.DateTimeField(blank=True, help_text='Date and time to stop allowing submission of assignments.')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access.')
    max_submissions = models.IntegerField(default=0, help_text='Maximum allowed submissions per student. 0 for unlimited.')
    test_file = models.FileField(upload_to=testfileurl, blank=True)
    
class Submission(models.Model):
    # TODO: Rename to JARSubmission
    def fileurl(self, filename):
        import os.path
        extension = os.path.splitext(filename)
        return "submissions/%s/%s%s/%s_%s%s" % (self.assignment.course.course_num, self.assignment.course.term, self.assignment.course.year, self.last_name, self.first_name, extension[1])
    
    def __unicode__(self):
        return self.last_name + " " + self.first_name + ": " + self.assignment.__unicode__() + " " + str(self.id)
    
    assignment = models.ForeignKey(Assignment)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    file = models.FileField(upload_to=fileurl)
    submission_time = models.DateTimeField(auto_now_add=True)
    
#################
###   Forms   ###
#################

class SubmissionForm(ModelForm):
    # TODO: Create a JAR-specific JAR submission form, and a generic Submission form
    #def clean(self):
        # Verify max submissions ?
        # only possible once all other fields are available
        #path = MEDIA_ROOT + self.instance.fileurl('')
        #print self.instance.fileurl('') or 'no path to print'
        #pass
    
    def clean_file(self):
        import zipfile, os.path
        
        f = self.cleaned_data['file']
        
        # Verify that the uploaded is a JAR based on magical numbers
        try:
            z = zipfile.ZipFile(f)
            z.testzip()
        except(zipfile.BadZipfile):
            raise ValidationError("Must be a JAR file.")
        #print f.name or 'no name to print'
        #if not zipfile.is_zipfile(f.name):
        #z = zipfile.ZipFile(f)
        #print z.testzip()
        #if not z.testzip():
        #    raise ValidationError("Must be a JAR file.")
        
        # Verify File extension
        name, extension = os.path.splitext(f.name)
        if not extension == '.jar':
            raise ValidationError("Must be a JAR file.")

        return f
    
    class Meta:
        model = Submission
        exclude = ('assignment','submission_time')
