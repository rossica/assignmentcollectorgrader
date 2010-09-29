# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404

from django.core.files import File
from django.core.urlresolvers import reverse

from assignmentcollectorgrader.collector.models import *
from assignmentcollectorgrader.settings import JUNIT_ROOT

def render_to_csrf(request, template, context):
    from django.core.context_processors import csrf
    from django.shortcuts import render_to_response
    c = {}
    c.update(csrf(request))
    try:
        c.update(context)
        return render_to_response(template, c)
    except:
        pass
    

def course_index(request):
    list = Course.objects.all();
    return render_to_response('collector/index.html', {'course_list':list, 'course_index':'a',})

def specific_term_course_index(request, year, term):
    list = Course.objects.filter(year=year, term=term.lower())
    return render_to_response('collector/index.html', {'course_list':list, 'specific_term_course_index':(year,term), })

def view_course(request, year, term, course_id):
    course = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    import datetime
    # TODO: Only show assignments that have started before now() -- FIXED: can't submit to assignments that start before now
    assns = course.assignment_set.order_by('due_date').filter(due_date__gte=datetime.datetime.now())
    late = course.assignment_set.order_by('due_date').filter(due_date__lt=datetime.datetime.now())
    return render_to_response('collector/course.html', {'assignments':assns, 'late':late, 'course':course})
    
def view_assignment(request, year, term, course_id, assn_name):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name) # where the course and assignment name uniquely id the assn
    import datetime

    if datetime.datetime.now() < assn.start_date:
        form = None
    elif (not assn.allow_late) and datetime.datetime.now() > assn.due_date:
        form = None
    else:
        # If there is no passkey, use a different form
        if assn.passkey == '' and c.passkey == '':
            form = SubmissionForm()
        else:
            form = SubmissionFormP()
    return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form,})

def view_submission(request, year, term, course_id, assn_name, sub_id):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name)
    sub = get_object_or_404(Submission, id=sub_id)
    
    grader_output = sub.grade_log.read()
    
    return render_to_response('collector/assignment.html', {'assignment':assn, 'grader_output':grader_output, 'submission':sub})

def submit_assignment(request, year, term, course_id, assn_name):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name)
    
    import datetime
    
    if request.method == 'POST':
        s = Submission(assignment=assn, course=c)
        # Choose the right kind of form to perform validation
        if assn.passkey == '' and c.passkey == '':
            form = SubmissionForm(request.POST, request.FILES, instance=s)
        else:
            form = SubmissionFormP(request.POST, request.FILES, instance=s)
        
        # If the user is trying to upload a submission before the assignment is available, inform them
        if datetime.datetime.now() < assn.start_date:
            error_msg = 'Submission has not opened for this assignment. Please wait until the assignment is available to submit your code.'
            return render_to_response('collector/assignment.html', {'assignment':assn, 'grader_output':error_msg})
        
        #if now is later than assn.due_date:
        #    return and inform the user that submission is closed
        if (datetime.datetime.now() > assn.due_date) and not assn.allow_late:
            error_msg = 'It is past the due date and late assignments are not accepted. Sorry. :('
            return render_to_response('collector/assignment.html', {'assignment':assn, 'grader_output':error_msg})
        # else if the assignment is late, but late submissions are allowed
        elif (datetime.datetime.now() > assn.due_date) and assn.allow_late:
            late = "You are turning in this assignment past the due date. But it will be accepted anyway. :)\n\n"
        else:
            late = ""
        
        if form.is_valid():

            # Calculate which submission number this is
            count = Submission.objects.filter(last_name=form.cleaned_data['last_name'], first_name=form.cleaned_data['first_name'], assignment=assn, ).count()
            if count > 0:
                form.instance.submission_number = count + 1
            
            # Determine if the maximum number of submissions has been reached.
            if count >= assn.max_submissions > 0:
                error_msg = "I'm sorry, but you've reached the maximum number of submissions."
                return render_to_response('collector/assignment.html', {'assignment':assn, 'grader_output':error_msg})
            
            # Save the form to disk/database
            submission = form.save()
            
            # Once saved, run the tests on the uploaded assignment and save the output as a string
            
            grader_output = late 
            if assn.max_submissions > 0:
                grader_output += "You have {0} attempts remaining for this assignment.\n\n".format(assn.max_submissions - count - 1)
            
            # If this assignment contains a test file
            if assn.test_file:
                # append the grader output to send it to the user.
                grader_output += _grader(assn, submission)
            
            return render_to_response('collector/assignment.html', {'assignment':assn, 'grader_output':grader_output, 'submission':submission})
        
        else: # Invalid form
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form}) 
    
    else: # HTTP GET instead of POST
        return HttpResponseRedirect(reverse('assignmentcollectorgrader.collector.views.view_assignment', args=(c.year, c.term, c.course_num, assn.name,)))
        #if datetime.datetime.now() < assn.start_date:
        #    return render_to_response('collector/assignment.html', {'assignment':assn, })
        #else:
        #    return render_to_response('collector/assignment.html', {'assignment':assn, 'form':SubmissionForm()})
    

