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

from django.db import models
from django import forms
from settings import MEDIA_ROOT
from django.core.files.storage import Storage, FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver

import datetime, os, os.path, re, zipfile

# large changes, e.g. API changes, 
# database changes (that require syncdb and database export/import)
MAJOR_VERSION = 2 
# feature development, bug fixes are rolled into feature enhancements
# Security fixes do get their own version
MINOR_VERSION = 0 


##################
# Storage System #
##################
class AssignmentFileStorage(FileSystemStorage): # pragma: no cover
    def save(self, name, content):
        """
        Saves new content to the file specified by name. The content should be a
        proper File object, ready to be read from the beginning.
        """
        from django.utils.encoding import force_unicode
        # Get the proper name for the file, as it will actually be saved.
        if name is None:
            name = content.name
    
        if self.exists(name): # If the file already exists, delete the current one so we can save the new one
            self.delete(name)
            
        name = self._save(name, content)
    
        # Store filenames with forward slashes, even on Windows
        return force_unicode(name.replace('\\', '/'))

##################
###   Models   ###
##################

class Course(models.Model):
    def __unicode__(self):
        return "{0} {1} {2}".format(self.course_num, self.term, self.year)
    TERM_CHOICES = (
    ('fall', 'Fall'),
    ('winter', 'Winter'),
    ('spring', 'Spring'),
    ('summer', 'Summer'),
    )
    @models.permalink
    def get_absolute_url(self):
        return ('collector.views.view_course', (), {
                'year': self.year,
                'term':self.term,
                'course_id':self.course_num,})
    course_num = models.CharField("Course Number", max_length=8, help_text='For example: CS260.')
    course_title = models.CharField("Course Title", max_length=25, help_text='For example: Data Structures.')
    description = models.TextField(blank=True, verbose_name='Course Description')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access. Overridden by JavaAssignment passkeys.')
    year = models.IntegerField(default=datetime.datetime.now().year, help_text='The year this course is offered.')
    term = models.CharField(max_length=6, choices=TERM_CHOICES, help_text='The term this course is offered.')
    email = models.EmailField("Email to send grades to", blank=True)
    creator = models.ForeignKey(User, default=1, help_text="User who owns this Course and administrates it. (i.e. You!)") #  on_delete=models.SET_DEFAULT
    
    class Meta:
        unique_together=('course_num', 'year', 'term')
    
class GenericAssignment(models.Model):
    def testfileurl(self, filename):
        extension = os.path.splitext(filename)
        return "tests{0}{1}".format(self.get_absolute_url(), filename)
    
    def __unicode__(self):
        return self.name
    
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=25, help_text='No spaces allowed. Must start with a letter. Example: lab1-linkedlist.')
    instructions = models.TextField(blank=True)
    start_date = models.DateTimeField(help_text='Date and time to begin allowing submission of assignments.')
    due_date = models.DateTimeField(help_text='Date and time to stop allowing submission of assignments.')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access. Overrides any specified Course passkey.')
    max_submissions = models.IntegerField(default=0, help_text='Maximum allowed submissions per student. 0 for unlimited.')
    allow_late = models.BooleanField("Allow Late Submissions", default=False)
    creator = models.ForeignKey(User, default=1, help_text="User who owns this Assignment and administrates it. (i.e. You!)") #  on_delete=models.SET_DEFAULT
    
    class Meta:
        abstract = True
        unique_together = ('course', 'name')

class JavaAssignment(GenericAssignment):
    @models.permalink
    def get_absolute_url(self):
        return ('collector.views.view_assignment', (), {
                'year': self.course.year,
                'term': self.course.term,
                'course_id': self.course.course_num,
                'assn_name': self.name})
    OPTIONS_CHOICES = (
                       (0, 'None'),
                       (1, 'Automated Grading'),
                       (2, 'Plagiarism detection'),
                       (3, 'Both')
                       )
    test_file = models.FileField(upload_to=GenericAssignment.testfileurl, storage=AssignmentFileStorage(), blank=True)
    java_cmd = models.CharField("java runtime command line", help_text="Command line parameters to the java interpreter. Do not change this unless you know exactly what you are doing.", max_length=100, default="-Xms32m -Xmx32m junit.textui.TestRunner")
    javac_cmd = models.CharField("java compiler command line", help_text="Command line parameters to the java compiler. Do not change this unless you know exactly what you are doing.", max_length=100, default="-g")
    options = models.IntegerField("Optional Features", help_text="Optional processing to do after saving an uploaded submission.", default=1, choices=OPTIONS_CHOICES)
    watchdog_wait = models.IntegerField("Watchdog timer", help_text="Time to wait, in seconds, for test execution. Kills the test if it's still executing after this much time.", default=30)

class GenericSubmission(models.Model):
    def fileurl(self, filename):
        extension = os.path.splitext(filename)
        return "submissions{0}{1}_{2}_{3}{4}".format(self.assignment.get_absolute_url(), self.last_name, self.first_name, self.submission_number, extension[1])
    
    def __unicode__(self):
        return "{0} {1}: {2} #{3}".format(self.last_name, self.first_name, self.assignment.__unicode__(), self.submission_number)
    
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    email = models.EmailField("Email (optional)", blank=True)
    submission_time = models.DateTimeField(auto_now_add=True)
    submission_number = models.IntegerField(default=1)
    
    class Meta:
        abstract = True
        
