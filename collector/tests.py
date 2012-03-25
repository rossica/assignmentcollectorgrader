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
from settings import PROJECT_ROOT
import random, re, datetime, shutil, os

class ScenarioTests(TestCase):
    fixtures = ['collector.json', 'users.json']
    longMessage=True
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    """
    """
    def test_view_about(self):
        cli = Client()
        
        response = cli.get('/about/')
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200, "Non-success HTTP status")
        
        self.assertRegexpMatches(response.content, r'Version.*?{0}\.{1}'.format(MAJOR_VERSION, MINOR_VERSION))
    
    
    """
    """
    def test_view_course_index(self):
        courses = Course.objects.all()
        cli = Client()
        
        response = cli.get('/')
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200, "Non-success HTTP status")
        
        #Check the text of the page for course numbers
        #Make sure URLs exist for each course
        for c in courses:
            self.assertRegexpMatches(response.content, '{0}\s+{1}'.format(c.course_num, c.course_title), "Course_num not found")
            self.assertRegexpMatches(response.content, r'href=\"{0}\"'.format(c.get_absolute_url()), "Incorrect absolute URL returned by Course " + str(c))

    """
    """
    def test_view_specific_term_course_index(self):
        cli = Client()
        course = Course.objects.get(pk=1)
        
        response = cli.get('/{0}/{1}'.format(course.year, course.term), follow=True)
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200, "Non-success HTTP status")
        
        #Verify the course object is listed in this page
        self.assertRegexpMatches(response.content, '{0}\s+{1}'.format(course.course_num, course.course_title), "Course_num not found")
        self.assertRegexpMatches(response.content, r'href=\"{0}\"'.format(course.get_absolute_url()), "Incorrect absolute URL returned by Course " + str(course))

    """
    """
    def test_view_course(self):
        course = Course.objects.get(pk=1)
        c = Client()
        response = c.get(course.get_absolute_url(), follow=True)
        
        #verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Check the text of the page for course number
        self.assertRegexpMatches(response.content, '{0}'.format(course.course_num), "Course_num not found")
        
        #Check the text for the term and year of the course
        self.assertRegexpMatches(response.content, '{0}\s+{1}'.format(course.term.capitalize(), course.year))
        
        #Check to make sure all assignments are listed by name, at least
        for assn in course.javaassignment_set.all():
            self.assertRegexpMatches(response.content, '{0}'.format(assn.name))
    """
    """    
    def test_view_assignment(self):
        assn = JavaAssignment.objects.get(pk=1)
        cli = Client()
        response = cli.get(assn.get_absolute_url(),  follow=True)
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #verify the Assignment name is listed somewhere
        self.assertRegexpMatches(response.content, "{0}<br>".format(assn.name))
        
        #Verify the form submit link is correct
        self.assertRegexpMatches(response.content, r'action="{0}submit/"'.format(assn.get_absolute_url()))
        
        #verify the parameters of the form are displayed: first name, last name, and file
        self.assertRegexpMatches(response.content, r'id="id_first_name" type="text" name="first_name"')
        self.assertRegexpMatches(response.content, r'id="id_last_name" type="text" name="last_name"')
        self.assertRegexpMatches(response.content, r'type="file" name="file" id="id_file"')
    
    """
    """
    def test_view_assignment_early(self):
        assn = JavaAssignment.objects.get(pk=8)
        cli = Client()
        response = cli.get(assn.get_absolute_url(),  follow=True)
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #verify the Assignment name is listed somewhere
        self.assertRegexpMatches(response.content, "{0}<br>".format(assn.name))
        
        self.assertRegexpMatches(response.content, r'(?s)(?!<form.+?>.+?</form>)', "Found a submission form when there shouldn't be one")
    
    """
    """
    def test_view_assignment_late(self):
        assn = JavaAssignment.objects.get(pk=6)
        cli = Client()
        response = cli.get(assn.get_absolute_url(),  follow=True)
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #verify the Assignment name is listed somewhere
        self.assertRegexpMatches(response.content, "{0}<br>".format(assn.name))
        
        self.assertRegexpMatches(response.content, r'(?s)(?!<form.+?>.+?</form>)', "Found a submission form when there shouldn't be one")

    """
    """
    def test_view_assignment_password(self):
        assn = JavaAssignment.objects.get(pk=2)
        cli = Client()
        response = cli.get(assn.get_absolute_url(),  follow=True)
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify a form is shown
        self.assertRegexpMatches(response.content, r'(?s)<form.+?>.+?</form>', "Didn't find a submission form when there should be one")
        
        #Verify the parameters of the form are displayed: first name, last name, file, and passkey
        self.assertRegexpMatches(response.content, r'id="id_first_name" type="text" name="first_name"')
        self.assertRegexpMatches(response.content, r'id="id_last_name" type="text" name="last_name"')
        self.assertRegexpMatches(response.content, r'type="file" name="file" id="id_file"')
        self.assertRegexpMatches(response.content, r'id="id_passkey" type="text" name="passkey"')

    """
    """
    def test_view_assignment_course_password(self):
        assn = JavaAssignment.objects.get(pk=4)
        cli = Client()
        response = cli.get(assn.get_absolute_url(),  follow=True)
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify a form is shown
        self.assertRegexpMatches(response.content, r'(?s)<form.+?>.+?</form>', "Didn't find a submission form when there should be one")
        
        #Verify the parameters of the form are displayed: first name, last name, file, and passkey
        self.assertRegexpMatches(response.content, r'id="id_first_name" type="text" name="first_name"')
        self.assertRegexpMatches(response.content, r'id="id_last_name" type="text" name="last_name"')
        self.assertRegexpMatches(response.content, r'type="file" name="file" id="id_file"')
        self.assertRegexpMatches(response.content, r'id="id_passkey" type="text" name="passkey"')

    """
    """
    def test_view_submission(self):
        s = JavaSubmission.objects.get(pk=1)
        cli = Client()
        response = cli.get(s.get_absolute_url())
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify the link back to this page is available
        self.assertRegexpMatches(response.content, r'href={0}'.format(s.get_absolute_url()))
        
        #Verify the grade is displayed
        self.assertRegexpMatches(response.content, r'(?m)Grade:\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests))
        
        #Verify the name is displayed
        self.assertRegexpMatches(response.content, r'Submitted by {0} {1}'.format(s.first_name, s.last_name))

    """
    """
    def test_view_submission_no_grade_log(self):
        s = JavaSubmission.objects.get(pk=2)
        assn = s.assignment
        cli = Client()
        response = cli.get(s.get_absolute_url())
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify the link back to this page is available
        self.assertRegexpMatches(response.content, r'href={0}'.format(s.get_absolute_url()))
        
        #Verify the grade is displayed
        self.assertRegexpMatches(response.content, r'(?m)Grade:\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests))
        
        #Verify the name is displayed
        self.assertRegexpMatches(response.content, r'Submitted by {0} {1}'.format(s.first_name, s.last_name))
        
        #Verify the gradelog is not displayed and a message telling the user is
        self.assertRegexpMatches(response.content, r'No grade results to display.',)

    """
    """
    def test_view_submission_large_grade_log(self):
        cli = Client()
        s = JavaSubmission.objects.get(pk=3)
        
        response = cli.get(s.get_absolute_url())
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify the link back to this page is available
        self.assertRegexpMatches(response.content, r'href={0}'.format(s.get_absolute_url()))
        
        #Verify the grade is displayed
        self.assertRegexpMatches(response.content, r'(?m)Grade:\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests))
        
        #Verify the name is displayed
        self.assertRegexpMatches(response.content, r'Submitted by {0} {1}'.format(s.first_name, s.last_name))
        
        #Verify the gradelog is truncated and a message telling the user is displayed
        self.assertRegexpMatches(response.content, r'Grade results too long, truncating',)

    """
    """
    def test_submit_assignment_late_not_allowed(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=6)
        self.f = open(PROJECT_ROOT+'/testdata/EmptyJar.jar', 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify the submission is rejected
        self.assertRegexpMatches(response.content, r'It is past the due date and late assignments are not accepted. Sorry. :\(', "Submission was not rejected")
    
    """
    """
    def test_submit_assignment_late_allowed(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=9)
        self.f = open(PROJECT_ROOT+'/testdata/SimpleClass.jar', 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify that we inform the user they are turning in late.
        self.assertRegexpMatches(response.content, r'You are turning in this assignment past the due date. But it will be accepted anyway. :\)')
        
        #Delete the submission created for this test
        JavaSubmission.objects.filter(assignment__pk=a.id).delete()
    
    """
    """
    def test_submit_assignment_max_submissions_reached(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=5)
        
        self.f = open(PROJECT_ROOT+'/testdata/EmptyJar.jar', 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify we inform the user they have reached maximum number of submissions
        self.assertRegexpMatches(response.content, r'I&#39;m sorry, but you&#39;ve reached the maximum number of attempts.')
    
    """
    """
    def test_submit_assignment_GET(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        
        response = cli.get("{0}submit/".format(a.get_absolute_url()), follow=True)
        
        #Verify the client redirected in the past
        self.assertRedirects(response, a.get_absolute_url())
        
        #verify the Assignment name is listed somewhere
        self.assertRegexpMatches(response.content, "{0}<br>".format(a.name))
        
        #Verify the form submit link is correct
        self.assertRegexpMatches(response.content, r'action="{0}submit/"'.format(a.get_absolute_url()))

    """
    """
    def test_submit_assignment_early(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=8)
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':"asdfasdfasdfasdf"
                  })
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Inform the user that submission is not available for this assignment yet
        self.assertRegexpMatches(response.content, r'Submission has not opened for this assignment. Please wait until the assignment is available to submit your code')
    
    """
    """
    def test_submit_assignment_invalid_form(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':"asdfasdfasdfasdf"
                  })
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify that form errors are returned to the user
        self.assertRegexpMatches(response.content, r'<ul class="errorlist"><li>This field is required.</li></ul>', "Did not produce error")
    
    """
    """
    def test_submit_assignment_no_test_file(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=10)
        
        f = open(PROJECT_ROOT+'/testdata/EmptyJar.jar', 'rb')
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':f
                  })
        f.close()
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Not really certain how to test this.
        
        #Clean up after the test
        JavaSubmission.objects.get(assignment__pk=a.id).delete()
    
    """
    """
    def test_submit_assignment_password(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=2)
        
        f = open(PROJECT_ROOT+'/testdata/SimpleClass.jar', 'rb')
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'passkey':a.passkey,
                  'file':f
                  })
        f.close()
        
        #Verify the response is a success
        self.assertEqual(response.status_code, 200)
        
        #Verify that we don't have an error for bad password
        self.assertRegexpMatches(response.content, r'(?!The passkey is incorrect)')
        
        #Clean up after the test
        JavaSubmission.objects.get(assignment__pk=a.id).delete()
    
        
