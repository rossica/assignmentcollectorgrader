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
These tests verify that the form validation is functioning properly,
both by rejecting invalid inputs, and by accepting valid inputs.
"""
class FormsTest(TestCase):
    longMessage=True
    def setUp(self):        
        data = {'course_num':"CS000",
                'course_title':"course_title",
                'year':2011,
                'term':Course.TERM_CHOICES[0][0] # Fall term
                }
        
        c = CourseAdminForm(data)
        c.save()
    
    def tearDown(self):
        pass
    
    """
    Generate some random valid data to populate a CourseAdminForm.
    Then attempt to validate it.
    """
    def test_course_form(self):
        course_num = ""
        letters = random.randint(1,4)
        num_letters = 0
        course_title = ""
        
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
            
        #generate a random course title
        for i in range(0,random.randint(1,24)):
            course_title += random.choice("abcdefghijklmnopqrstuvwxyz")
        
        data = {'course_num':course_num,
                'course_title':course_title,
                'year':random.randint(0000,9999), # pick a random year
                'term':Course.TERM_CHOICES[random.randint(0,3)][0] # random term
                }
        
        c = CourseAdminForm(data)
        
        # Validate the data. this should pass
        self.assertTrue(c.is_valid(), 
            """CourseAdminForm failed on valid input: 
                course_num: {0} 
                course_title: {1} 
                year: {2} 
                term: {3} 
            """.format(course_num, course_title, str(data['year']), data['term']))

        
        # Now generate an invalid course number
        bad_course_num = ''.join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789CDW", random.randint(1,8)))
        
        while re.match(r'^[A-Z]{1,4}\d{3}[CDW]?$', bad_course_num):
            bad_course_num = ''.join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789CDW", random.randint(1,8)))
            
        data['course_num'] = bad_course_num
            
        c = CourseAdminForm(data)
        
        # Validate the data. This should fail
        self.assertFalse(c.is_valid(), 
            """CourseAdminForm succeeded on invalid input: 
                course_num: {0}
                course_title: {1} 
                year: {2} 
                term: {3} 
            """.format(course_num, course_title, str(data['year']), data['term']))
    
    """
    Test the validation routines on AssignmentAdminForm
    """
    def test_assignment_form(self):
        name = random.choice("abdcefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        name += ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,24)))
        name_backup = name # save valid name for later
        f = open(PROJECT_ROOT+"/testdata/SimpleJUnitTest.java")
        
        file_data = {
                     'test_file': SimpleUploadedFile('SimpleJUnitTest.java', f.read())
                     }
        f.close()
        
        data = {
                'course':1,
                'name':name,
                'start_date':datetime.datetime.now(),
                'due_date':datetime.datetime.now() + datetime.timedelta(hours=2),
                'max_submissions': 10,
                }
        
        asgnmt_form = AssignmentAdminForm(data, file_data)
        
        # validate name and JAR file support
        self.assertTrue(asgnmt_form.is_valid(), # "Fields in error: " + ', '.join(asgnmt_form.errors.keys()))
            """AssignmentAdminForm failed on valid input
                course: {0}
                name: {1}
                start_date: {2}
                due_date: {3}
                test_file: {4} 
                errors: {5}
            """.format(data['course'], name, data['start_date'], data['due_date'], file_data['test_file'], asgnmt_form.errors))
        
        #Now generate a bad assignment name and see if we catch that
        while re.match(r'^[a-zA-Z][\w\-]{,24}$', name):
            name = ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,25)))
        data['name'] = name
        
        asgnmt_form = AssignmentAdminForm(data, file_data)
        
        #Validate that we catch the bad name
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch bad name: {0}".format(name))
        
        #Reset back to good name
        data['name'] = name_backup
        
        # Generate a bad JAR file and see if we catch that
        f = open(PROJECT_ROOT+"/testdata/FakeJarFile.jar")
        file_data['test_file'] = SimpleUploadedFile('FakeJarFile.jar', f.read())
        f.close()
        
        asgnmt_form = AssignmentAdminForm(data, file_data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch bad JAR: {0}".format(file_data['test_file']))
        
        #Now try a file that is neither Jar nor Java
        fake_ext = ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,5)))
        
        file_data['test_file'] = SimpleUploadedFile('NotAJarOrJavaFile.'+fake_ext, "ffffff")
        
        asgnmt_form = AssignmentAdminForm(data, file_data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch non-java/jar file: {0}".format(file_data['test_file']))