class JavaSubmission(GenericSubmission):
    @models.permalink
    def get_absolute_url(self):
        return ('collector.views.view_submission', (), {
                'year': self.assignment.course.year,
                'term': self.assignment.course.term,
                'course_id': self.assignment.course.course_num,
                'assn_name': self.assignment.name,
                'sub_id': self.id})
    assignment = models.ForeignKey(JavaAssignment)
    file = models.FileField(upload_to=GenericSubmission.fileurl)
    
#################
###   Forms   ###
#################

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
    
    def clean_course_num(self):
        cn = self.cleaned_data['course_num']
        if not re.match(r'^[A-Z]{1,4}\d{3}[CDW]?$', cn.upper()):
            raise forms.ValidationError("Must begin with 1-4 letters, followed by 3 numbers, possibly followed by C,D or W.")
        return cn.upper()

class JavaAssignmentForm(forms.ModelForm):
    class Meta:
        model = JavaAssignment
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(r'^[a-zA-Z][\w\-]{,24}$', name):
            raise forms.ValidationError("Name must begin with a letter, and only contain letters, numbers, _ and -")
        return name
    
    def clean_test_file(self):
        tf = self.cleaned_data['test_file']
        if not tf:
            raise forms.ValidationError("This assignment must include a JUnit test script.")
        
        name, extension = os.path.splitext(tf.name)
        
        if not re.search(r'(\.jar$|\.java$)', extension.lower()):
            raise forms.ValidationError("Must be a Jar or a Java file")
        
        # Validate that uploaded JAR files are actually JAR files
        if '.jar' == extension.lower():
            
            if not zipfile.is_zipfile(tf):
                raise forms.ValidationError("Corrupted JAR file. Please remake JAR file.")
            
            try:
                z = zipfile.ZipFile(tf)
                z.testzip()
            except(zipfile.BadZipfile):
                raise forms.ValidationError("Corrupted JAR file. Please remake JAR file.")
        
        return tf

class JavaSubmissionForm(forms.ModelForm):
    
    def clean_first_name(self):
        fn = re.sub(r'[^a-z\-]', '', self.cleaned_data['first_name'].lower())
        if not re.match(r'\w+(\-\w+)?', fn):
            raise forms.ValidationError("Your name must begin with a letter, and can only contain letters and -")
        return fn
    
    def clean_last_name(self):
        ln = re.sub(r'[^a-z\-]', '', self.cleaned_data['last_name'].lower())
        if not re.match(r'\w+(\-\w+)?', ln):
            raise forms.ValidationError("Your name must begin with a letter, and can only contain letters and -")
        return ln
    
    def clean_file(self):
        f = self.cleaned_data['file']
        
        # Verify File extension
        name, extension = os.path.splitext(f.name)
        if not extension.lower() == '.jar':
            raise forms.ValidationError("Must have .jar extension")
        
        # Verify that the uploaded is a JAR based on magical numbers
        if not zipfile.is_zipfile(f):
            raise forms.ValidationError("Must be a JAR file.")
        
        try:
            z = zipfile.ZipFile(f)
            z.testzip()
        except zipfile.BadZipfile:
            raise forms.ValidationError("Must be a JAR file.")

        return f
    
    class Meta:
        model = JavaSubmission
        fields = ('first_name', 'last_name', 'email', 'file')
        
class JavaSubmissionFormP(JavaSubmissionForm):
    passkey = forms.CharField(max_length=25, required=True)
    
    def clean(self):
        # check to make sure we have an assignment and course object to test against
        if not self.instance:
            raise forms.ValidationError("No JavaSubmission instance supplied to this form. Tell a programmer.")
        elif not self.instance.assignment:
            raise forms.ValidationError("No JavaAssignment supplied to this form. Tell a programmer.")
        elif not self.instance.assignment.course:
            raise forms.ValidationError("No Course supplied to this form. Tell a programmer.")
        
        # If the passkey field is specified
        if 'passkey' in self.cleaned_data:      # pragma: no branch
            p = self.cleaned_data['passkey']
            # First test if the passkey is the assignment passkey
            if (p != self.instance.assignment.passkey):
                # Then test if the passkey is the course passkey
                if (p != self.instance.assignment.course.passkey):
                    # If neither course nor assignment passkey, display an error
                    self._errors["passkey"] = self.error_class(["The passkey is incorrect."])
        return self.cleaned_data
    
    class Meta(JavaSubmissionForm.Meta):
        fields = ('first_name', 'last_name', 'email', 'passkey', 'file')
        
        
###########################
###   Signal Handlers   ###
###########################

@receiver(pre_delete, sender=JavaSubmission)
def delete_submission_files(sender, **kwargs):
    try:
        if kwargs['instance'].file:
            kwargs['instance'].file.delete()

    except ObjectDoesNotExist as dne:                   # pragma: no cover
        print "DNE Error in delete_submission_files: ", dne
    except WindowsError as (winerror, strerror):        # pragma: no cover
        print "Windows Error in delete_submission_files: ", winerror, strerror
    except OSError as ose:                              # pragma: no cover
        print "OSError in delete_submission_files: ", ose
        
@receiver(pre_delete, sender=JavaAssignment)
def delete_assignment_file(sender, **kwargs):
    try:
        if kwargs['instance'].test_file:
            kwargs['instance'].test_file.delete()

    except ObjectDoesNotExist as dne:                   # pragma: no cover
        print "DNE Error in delete_assignment_file: ", dne
    except WindowsError as (winerror, strerror):        # pragma: no cover
        print "Windows Error in delete_assignment_file: ", winerror, strerror
    except OSError as ose:                              # pragma: no cover
        print "OSError in delete_assignment_file: ", ose