"""
These tests verify that the various states the grader can be in are covered and handled.
When the grader is moved to its own app, these tests will still remain here, but will
also serve as basis for the tests written for the grader.
"""
class GraderTests(TestCase):
    fixtures = ['collector.json', 'users.json']
    longMessage = True
    unable_to_parse_regex = re.compile(r'Grade[^A-Z]+Unable to parse grade\.')
    def setUp(self):
        pass
    def tearDown(self):
        #self.f.close() # always close files, regardless of success or failure
        #shutil.rmtree(,ignore_errors=True)
        JavaSubmission.objects.filter(pk__gt=3).delete() # delete the files from the disk too

    """
    Catch the case where there are no files to compile
    """
    def test_compile_failure_no_src(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        self.f = open(PROJECT_ROOT+'/testdata/EmptyJar.jar', 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        # verify the correct error message
        self.assertRegexpMatches(response.content, r'Grade\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't find grade")
        self.assertRegexpMatches(response.content, r'Reason\D+?\d+ compiler errors', "Didn't find reason for failure")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")

    """
    Test the case where there is a syntax error in the student-uploaded file
    """
    def test_compile_failure_syntax_error(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        self.f = open(PROJECT_ROOT + "/testdata/SyntaxError.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        # verify the correct error message
        self.assertRegexpMatches(response.content, r'Grade\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't find grade")
        self.assertRegexpMatches(response.content, r'Reason\D+?\d+ compiler errors', "Didn't find reason for failure")        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")

    """
    Test compilation still fails because we are deleting .class files and there are no source files
    """
    def test_compile_failure_only_class_files(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        self.f = open(PROJECT_ROOT + "/testdata/ClassFileOnly.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        # verify the correct error message
        self.assertRegexpMatches(response.content, r'Grade\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't find grade")
        self.assertRegexpMatches(response.content, r'Reason\D+?\d+ compiler errors', "Didn't find reason for failure")        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")

    """
    Test that the watchdog timer kicks in after 30 seconds
    """
    def test_watchdog_timer(self):
        #self.skipTest("Long test, need to move to its own queue")
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        self.f = open(PROJECT_ROOT + "/testdata/WatchdogTimer.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        # verify the correct error message
        self.assertRegexpMatches(response.content, r'Grade\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't hit watchdog timer")
        self.assertRegexpMatches(response.content, r'Reason[^A-Z]+?Watchdog timer killed the test after \d+ seconds', "Didn't hit watchdog timer")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")

    """
    Test that we handle code exceptions gracefully
    """
    @unittest.expectedFailure
    def test_junit_exception(self):
        #self.skipTest("Need to figure out how to throw this specific error.")
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        self.f = open(PROJECT_ROOT + "/testdata/Exception.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        # verify the correct error message
        self.assertRegexpMatches(response.content, r'Grade\D+?{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't produce exception errors")
        self.assertRegexpMatches(response.content, r'Reason[^A-Z]+?Exception in thread \"main\"', "Didn't hit exception")

    """
    Test picking up more than one test case failure
    """
    def test_junit_failures(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=7)
        self.f = open(PROJECT_ROOT + "/testdata/ThreeTestFailures.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the failures occurred
        self.assertRegexpMatches(response.content, r'Failures:\s+2', "Didn't produce multiple failures")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")

    """
    Test picking up a single test case failure
    """
    def test_junit_failure(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=7)
        self.f = open(PROJECT_ROOT + "/testdata/ThreeTestFailure.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'Failures:\s+1', "Didn't produce a single failure")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")

    """
    Test multiple test case errors
    """
    def test_junit_errors(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=7)
        self.f = open(PROJECT_ROOT + "/testdata/ThreeTestErrors.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'Errors:\s+2', "Didn't produce multiple errors")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")

    """
    Test a single test case error out of three tests
    """
    def test_junit_error(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=7)
        self.f = open(PROJECT_ROOT + "/testdata/ThreeTestError.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'Errors:\s+1', "Didn't produce a single error")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")
    
    """
    """
    def test_junit_one_error(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        self.f = open(PROJECT_ROOT + "/testdata/SingleError.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message
        self.assertRegexpMatches(response.content, r'Errors:\s+1', "Didn't produce a single error")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")

    """
    """
    def test_junit_one_of_each_type(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=7)
        c = a.course
        self.f = open(PROJECT_ROOT + "/testdata/ThreeTestOneOfEach.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'Errors:\s+1', "Didn't produce a single error")
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'Failures:\s+1', "Didn't produce a single failure")
       
        self.assertRegexpMatches(response.content, r'Tests\s+run:\s+3', "Didn't run 3 tests")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")
    
    """
    Test a single test case that passes (no failures)
    """
    def test_junit_single_pass(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=1)
        self.f = open(PROJECT_ROOT + "/testdata/SimpleClass.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'OK\s+\(1\s+test\)', "Didn't pass a single test")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")

    """
    Test multiple passing test cases with no failures
    """
    def test_junit_multiple_pass(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=7)
        self.f = open(PROJECT_ROOT + "/testdata/ThreeTestClass.jar", 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'OK\s+\(3\s+tests\)', "Didn't pass all three tests")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            print response.content
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")

    """
    """
    def test_generate_large_grade_log(self):
        cli = Client()
        a = JavaAssignment.objects.get(pk=7)
        c = a.course
        self.f = open(PROJECT_ROOT+'/testdata/GenerateLargeGradeLog.jar', 'rb')
        
        response = cli.post("{0}submit/".format(a.get_absolute_url()),
                 {'first_name':"tester",
                  'last_name':"test",
                  'file':self.f
                  })
        self.f.close()
        
        # check the upload succeeded
        self.assertEqual(response.status_code, 200)
        
        # verify the correct error message shield 
        self.assertRegexpMatches(response.content, r'Grade results too long, truncating', "Didn't truncate grade log")
        
        #Should not be unable to parse the grade (should be able to parse the grade)
        if self.unable_to_parse_regex.search(response.content):             #pragma: no branch
            self.fail("Should have been able to parse grade.")
        s = JavaSubmission.objects.get(assignment=a, pk__gt=3)
        #Verify the proper grade is given
        self.assertRegexpMatches(response.content, r'(?m)Grade\D+{0} / {1}'.format(s.javagrade.tests_passed, s.javagrade.total_tests), "Didn't grade properly")


"""
Generate some random valid data to populate a CourseForm.
Then attempt to validate it.
"""
class CourseFormTests(TestCase):
    fixtures = ['users.json']
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
        self.data['creator'] = 1;
        
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
        if random.randint(0,1):             #pragma: no branch
            course_num += random.choice("CDW")
                               
        self.data['course_num'] = course_num
        
        c = CourseForm(self.data)
        
        # Validate the data. this should pass
        self.assertTrue(c.is_valid(), 
            """CourseForm failed on valid input: 
                course_num: {0} 
                course_title: {1} 
                year: {2} 
                term: {3} 
            """.format(course_num, self.data['course_title'], str(self.data['year']), self.data['term']))
            
    def test_invalid_course_num(self):
        # Now generate an invalid course number
        bad_course_num = ''.join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789CDW", random.randint(1,8)))
        
        while re.match(r'^[A-Z]{1,4}\d{3}[CDW]?$', bad_course_num):             #pragma: no branch
            bad_course_num = ''.join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789CDW", random.randint(1,8)))
            
        self.data['course_num'] = bad_course_num
            
        c = CourseForm(self.data)
        
        # Validate the data. This should fail
        self.assertFalse(c.is_valid(), 
            """CourseForm succeeded on invalid input: 
                course_num: {0}
                course_title: {1} 
                year: {2} 
                term: {3} 
            """.format(bad_course_num, self.data['course_title'], str(self.data['year']), self.data['term']))

"""
These tests verify that the assignment form validation is functioning properly,
both by rejecting invalid inputs, and by accepting valid inputs.
"""
class AssignmentFormTests(TestCase):
    fixtures = ['collector.json', 'users.json']
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
                'java_cmd':"-Xms32m -Xmx32m junit.textui.TestRunner",
                'javac_cmd':"-g",
                'options': 1,
                'creator': 1,
                'watchdog_wait':30,
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
        
        asgnmt_form = JavaAssignmentForm(self.data, file_data)
        
        # validate name and JAR file support
        self.assertTrue(asgnmt_form.is_valid(), # "Fields in error: " + ', '.join(asgnmt_form.errors.keys()))
            """JavaAssignmentForm failed on valid input
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
        f = open(PROJECT_ROOT+"/testdata/SimpleJUnitTest.jar", 'rb')
        file_data= {
                    'test_file': SimpleUploadedFile('SimpleJUnitTest.jar', f.read())
                    }
        f.close()
        
        asgnmt_form = JavaAssignmentForm(self.data, file_data)
        
        #Validate the valid Jar
        self.assertTrue(asgnmt_form.is_valid(), "Failed to accept valid Jar file")
    
    """
    Verify that invalid assignment names are rejected
    """
    def test_invalid_name(self):
        #Now generate a bad assignment name and see if we catch that
        name = ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_!@#$%^&*()", random.randint(0,25)))
        while re.match(r'^[a-zA-Z][\w\-]{,24}$', name):             #pragma: no branch
            name = ''.join(random.sample("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789-_!@#$%^&*()", random.randint(0,25)))
        self.data['name'] = name
        
        file_data = {
                     'test_file': SimpleUploadedFile('ValidJavaFile.java', "ffffff")
                     }
        
        asgnmt_form = JavaAssignmentForm(self.data, file_data)
        
        #Validate that we catch the bad name
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch bad name: {0}".format(name))
    
    """
    Verify that fake or corrupt .jar files are caught
    """
    def test_invalid_jar(self):
        # Generate a bad JAR file and see if we catch that
        f = open(PROJECT_ROOT+"/testdata/FakeJarFile.jar", 'rb')
        file_data = {
                     'test_file': SimpleUploadedFile('FakeJarFile.jar', f.read())
                     }
        f.close()
        
        asgnmt_form = JavaAssignmentForm(self.data, file_data)
        
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
        
        asgnmt_form = JavaAssignmentForm(self.data, file_data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch non-java/jar file: {0}".format(file_data['test_file']))
    
    """
    Verify that files without an extension are rejected.
    """
    def test_no_ext(self):
        #Test with no file extension
        file_data = {
                     'test_file': SimpleUploadedFile('NoFileExtension', "ffffff")
                     }
        
        asgnmt_form = JavaAssignmentForm(self.data, file_data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Failed to catch no file extension")
        
    """
    Verify that we provide an error when there is no test file
    """
    def test_no_test_file(self):
        asgnmt_form = JavaAssignmentForm(self.data)
        
        self.assertFalse(asgnmt_form.is_valid(), "Validated a form with no test file")
        
        self.assertIn(u"This assignment must include a JUnit test script.", asgnmt_form.errors['test_file'])

"""
These tests validate the operation of submission forms.
"""
class SubmissionFormTests(TestCase):
    fixtures = ['collector.json', 'users.json']
    longMessage = True
    def setUp(self):
        self.data = {
                     'first_name': ''.join(random.sample("abcdefghijklmnopqrstuvwxyz", random.randint(1,25))),
                     'last_name': ''.join(random.sample("abcdefghijklmnopqrstuvwxyz", random.randint(1,25)))
                     }
        f = open(PROJECT_ROOT+'/testdata/SimpleClass.jar', 'rb')
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
        s = JavaSubmissionForm(self.data, self.file_data)
        
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
        f = open(PROJECT_ROOT+'/testdata/FakeJarFile.jar', 'rb')
        file_data = {
                     'file': SimpleUploadedFile('FakeJar.jar', f.read())
                     }
        f.close()
        
        s = JavaSubmissionForm(self.data, file_data)
        
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
        
        s = JavaSubmissionForm(self.data, file_data)
        
        self.assertFalse(s.is_valid(), "Accepted a valid jar without an extension.")
    
    """
    Reject empty name strings
    """
    def test_empty_name(self):
        self.data['first_name'] = ''
        self.data['last_name'] = ''
        
        s = JavaSubmissionForm(self.data, self.file_data)
        
        self.assertFalse(s.is_valid(), "Failed to reject empty names")
        
    """
    Reject names that are entirely made up of symbols
    """
    def test_invalid_names(self):
        self.data['first_name'] = ''.join(random.sample(" `~!@#$%^&*()-_=+0123456789,.<>?|{}[]\\/\t", random.randint(1,25)))
        self.data['last_name'] = ''.join(random.sample(" `~!@#$%^&*()-_=+0123456789,.<>?|{}[]\\/\t", random.randint(1,25)))
        
        s = JavaSubmissionForm(self.data, self.file_data)
        
        self.assertFalse(s.is_valid(), "Failed to reject invalid names")
        
    """
    Verify that names with symbols and letters are properly cleaned
    """
    def test_name_cleaning(self):
        self.data['first_name'] = random.choice("abcdefghijklmnopqrstuvwxyz").join(random.sample(" abcdefghijklmnopqrstuvwxyz`~!@#$%^&*0123456789", random.randint(2,12)))
        self.data['last_name'] = random.choice("abcdefghijklmnopqrstuvwxyz").join(random.sample(" abcdefghijklmnopqrstuvwxyz`~!@#$%^&*0123456789", random.randint(2,12)))
        
        s = JavaSubmissionForm(self.data, self.file_data)
        
        self.assertTrue(s.is_valid(), 
                        """Failed to clean symbols from name. 
                            first name: {0}
                            last name:  {1}
                        """.format(self.data['first_name'], self.data['last_name']))
        fn = re.sub(r'[^a-z\-]', '', self.data['first_name'])
        ln = re.sub(r'[^a-z\-]', '', self.data['last_name'])
        self.assertEqual(s.cleaned_data['first_name'], fn, "Didn't clean first name")
        self.assertEqual(s.cleaned_data['last_name'], ln, "Didn't clean last name")
        self.assertIsNotNone(re.match(r'\w+(\-\w+)?', fn), "First name doesn't begin/end with a letter or has more than one hyphen")
        self.assertIsNotNone(re.match(r'\w+(\-\w+)?', ln), "last name doesn't begin/end with a letter or has more than one hyphen")
    
    """
    Put the course password on the form and validate
    """
    def test_valid_course_password(self):
        a = JavaAssignment.objects.get(pk=4) # get the assignment object with no password
        c = Course.objects.get(pk=2) # get the course object with a password
        s = JavaSubmission(assignment=a)
        
        self.data['passkey'] = c.passkey # set the password to the course password
        
        sfp = JavaSubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate course password")
    
    """
    Put the assignment password on the form and validate
    """ 
    def test_valid_assn_password(self):
        a = JavaAssignment.objects.get(pk=2) # get the assignment object with a password
        c = Course.objects.get(pk=1) # get the course object with no password
        s = JavaSubmission(assignment=a)
        
        self.data['passkey'] = a.passkey # set the password to the assignment password
        
        sfp = JavaSubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate assignment password")
    
    """
    Put the assignment password on the form, see if validation still succeeds
    """
    def test_assn_course_password(self):
        a = JavaAssignment.objects.get(pk=3) # get the assignment object with a password
        c = Course.objects.get(pk=2) # get the course object with a password
        s = JavaSubmission(assignment=a)
        
        self.data['passkey'] = a.passkey # set the password to the assignment password
        
        sfp = JavaSubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate assignment password")
     
    """
    Put the course password on the form, see if validation still succeeds
    """   
    def test_course_assn_password(self):
        a = JavaAssignment.objects.get(pk=3) # get the assignment object with a password
        c = Course.objects.get(pk=2) # get the course object with a password
        s = JavaSubmission(assignment=a)
        
        self.data['passkey'] = c.passkey # set the password to the assignment password
        
        sfp = JavaSubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertTrue(sfp.is_valid(), "Did not validate course password")
        
    """
    Put the course password on the form, see if validation still succeeds
    """   
    def test_invalid_password(self):
        a = JavaAssignment.objects.get(pk=3) # get the assignment object with a password
        c = Course.objects.get(pk=2) # get the course object with a password
        s = JavaSubmission(assignment=a)
        
        self.data['passkey'] = 'c.passkey' # set the password to something false
        
        sfp = JavaSubmissionFormP(self.data, self.file_data, instance=s)
        
        self.assertFalse(sfp.is_valid(), "Should not validate either password")
        
class AdminTests(TestCase):
    fixtures = ['users.json', ]
    

class MiscTests(TestCase):
    longMessage = True
    fixtures = ['collector.json', 'users.json']
    def setUp(self):
        pass
    def tearDown(self):
        pass
    
    """
    """
    @unittest.expectedFailure
    def test_display_grades(self):
        from collector.admin import AssignmentAdmin
        admin = AssignmentAdmin(Assignment, None)
        a = JavaAssignment.objects.get(pk=1)
        
        response = admin.display_grades(None, JavaAssignment.objects.filter(pk=1))
        
        if datetime.datetime.now() < a.due_date:
            self.assertRegexpMatches(response.__str__(), r'These grades are preliminary\. The assignment is not due yet\.',)
        
        s = a.submission_set.latest('submission_time')
        self.assertRegexpMatches(response.__str__(), s.grade, "Didn't find grade listed")