def _grader(assignment, submission):
    import os, re, shutil, subprocess, tempfile, time, zipfile
    # create a temporary directory
    #submission_dir, file = os.path.split(submission.file.path)
    #temp = tempfile.mkdtemp(dir=submission_dir)
    temp = tempfile.mkdtemp()
    # extract the student's work into the temporary directory
    ## create a zipfile object
    jar = zipfile.ZipFile(submission.file.path)
    ## Get a list of all files in the archive
    files = jar.namelist()
    ## find all "legal" files in the jar/zip (files that don't start with / and don't have .. in them)
    to_extract = []
    for i in files:
        if not re.search("(^/|/?\.\./|^META-INF)", i):
            to_extract.append(i)
    ## extract legal files to the temporary directory
    jar.extractall(temp, to_extract) 
    # delete all class files 
    for i in os.listdir(temp):
    ## find all class files
        if re.search("\.class$", i):
    ## delete them
            os.remove(os.path.join(temp,i))
    # if the grader is a java file, copy it to the temporary dir
    # the extra-complicated manner this is accomplished in, is to assure case-sensitivity
    grader_path, grader_name = os.path.split(assignment.test_file.path)
    grader_name = os.path.basename(assignment.test_file.name)
    shutil.copy2(os.path.join(grader_path, grader_name), temp)
    # TODO: if the grader is a JAR, extract the grader into the temporary dir
    # compile all java files, saving all output
    output_handle, output_path = tempfile.mkstemp(suffix=".log", dir=temp, text=True)
    ## add the location of JUnit to the classpath, or environment
    if 'CLASSPATH' in os.environ:
        if JUNIT_ROOT not in os.environ['CLASSPATH']:
            os.environ['CLASSPATH'] = os.environ['CLASSPATH'] + os.pathsep + '.' + os.pathsep + JUNIT_ROOT # os.pathsep + 
    else:
        os.environ['CLASSPATH'] =  '.' + os.pathsep + JUNIT_ROOT # os.pathsep + os.pathsep +
    ## Get list of .java files to compile.
    args = ['javac',  ] #  '-verbose', 
    ## Append the java files to the list of args
    args.append(grader_name)
    for i in to_extract:
        if re.search("\.java$", i):
            args.append(i)
    ## Alternate way of doing it
    #for i in os.listdir(temp):
    #    if re.search("\.java$", i):
    #        args.append(i)
    ## actually compile
    javac = subprocess.call(args=args, shell=False, stdout=output_handle, stderr=subprocess.STDOUT, cwd=temp, )
    # If compilation is unsuccessful, return the program output
    if javac > 0:
    ## first save the output file to the submission
        file = File(open(output_path))
        submission.grade_log.save(os.path.basename(output_path), file, save=True)  
    ## read in the output
        output = submission.grade_log.read()
    ## Extract the grade information from the output
        #match = re.search(r'([1]) error|(\d+) errors', output)
        match = re.search(r'^(\d+)\s+error', output, re.M)
    ## Save to the submission
        submission.grade = "0 ({0} compiler errors)".format(match.group(1))
        submission.save()
    ## close open files
        file.close()
        submission.grade_log.close()
        os.close(output_handle)
        jar.close()
    ## delete the temporary folder
        shutil.rmtree(temp)
    ## return the output
        return output
    # else, run the tests, saving output
    else: 
    ## Run the tests
        name, ext = os.path.splitext(os.path.basename(assignment.test_file.name))
        args2 = ['java', 'junit.textui.TestRunner', name]
        java = subprocess.call(args=args2, shell=False, stdout=output_handle, stderr=subprocess.STDOUT, cwd=temp, )
    ## Save the test output to the submission
        file = File(open(output_path))
        submission.grade_log.save(os.path.basename(output_path), file, save=True)  
    ## read in the output
        output = submission.grade_log.read()
    ## Extract the grade information from the output
    ### If java returns with an error code
        if java > 0:
    ### First check for a JUnit failure
            regex = r"^Tests\s+run:\s+(?P<total>\d+?),\s+Failures:\s+(?P<failures>\d+?),\s+Errors:\s+(?P<errors>\d+?)$"
            match = re.search(regex, output, re.M)
            if match:
                results = match.groupdict()
                submission.grade = "{0}/{1}".format(int(results['total']) - (int(results['failures']) + int(results['errors'])), results['total'])
    ### Otherwise, check for an Exception
            else:
                regex = "^Exception\s+in\s+thread\s+\"main\"\s+(?P<exception>[a-zA-Z0-9._]+?):\s+(?P<class>[a-zA-Z0-9._]+?)$"
                match = re.search(regex, output, re.M)
                results = match.groupdict()
                submission.grade = "0 (Exception in thread \"main\" {0}: {1})".format(results['exception'], results['class'])
    ### If java runs just fine
        else:
            regex = r"^OK\s+[(](?P<successful>\d+?)\s+tests[)]$"
            match = re.search(regex, output, re.M)
            results = match.groupdict()
            submission.grade = "{0}/{0}".format(results['successful'])
    ## Save to the submission    
        submission.save()
    ## close open files
        submission.grade_log.close()
        file.close()
        os.close(output_handle)
        jar.close()
    ## delete the temporary directory
        shutil.rmtree(temp)
    ## return the output
        return output
