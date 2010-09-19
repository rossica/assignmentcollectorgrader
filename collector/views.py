# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404

from django.core.files import File

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
    # TODO: Only show assignments that have started before now()
    assns = course.assignment_set.all()
    return render_to_response('collector/course.html', {'assignments':assns, 'course':course})
    
def view_assignment(request, year, term, course_id, assn_name):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name) # where the course and assignment name uniquely id the assn
    form = SubmissionForm()
    # If there is no passkey, use a different form, or hide the passkey field on the fly.
    # It's ok if it's blank if the passkey field is blank on the assingment
    return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form})

def submit_assignment(request, year, term, course_id, assn_name):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name)
    
    import datetime
    
    if request.method == 'POST':
        s = Submission(assignment=assn)
        form = SubmissionForm(request.POST, request.FILES, instance=s)
        
        #if now is later than assn.due_date:
        #    return and inform the user that submission is closed
        if (datetime.datetime.now() > assn.due_date) and not assn.allow_late:
            error_msg = 'It is past the due date and late assignments are not allowed. Sorry.'
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form, 'grader_output':error_msg})
        # else if the assignment is late, but late submissions are allowed
        elif datetime.datetime.now() > assn.due_date and assn.allow_late:
            late = "You are turning this assignment in past the due date. But it will be accepted anyway.\n\n"
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
                return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form, 'grader_output':error_msg})
                
            
            # Save the form to disk/database
            submission = form.save()
            
            # Once saved, run the tests on the uploaded assignment and save the output as a string
            
            grader_output = 'Upload Successful!\n\n' + late 
            if assn.max_submissions > 0:
                grader_output += "You have {0} attempts remaining for this assignment.\n\n".format(assn.max_submissions - count - 1)
            
            # append the grader output to send it to the user.
            grader_output += _grader(assn, submission)
            
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':SubmissionForm(), 'grader_output':grader_output, })
            # Maybe use a Response redirect to prevent students from refreshing the page and resubmitting the same assignment. 
            # Might not be possible with the grader requirement
            #return HttpResponseRedirect(reverse('sukiyaki.imageboard.views.view_post', args=(tempPost.id,)))
        
        else: # Invalid form
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form}) 
    
    else: # HTTP GET instead of POST
        return render_to_response('collector/assignment.html', {'assignment':assn, 'form':SubmissionForm()})
    

def _grader(assignment, submission):
    import os, re, shutil, subprocess, tempfile, time, zipfile
    # create a temporary directory
    submission_dir, file = os.path.split(submission.file.path)
    temp = tempfile.mkdtemp(dir=submission_dir)
    # extract the student's work into the temporary directory
    ## create a zipfile object
    jar = zipfile.ZipFile(submission.file.path)
    ## Get a list of all files in the archive
    files = jar.namelist()
    ## find all "legal" files in the jar/zip (files that don't start with / and don't have .. in them)
    to_extract = []
    for i in files:
        if not re.search("(^/|.*\.\..*|^META-INF.*)", i):
            to_extract.append(i)
    ## extract legal files to the temporary directory
    jar.extractall(temp, to_extract) 
    # delete all class files
    temp_files = os.listdir(temp)
    ## find all class files
    ## delete them
    for i in temp_files:
        if re.search("\.class$", i):
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
        os.environ['CLASSPATH'] = os.environ['CLASSPATH'] + os.pathsep + JUNIT_ROOT + os.pathsep + '.' + os.pathsep + os.pathsep
    else:
        os.environ['CLASSPATH'] = JUNIT_ROOT + os.pathsep + '.' + os.pathsep + os.pathsep
    ## Get list of .java files to compile.
    args = ['javac',  ] #  '-verbose', 
    for i in temp_files:
        if re.search("\.java$", i):
            args.append(i)
    ## actually compile
    javac = subprocess.Popen(args=args, shell=False, stdout=output_handle, stderr=subprocess.STDOUT, cwd=temp, )
    ## wait until the compilation is done
    javac.wait() # may deadlock. Let's see
    #while javac.poll() is None:
    #    time.sleep(.25) # this is a work-around to avoid using javac.wait() because of the risk of deadlocking the subprocess
    # If compilation is unsuccessful, return the program output
    if javac.returncode > 0:
    ## first move the output file to the submission directory tree
        #submission.grade_log.save(submission.fileurl(os.path.basename(output_path)), File(open(output_path)), save=True)
        file = File(open(output_path))
        submission.grade_log.save(os.path.basename(output_path), file, save=True)  
    ## read in the output
        output = submission.grade_log.read()
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
        args = ['java', 'junit.textui.TestRunner', name.encode('ascii')]
        java = subprocess.Popen(args=args, shell=False, stdout=output_handle, stderr=subprocess.STDOUT, cwd=temp, )
    ## Wait for the tests to complete
        java.wait()
        #while java.poll() is None:
        #    pass
    ## Save the test output
        file = File(open(output_path))
        submission.grade_log.save(os.path.basename(output_path), file, save=True)  
    ## read in the output
        output = submission.grade_log.read()
    ## close open files
        submission.grade_log.close()
        file.close()
        os.close(output_handle)
        jar.close()
    ## delete the temporary directory
        shutil.rmtree(temp)
    ## return the output
        return output

        
        # Save the state information to the output for debugging
        #environment = ''
        #for i in os.environ.items():
        #    environment += ' '.join([i[0], ':', i[1], '\n'])
        #os.write(output_handle, environment)
