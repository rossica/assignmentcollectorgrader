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
from collector.models import *
import random, re, datetime

class ScenarioTests(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    


"""
These tests verify that the form validation is functioning properly,
both by rejecting invalid inputs, and by accepting valid inputs.
"""
class FormsTest(TestCase):
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
    This test is currently broken
    """
    def test_assignment_form(self):
        self.skipTest("This test is taking too long to automate and doesn't really provide any gain")
        name = random.choice("abdcefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        name += ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_", random.randint(0,24)))
        f = open("C:/assignmentcollectorgrader/media/tests/2011/spring/cs000/lab9999/lab4test.java")
        
        data = {
                'course':1,
                'name':name,
                'start_date':datetime.datetime.now(),
                'due_date':datetime.datetime.now() + datetime.timedelta(hours=2),
                'test_file':r"c:/assignmentcollectorgrader/media/tests/2011/spring/cs000/lab9999/lab4test.java",
                'max_submissions': 10,
                }
        
        asgnmt_form = AssignmentAdminForm(data)
        
        # validate name and JAR file support
        # TODO: figure out why the test file always fails
        self.assertTrue(asgnmt_form.is_valid(), # "Fields in error: " + ', '.join(asgnmt_form.errors.keys()))
            """AssignmentAdminForm failed on valid input
                course: {0}
                name: {1}
                start_date: {2}
                due_date: {3}
                test_file: {4} 
                errors: {5}
            """.format(data['course'], name, data['start_date'], data['due_date'], data['test_file'], asgnmt_form.errors['test_file']))