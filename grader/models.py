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
from django.core.files import File

from settings import MEDIA_ROOT, JUNIT_ROOT
from collector.models import JavaSubmission, GenericSubmission


import os, os.path, re, shutil, subprocess, tempfile, time, zipfile

class GenericGrade(models.Model):
    class Meta:
        abstract = True
    error = models.IntegerField("Error Code", default=0)
    # Error codes:
    # -1 - unable to parse/unknown error
    # 0 - no error. Success
    # 1 - compiler error(s)
    # 2 - unhandled Exception
    # 3 - watchdog timer hit
    error_text = models.CharField("Error string", max_length=255, default="")

class JavaGrade(GenericGrade):
    def filepath(self, filename):
        return self.submission.fileurl(filename)
    
    def __unicode__(self):
        if self.error:
            return "({0})".format(self.error_text)
        else:
            return "{0}/{1}".format(self.tests_passed, self.total_tests)

    submission = models.OneToOneField(JavaSubmission, help_text="Submission that generated this grade")
    grade_log = models.FileField(blank=True, upload_to=filepath, help_text="Contains the output of compilation and test execution.")
    total_tests = models.IntegerField(default=0)
    tests_passed = models.IntegerField(default=0)
    tests_failed = models.IntegerField(default=0)
    test_errors = models.IntegerField(default=0)
    junit_return = models.IntegerField("JUnit/javac Return code", help_text="Non-zero if either compilation or any tests failed.", default=0)
    
    def _extract_files(self, assignment, submission):
        # create a temporary directory
        submission_dir, file = os.path.split(submission.file.path) # temporary fix for filling the temp directory
        temp_dir = tempfile.mkdtemp(dir=submission_dir, suffix=submission.last_name) 
        # extract the student's work into the temporary directory
        ## create a zipfile object
        jar = zipfile.ZipFile(submission.file.path)
        ## Get a list of all files in the archive
        files = jar.namelist()
        ## find all "legal" files in the jar/zip (files that don't start with / and don't have .. in them)
        to_extract = []
        java_files = []
        for i in files:
            if not re.search("^/|/?\.\./|^META-INF|\.class$", i):
                to_extract.append(i)
                ## Add java files to their own list
                if re.search("\.java$", i):
                    java_files.append(i)
        ## extract legal files to the temporary directory
        jar.extractall(temp_dir, to_extract) 
        jar.close()
                
        # The extra-complicated manner copying is accomplished in is to assure case-sensitivity
        # On windows platforms, filename case is not maintained when stored on the filesystem.
        # It is, however, maintained in the database.
        grader_path, grader_name = os.path.split(assignment.test_file.path)
        grader_name = os.path.basename(assignment.test_file.name)
        
        # if the grader is a java file, copy it to the temporary dir
        if os.path.splitext(assignment.test_file.path.lower())[1] == '.java':
            shutil.copy2(os.path.join(grader_path, grader_name), temp_dir)
            java_files.append(grader_name)
        
        # if the grader is a JAR, extract the grader into the temporary dir
        elif os.path.splitext(assignment.test_file.path.lower())[1] == '.jar':      # pragma: no branch
            shutil.copy2(os.path.join(grader_path, grader_name), temp_dir)
            
            grader_jar = zipfile.ZipFile(os.path.join(temp_dir, grader_name))
            grader_extract = []
            for i in grader_jar.namelist():
                if not re.search("(^/|/?\.\./|^META-INF)", i):
                    grader_extract.append(i)
                    # To make sure the grader files get compiled, append them to the list
                    if re.search("\.java$", i):
                        java_files.append(i)
            # Extract the files
            grader_jar.extractall(temp_dir, grader_extract)
                    
            # Housekeeping: close the jar.
            grader_jar.close() 
        return (java_files, temp_dir)
    
    def _compile(self, cmd_parms, java_files, dir, output_handle):
        ## add the location of JUnit to the classpath, or environment
        if 'CLASSPATH' in os.environ:
            if JUNIT_ROOT not in os.environ['CLASSPATH']:
                os.environ['CLASSPATH'] = os.environ['CLASSPATH'] + os.pathsep + '.' + os.pathsep + JUNIT_ROOT
        else:
            os.environ['CLASSPATH'] =  '.' + os.pathsep + JUNIT_ROOT
        ## Prepare a list of arguments starting with the program name
        args = ['javac',  ]
        ## Append compiler options
        args.extend(cmd_parms)
        ## Append the java files to the list of args
        args.extend(java_files)
        ## Pretty Print: To the grade_log a header listing any messages here belonging to the compiler
        os.write(output_handle, "Compiler Output=================================================\n")
        ## compile and return the return code
        return subprocess.call(args=args, shell=False, stdout=output_handle, stderr=subprocess.STDOUT, cwd=dir, )
    
    def _parse_grade(self, junit_output, error):
        output = junit_output[-5:] # should get the last 5 lines of the output
        #print output # DEBUG
        output.reverse() # parse the last lines first
        parsed = False
        # If an error occurred, check the errors
        if error:
            for line in output:
                # First check for compiler errors
                match = re.search(r'^(\d+)\s+error(s)?', line, re.M)
                if match:
                    self.error = 1
                    self.error_text = "{0} compiler errors".format(match.group(1))
                    parsed = True
                    break
                # Then check for tests with failures/errors
                regex = r"^Tests run: (?P<total>\d+?),\s+Failures: (?P<failures>\d+?),\s+Errors: (?P<errors>\d+?)"
                match = re.search(regex, line, re.M)
                if match:
                    results = match.groupdict()
                    self.total_tests = int(results['total'])
                    self.tests_failed = int(results['failures'])
                    self.test_errors = int(results['errors'])
                    self.tests_passed = self.total_tests - (self.tests_failed + self.test_errors)
                    parsed = True
                    break
                
            # Check the whole output for an exception
            if not parsed:
                regexcep = re.compile(r"^Exception\s+in\s+thread\s+\"main\"\s+(?P<exception>[-\w._]+?):\s+(?P<class>[-\w._/]+?)$")
                for line in junit_output:
                    match = regexcep.search(line)
                    if match:
                        results = match.groupdict()
                        self.error = 2
                        self.error_text = "Exception in thread \"main\" {0}: {1}".format(results['exception'], results['class'])
                        parsed = True
                        break
                    
        # Or parse for success   
        else:
            for line in output:
                match = re.search(r"OK\s+\((?P<successful>\d+?)\s+test(s)?\)", line, re.M)
                if match:
                    results = match.groupdict()
                    self.tests_passed = self.total_tests = int(results['successful'])
                    parsed = True
                    break

        # Something unexpected happened and the grade could not be parsed
        if not parsed:
            self.error = -1
            self.error_text = "Unable to parse grade or unknown error. Please see grade log for details"
    
    def grade(self, assignment, submission):
        # Set the submission for this grade
        self.submission = submission
        
        # Create temporary working folder and extract files 
        java_files, temp_dir = self._extract_files(assignment, submission)
            
        # Create a temporary file for the gradelog
        output_handle, output_path = tempfile.mkstemp(suffix=".log", dir=temp_dir, text=True)
        
        ## actually compile
        javac = self._compile(assignment.javac_cmd.split(), java_files, temp_dir, output_handle)
        
        # If compilation is successful, run the tests
        if javac == 0: 
            name, ext = os.path.splitext(os.path.basename(assignment.test_file.name))
            args2 = ['java', ]
            args2.extend(assignment.java_cmd.split())
            args2.append(name)
            #print args2 # DEBUG
            # Pretty Print: to the grade_log that these messages belong to JUnit
            os.write(output_handle, "\nJUnit Test Output===============================================\n")
            # Run the JUnit tests in a subprocess
            java_proc = subprocess.Popen(args=args2, shell=False, stdout=output_handle, stderr=subprocess.STDOUT, cwd=temp_dir, )
            ## Have a watchdog timer in case of infinite loops in code.
            itercount = 0
            WATCHDOG_POLL_TIME = 0.3 # a conservative trade-off between responsiveness and processor usage
            WATCHDOG_WAIT_TIME = assignment.watchdog_wait
            WATCHDOG_ITERATIONS = WATCHDOG_WAIT_TIME / WATCHDOG_POLL_TIME
            while java_proc.poll() is None and (itercount <= WATCHDOG_ITERATIONS):
                itercount += 1
                time.sleep(WATCHDOG_POLL_TIME)
            ## If the code is still executing after WATCHDOG_WAIT_TIME seconds, kill the process.
            if itercount > WATCHDOG_ITERATIONS:
                java_proc.kill()
                self.error = 3; # Set the error
                self.error_text = "Watchdog timer killed the test after {0} seconds".format(WATCHDOG_WAIT_TIME)
                os.write(output_handle, "\nExecution took longer than {0} seconds, terminating test. Possible infinite loop?".format(WATCHDOG_WAIT_TIME))
            else:
                ## save the return value
                self.junit_return = java_proc.returncode
       # otherwise, set the error
        else:
            self.junit_return = javac

        # Save the grade log to the JavaGrade
        log_file = File(open(output_path, 'rU'))
        log_file.seek(0)
        self.grade_log.save(os.path.basename(output_path), log_file, save=True)  
        log_file.seek(0)

        # Determine how much grade log to read into memory
        if log_file.size < 2097152:
            output = log_file.readlines()
        # For large logs, read the first ~100kB and last ~100kB
        else:
            output = log_file.readlines(100000)
            output.extend(["\n==================================================================================", 
                           "\n Grade results too long, truncating.............................................\n", 
                           "==================================================================================\n"])
            log_file.seek(-100000, os.SEEK_END)
            output.extend(log_file.readlines(100000))
            
        ## Extract the grade information from the output only if the watchdog timer was not hit
        if self.error != 3:
            self._parse_grade(output, (javac or self.junit_return))
        
        ## Save the grades  
        self.save()
        ## close open files
        log_file.close()
        os.close(output_handle)
        ## delete the temporary directory
        shutil.rmtree(temp_dir)
        ## return the output
        return ''.join(output)
