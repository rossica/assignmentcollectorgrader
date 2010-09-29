from django.db import models
from django import forms
from assignmentcollectorgrader.settings import MEDIA_ROOT


##################
###   Models   ###
##################
# TODO: Create Generic Assignment and Submission objects, and subclass them to make JAR-specific versions

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
        return ('view_course', (), {
                'year': self.year,
                'term':self.term,
                'course_id':self.course_num,})
    course_num = models.CharField("Course Number", max_length=8, help_text='For example: CS260.')
    course_title = models.CharField("Course Title", max_length=25, help_text='For example: Data Structures.')
    description = models.TextField(blank=True, verbose_name='Course Description')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access. Overridden by Assignment passkeys.')
    year = models.IntegerField(default=2010, help_text='The year this course is offered.')
    term = models.CharField(max_length=6, choices=TERM_CHOICES, help_text='The term this course is offered.')
    email = models.EmailField("Email to send grades to", blank=True)
    
class GenericAssignment(models.Model):
    def testfileurl(self, filename):
        import os.path
        extension = os.path.splitext(filename)
        return "tests/{0}/{1}/{2}/{3}/{4}".format(self.course.year, self.course.term, self.course.course_num, self.name, filename)
    
    def __unicode__(self):
        #return "{0}: {1}".format(self.course.__unicode__(), self.name)
        return self.name
    
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=25, help_text='No spaces allowed. Must start with a letter. Example: lab1-linkedlist.')
    instructions = models.TextField(blank=True)
    start_date = models.DateTimeField(help_text='Date and time to begin allowing submission of assignments.')
    due_date = models.DateTimeField(help_text='Date and time to stop allowing submission of assignments.')
    passkey = models.CharField(max_length=25, blank=True, verbose_name='Access passkey', help_text='A <i>secret</i> passkey to allow submission access. Overrides any specified Course passkey.')
    max_submissions = models.IntegerField(default=0, help_text='Maximum allowed submissions per student. 0 for unlimited.')
    allow_late = models.BooleanField("Allow Late Submissions", default=False)
    
    class Meta:
        abstract = True
        unique_together = ('course', 'name')

class Assignment(GenericAssignment):
    # TODO: Rename to JARAssignment
    @models.permalink
    def get_absolute_url(self):
        return ('view_assignment', (), {
                'year': self.course.year,
                'term':self.course.term,
                'course_id':self.course.course_num,
                'assn_name':self.name})
    test_file = models.FileField(upload_to=GenericAssignment.testfileurl, blank=True)

class GenericSubmission(models.Model):
    def fileurl(self, filename):
        import os.path
        extension = os.path.splitext(filename)
        return "submissions/{0}/{1}/{2}/{3}/{4}_{5}_{6}{7}".format(self.assignment.course.year, self.assignment.course.term, self.assignment.course.course_num, self.assignment.name, self.last_name, self.first_name, self.submission_number, extension[1])
    
    def __unicode__(self):
        return "{0} {1}: {2} #{3}".format(self.last_name, self.first_name, self.assignment.__unicode__(), self.submission_number)
    
    assignment = models.ForeignKey(Assignment)
    course = models.ForeignKey(Course)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    submission_time = models.DateTimeField(auto_now_add=True)
    submission_number = models.IntegerField(default=1)
    
    class Meta:
        abstract = True
        
class Submission(GenericSubmission):
    # TODO: Rename to JARSubmission
    @models.permalink
    def get_absolute_url(self):
        return ('collector.views.view_submission', [], {
                'year': self.assignment.course.year,
                'term':self.assignment.course.term,
                'course_id':self.assignment.course.course_num,
                'assn_name':self.assignment.name,
                'sub_id':self.id})
    file = models.FileField(upload_to=GenericSubmission.fileurl)
    grade_log = models.FileField(blank=True, upload_to=GenericSubmission.fileurl)
    grade = models.CharField(max_length=100, blank=True)
    
#################
###   Forms   ###
# TODO: Create Assignment form that validates the assignment name
#################

class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
    
    def clean_course_num(self):
        import re
        cn = self.cleaned_data['course_num']
        if not re.match(r'^[A-Z]{1,4}\d{3}[CDW]?$', cn.upper()):
            raise forms.ValidationError("Must begin with 1-4 letters, followed by 3 numbers, possibly followed by C,D or W.")
        return cn.upper()

class AssignmentAdminForm(forms.ModelForm):
    class Meta:
        model = Assignment
    
    def clean_name(self):
        import re
        name = self.cleaned_data['name']
        if not re.match(r'^[a-zA-Z][\w\-]{,24}$', name):
            raise forms.ValidationError("Name must begin with a letter, and only contain letters, numbers, _ and -")
        return name

class SubmissionForm(forms.ModelForm):
    # TODO: Create a JAR-specific JAR submission form, and a generic Submission form
    
    def clean_file(self):
        import zipfile, os.path
        
        f = self.cleaned_data['file']
        
        # Verify that the uploaded is a JAR based on magical numbers
        try:
            z = zipfile.ZipFile(f)
            z.testzip()
        except(zipfile.BadZipfile):
            raise forms.ValidationError("Must be a JAR file.")
        #print f.name or 'no name to print'
        #if not zipfile.is_zipfile(f.name):
        #z = zipfile.ZipFile(f)
        #print z.testzip()
        #if not z.testzip():
        #    raise ValidationError("Must be a JAR file.")
        
        # Verify File extension
        name, extension = os.path.splitext(f.name)
        if not extension == '.jar':
            raise forms.ValidationError("Must be a JAR file.")

        return f
    
    class Meta:
        model = Submission
        fields = ('first_name', 'last_name', 'file')
        
class SubmissionFormP(SubmissionForm):
    passkey = forms.CharField(max_length=25, required=True)
    
    def clean(self):
        # If the passkey field is specified
        if 'passkey' in self.cleaned_data:
            p = self.cleaned_data['passkey']
            # First test if the passkey is the assignment passkey
            if (p != self.instance.assignment.passkey):
                # Then test if the passkey is the course passkey
                if (p != self.instance.course.passkey):
                    # If niether course nor assignment passkey, display an error
                    self._errors["passkey"] = self.error_class(["The passkey is incorrect."])
        return self.cleaned_data
    
    class Meta(SubmissionForm.Meta):
        fields = ('first_name', 'last_name', 'passkey', 'file')
