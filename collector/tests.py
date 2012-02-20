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

from django.utils import unittest
from django.test import TestCase
from django.test.client import Client
from django import forms
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from collector.models import *
from assignmentcollectorgrader.settings import PROJECT_ROOT
import random, re, datetime

class ScenarioTests(TestCase):
    fixtures = ['collector.json']
    longMessage=True
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_view_course(self):
        course = Course.objects.get(pk=1)
        c = Client()
        response = c.get('/{0}/{1}/{2}'.format(course.year, course.term, course.course_num), follow=True)
        
        #verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Check the text of the page for course number
        self.assertRegexpMatches(response.content, '{0}'.format(course.course_num), "Course_num not found")
        
        #Check the text for the term and year of the course
        self.assertRegexpMatches(response.content, '{0}\s+{1}'.format(course.term.capitalize(), course.year))
        
        #Check to make sure all assignments are listed by name, at least
        for assn in course.assignment_set.all():
            self.assertRegexpMatches(response.content, '{0}'.format(assn.name))
            
    def test_view_assignment(self):
        assn = Assignment.objects.get(pk=1)
        cli = Client()
        response = cli.get('/{0}/{1}/{2}/{3}/'.format(assn.course.year, assn.course.term, assn.course.course_num, assn.name),  follow=True)
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #verify the Assignment name is listed somewhere
        self.assertRegexpMatches(response.content, "lab999-TestLab<br>")
        
        #Verify the form submit link is correct
        self.assertRegexpMatches(response.content, r'action="/{0}/{1}/{2}/{3}/submit/"'.format(assn.course.year, assn.course.term, assn.course.course_num, assn.name))
        
        #verify the parameters of the form are displayed: first name, last name, and file
        self.assertRegexpMatches(response.content, r'id="id_first_name" type="text" name="first_name"')
        self.assertRegexpMatches(response.content, r'id="id_last_name" type="text" name="last_name"')
        self.assertRegexpMatches(response.content, r'type="file" name="file" id="id_file"')
        


"""
Generate some random valid data to populate a CourseAdminForm.
Then attempt to validate it.
"""
class CourseFormTests(TestCase):
    longMessage = True
    def setUp(self):
        self.data = {}
        course_title = ""
        #generate a random valid course title
        for i in range(0, random.randint(1,24)):
            course_title += random.choice("abcdefghijklmnopqrstuvwxyz")
        self.data['course_title']= course_title
        self.data['year']= random.randint(0000,9999) # pick a random year
        self.data['term']= Course.TERM_CHOICES[random.randint(0,3)][0] # random term
        
    def tearDown(self):
        pass
    
    def test_valid_course_num(self):
        course_num = ""
        letters = random.randint(1,4)
        num_letters = 0
        
        # generate course letters
        while num_letters < letters:
            course_num += random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            num_letters +=1
        # generate course number
        for i in range(3):
            course_num += random.choice("0123456789")
        # decide whether to include a special letter at the end
        if random.randint(0,1):
            course_num += random.choice("CDW")
                               
        self.data['course_num'] = course_num
        
        c = CourseAdminForm(self.data)
        
        # Validate the data. this should pass
        self.assertTrue(c.is_valid(), 
            """CourseAdminForm failed on valid input: 
                course_num: {0} 
                course_title: {1} 
                year: {2} 
                term: {3} 
            """.format(course_num, self.data['course_title'], str(self.data['year']), self.data['term']))
            
    def test_invalid_course_num(self):
        # Now generate an invalid course number
        bad_course_num = ''.join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789CDW", random.randint(1,8)))
        
        while re.match(r'^[A-Z]{1,4}\d{3}[CDW]?$', bad_course_num):
            bad_course_num = ''.join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789CDW", random.randint(1,8)))
            
        self.data['course_num'] = bad_course_num
            
        c = CourseAdminForm(self.data)
        
        # Validate the data. This should fail
        self.assertFalse(c.is_valid(), 
            """CourseAdminForm succeeded on invalid input: 
                course_num: {0}
                course_title: {1} 
                year: {2} 
                term: {3} 
            """.format(bad_course_num, self.data['course_title'], str(self.data['year']), self.data['term']))

"""
These tests verify that the assignment form validation is functioning properly,
both by rejecting invalid inputs, and by accepting valid inputs.
"""
class AssignmentFormsTest(TestCase):
    fixtures = ['collector.json']
    longMessage=True
    def setUp(self): 
        name = random.choice("abdcefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        name += ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,24)))
        self.data = {
                'course':1,
                'name':name,
                'start_date':datetime.datetime.now(),
                'due_date':datetime.datetime.now() + datetime.timedelta(hours=2),
                'max_submissions': 10,
                }
    
    def tearDown(self):
        pass
    
    
    """
    Verify that we accept a valid form
    """
    def test_valid_form(self):
        f = open(PROJECT_ROOT+"/testdata/SimpleJUnitTest.java")
        file_data = {
                     'test_file': SimpleUploadedFile('SimpleJUnitTest.java', f.read())
                     }
        f.close()
        
        asgnmt_form = AssignmentAdminForm(self.data, file_data)
        
        # validate name and JAR file support
        self.assertTrue(asgnmt_form.is_valid(), # "Fields in error: " + ', '.join(asgnmt_form.errors.keys()))
            """AssignmentAdminForm failed on valid input
                course: {0}
                name: {1}
                start_date: {2}
                due_date: {3}
                test_file: {4} 
                errors: {5}
            """.format(self.data['course'], self.data['name'], self.data['start_date'], self.data['due_date'], file_data['test_file'], asgnmt_form.errors))
        
    """
    Verify that the form validation correctly detects a valid .jar file
    """
    def test_valid_jar(self):
        #Try again with a valid Jar file uploaded
        f = open(PROJECT_ROOT+"/testdata/SimpleJUnitTest.jar")
        file_data= {
                    'test_file': SimpleUploadedFile('SimpleJUnitTest.jar', f.read())
                    }
        f.close()
        
        asgnmt_form = AssignmentAdminForm(self.data, file_data)
        
        #Validate the valid Jar
        self.assertTrue(asgnmt_form.is_valid(), "Failed to accept valid Jar file")
    
    """
    Verify that invalid assignment names are rejected
    """
    def test_invalid_name(self):
        #Now generate a bad assignment name and see if we catch that
        name = ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,25)))
        while re.match(r'^[a-zA-Z][\w\-]{,24}$', name):
            name = ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,25)))
        self.data['name'] = name
        
        file_data = {
                     'test_file': SimpleUploadedFile('ValidJavaFile.java', "ffffff")
                     }
        
        asgnmt_form = AssignmentAdminForm(self.data, file_data)
        
        #Validate that we catch the bad name
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch bad name: {0}".format(name))
    
    """
    Verify that fake or corrupt .jar files are caught
    """
    def test_invalid_jar(self):
        # Generate a bad JAR file and see if we catch that
        f = open(PROJECT_ROOT+"/testdata/FakeJarFile.jar")
        file_data = {
                     'test_file': SimpleUploadedFile('FakeJarFile.jar', f.read())
                     }
        f.close()
        
        asgnmt_form = AssignmentAdminForm(self.data, file_data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch bad JAR: {0}".format(file_data['test_file']))
    
    """
    Verify that files without a .java or .jar extension are rejected.
    """
    def test_invalid_ext(self):
        #Now try a file that is neither Jar nor Java
        fake_ext = ''.join(random.sample("aBcDeFgHikLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,5)))
        file_data = {
                     'test_file': SimpleUploadedFile('NotAJarOrJavaFile.'+fake_ext, "ffffff")
                     }
        
        asgnmt_form = AssignmentAdminForm(self.data, file_data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch non-java/jar file: {0}".format(file_data['test_file']))
    
    """
    Verify that files without an extension are rejected.
    """
    def test_no_ext(self):
        #Test with no file extension
        file_data = {
                     'test_file': SimpleUploadedFile('NoFileExtension', "ffffff")
                     }
        
        asgnmt_form = AssignmentAdminForm(self.data, file_data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch no file extension")

"""
These tests validate the operation of submission forms.
"""
class SubmissionFormsTest(TestCase):
    fixtures = ['collector.json']
    longMessage = True
    def setUp(self):
        self.data = {
                     'first_name': ''.join(random.sample("abcdefghijklmnopqrstuvwxyz", random.randint(1,25))),
                     'last_name': ''.join(random.sample("abcdefghijklmnopqrstuvwxyz", random.randint(1,25)))
                     }
        f = open(PROJECT_ROOT+'/testdata/SimpleClass.jar')
        self.file_data= {
                         'file': SimpleUploadedFile('SimpleClass.jar', f.read())
                         }
        f.close()
        
    def tearDown(self):
        pass
    
    """
    Accept a valid form
    """
    def test_valid_jar(self):
        s = SubmissionForm(self.data, self.file_data)
        
        self.assertTrue(s.is_valid(),
            """Failed to validate a valid submission form.
                first name: {0}
                last name:  {1}
                file:       {2}
            """.format(self.data['first_name'], self.data['last_name'], self.file_data['file']))
    
    """
    Don't accept invalid jar files
    """
    def test_invalid_jar(self):
        file_data = {
                     'file': SimpleUploadedFile('FakeJar.jar', "ffffff")
                     }
        
        s = SubmissionForm(self.data, file_data)
        
        self.assertFalse(s.is_valid(), "Accepted an invalid jar.")
    
    """
    Don't accept jar files without an extension
    """
    def test_file_ext(self):
        f = open(PROJECT_ROOT+'/testdata/SimpleClass.jar')
        file_data= {
                    'file': SimpleUploadedFile('SimpleClass', f.read())
                    }
        f.close()
        
        s = SubmissionForm(self.data, file_data)
        
        self.assertFalse(s.is_valid(), "Accepted a valid jar without an extension.")
    
    """
    Reject empty name strings
    """
    def test_empty_name(self):
        self.data['first_name'] = ''
        self.data['last_name'] = ''
        
        s = SubmissionForm(self.data, self.file_data)
        
        self.assertFalse(s.is_valid(), "Failed to reject empty names")
        
    """
    Reject names that are entirely made up of symbols
    """
    def test_invalid_names(self):
        self.data['first_name'] = ''.join(random.sample(" `~!@#$%^&*()-_=+0123456789,.<>?|{}[]\\/\t", random.randint(1,25)))
        self.data['last_name'] = ''.join(random.sample(" `~!@#$%^&*()-_=+0123456789,.<>?|{}[]\\/\t", random.randint(1,25)))
        
        s = SubmissionForm(self.data, self.file_data)
        
        self.assertFalse(s.is_valid(), "Failed to reject invalid names")
        
    """
    Verify that names with symbols and letters are properly cleaned
    """
    def test_name_cleaning(self):
        self.data['first_name'] = ''.join(random.sample(" abcdefghijklmnopqrstuvwxyz`~!@#$56789", random.randint(1,25)))
        self.data['last_name'] = ''.join(random.sample(" abcdefghijklmnopqrstuvwxyz`~!@#$%56789", random.randint(1,25)))
        
        s = SubmissionForm(self.data, self.file_data)
        
        self.assertTrue(s.is_valid(), 
                        """Failed to clean symbols from name. 
                            first name: {0}
                            last name:  {1}
                        """.format(self.data['first_name'], self.data['last_name']))
        
        self.assertEqual(s.cleaned_data['first_name'], re.sub(r'[^a-z]', '',self.data['first_name']))
        self.assertEqual(s.cleaned_data['last_name'], re.sub(r'[^a-z]', '',self.data['last_name']))
    
    """
    Put the course password on the form and validate
    """
    def test_valid_course_password(self):
        a = Assignment.objects.get(pk=4) # get the assignment object with no password
        c = Course.objects.get(pk=2) # get the course object with a password
        s = Submission(assignment=a, course=c)
        
        self.data['passkey'] = c.passkey # set the password to the course password
        
        sfp = SubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate course password")
    
    """
    Put the assignment password on the form and validate
    """ 
    def test_valid_assn_password(self):
        a = Assignment.objects.get(pk=2) # get the assignment object with a password
        c = Course.objects.get(pk=1) # get the course object with no password
        s = Submission(assignment=a, course=c)
        
        self.data['passkey'] = a.passkey # set the password to the assignment password
        
        sfp = SubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate assignment password")
    
    """
    Put the assignment password on the form, see if validation still succeeds
    """
    def test_assn_course_password(self):
        a = Assignment.objects.get(pk=3) # get the assignment object with a password
        c = Course.objects.get(pk=2) # get the course object with a password
        s = Submission(assignment=a, course=c)
        
        self.data['passkey'] = a.passkey # set the password to the assignment password
        
        sfp = SubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate assignment password")
     
    """
    Put the course password on the form, see if validation still succeeds
    """   
    def test_course_assn_password(self):
        a = Assignment.objects.get(pk=3) # get the assignment object with a password
        c = Course.objects.get(pk=2) # get the course object with a password
        s = Submission(assignment=a, course=c)
        
        self.data['passkey'] = c.passkey # set the password to the assignment password
        
        sfp = SubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate course password")
        