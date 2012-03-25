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

from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.http import HttpResponseRedirect, Http404

from django.core.files import File
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage

from collector.models import *
from settings import JUNIT_ROOT

from grader.models import *

import os, os.path, re, shutil, subprocess, tempfile, datetime, time, zipfile
    

def course_index(request, **kwargs):
    if kwargs.has_key('year') and kwargs.has_key('term'):
        list = get_list_or_404(Course, year=kwargs['year'], term=kwargs['term'])
        return render_to_response('index.html', {'course_list':list, 'specific_term_course_index':(kwargs['year'],kwargs['term']), })
    elif kwargs.has_key('year'):
        list = get_list_or_404(Course, year=kwargs['year'])
        return render_to_response('index.html', {'course_list':list, 'specific_term_course_index':(kwargs['year'],None), })
    else:
        list = Course.objects.all().order_by('year', 'term')
    return render_to_response('index.html', {'course_list':list, 'course_index':'a',})

def view_about(request):
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_for_filename
        from settings import PROJECT_ROOT
    except ImportError:
        return render_to_response('about.html', {'major_version':MAJOR_VERSION, 'minor_version':MINOR_VERSION, })
    else:
        styles = ""
        sources = []
        for root, dirs, files in os.walk(PROJECT_ROOT, ):
            for file in files:
                name, ext = os.path.splitext(file)
                if ext in ['.py', '.html',] and name not in ['settings', 'manage']:
                    lexer = get_lexer_for_filename(file)
                    formatter = HtmlFormatter(linenos='inline',  anchorlinenos=False) # lineanchors=os.path.basename(root)+'.'+name,
                    f = open(os.path.join(root, file),'rU')
                    sources.append( (os.path.join(os.path.basename(root), file), highlight(f.read(), lexer, formatter)) )
                    f.close()
        styles = HtmlFormatter().get_style_defs()
        return render_to_response('about.html', {'major_version':MAJOR_VERSION, 'minor_version':MINOR_VERSION, 'styles': styles, 'sources':sources})

def view_course(request, year, term, course_id):
    course = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assns = course.javaassignment_set.order_by('due_date').filter(due_date__gte=datetime.datetime.now())
    late = course.javaassignment_set.order_by('due_date').filter(due_date__lt=datetime.datetime.now())
    return render_to_response('course.html', {'assignments':assns, 'late':late, 'course':course})

def view_assignment(request, year, term, course_id, assn_name):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(JavaAssignment, course=c.pk, name=assn_name) # where the course and assignment name uniquely id the assn

    if datetime.datetime.now() < assn.start_date:
        form = None
    elif (not assn.allow_late) and datetime.datetime.now() > assn.due_date:
        form = None
    else:
        # If there is no passkey, use a different form
        if assn.passkey == '' and c.passkey == '':
            form = JavaSubmissionForm()
        else:
            form = JavaSubmissionFormP()
    return render_to_response('assignment.html', {'assignment':assn, 'form':form,})

def view_submission(request, year, term, course_id, assn_name, sub_id):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(JavaAssignment, course=c.pk, name=assn_name)
    sub = get_object_or_404(JavaSubmission, id=sub_id)
    
    grade = None
    if JavaGrade.objects.filter(submission=sub).exists():
        grade = sub.javagrade
        
        if grade.grade_log:
            if grade.grade_log.size < 2097152:
                grader_output = grade.grade_log.read()
            else:
                grader_output = ''.join(grade.grade_log.readlines(100000))
                grader_output +="\n=================================================================================="
                grader_output +="\n Grade results too long, truncating.............................................\n"
                grader_output +="==================================================================================\n"
                grade.grade_log.seek(-100000, os.SEEK_END)
                grader_output += ''.join(grade.grade_log.readlines(100000))
                grader_output += "\n Grade results are too long. Please remove any extraneous output (println(), etc.) before submitting again."
        else:
            grader_output = "No grade results to display."
    else:
        grader_output = "No grade results to display."
    
    return render_to_response('assignment.html', {'assignment':assn, 'grader_output':grader_output, 'submission':sub, 'grade':grade})

def submit_assignment(request, year, term, course_id, assn_name):
    c = get_object_or_404(Course, year=year, term=term.lower(), course_num=course_id)
    assn = get_object_or_404(JavaAssignment, course=c.pk, name=assn_name)
    grader = None
    
    if request.method == 'POST':
        s = JavaSubmission(assignment=assn)
        # Choose the right kind of form to perform validation
        if assn.passkey == '' and c.passkey == '':
            form = JavaSubmissionForm(request.POST, request.FILES, instance=s)
        else:
            form = JavaSubmissionFormP(request.POST, request.FILES, instance=s)
        
        # If the user is trying to upload a submission before the assignment is available, inform them
        if datetime.datetime.now() < assn.start_date:
            error_msg = 'Submission has not opened for this assignment. Please wait until the assignment is available to submit your code.'
            return render_to_response('assignment.html', {'assignment':assn, 'grader_output':error_msg})
        
        #if now is later than assn.due_date:
        #    return and inform the user that submission is closed
        if (datetime.datetime.now() > assn.due_date) and not assn.allow_late:
            error_msg = 'It is past the due date and late assignments are not accepted. Sorry. :('
            return render_to_response('assignment.html', {'assignment':assn, 'grader_output':error_msg})
        # else if the assignment is late, but late submissions are allowed
        elif (datetime.datetime.now() > assn.due_date) and assn.allow_late:
            late = "You are turning in this assignment past the due date. But it will be accepted anyway. :)\n\n"
        else:
            late = ""
        
        if form.is_valid():

            # Calculate which submission number this is
            count = JavaSubmission.objects.filter(last_name=form.cleaned_data['last_name'], first_name=form.cleaned_data['first_name'], assignment=assn, ).count()
            if count > 0:
                form.instance.submission_number = count + 1
            
            # Determine if the maximum number of submissions has been reached.
            if count >= assn.max_submissions > 0:
                error_msg = "I'm sorry, but you've reached the maximum number of attempts."
                return render_to_response('assignment.html', {'assignment':assn, 'grader_output':error_msg})
            
            # Save the form to disk/database
            submission = form.save()
            
            # Once saved, run the tests on the uploaded assignment and save the output as a string
            
            grader_output = late 
            if assn.max_submissions > 0:
                grader_output += "You have {0} attempts remaining for this assignment.\n\n".format(assn.max_submissions - count - 1)
            
            # Grade this assignment only if grading is turned on.
            if (assn.options & 1) and assn.test_file:
                # append the grader output to send it to the user.
                grader = JavaGrade()
                grader_output += grader.grade(assn, submission)
                # If the user gave an email address, send them the grade log
                if submission.email:
                    subject = "{2}, {3}--Attempt: {6}--{0}/{1}--{4}-{5}".format(submission.javagrade.tests_passed,
                                                                       submission.javagrade.total_tests,
                                                                       submission.last_name, 
                                                                       submission.first_name, 
                                                                       c.course_num, 
                                                                       assn.name, 
                                                                       submission.submission_number)
                     # if the grade_log is less than 200K, send it in the body
                    if len(grader_output) < 205000:
                        email = EmailMessage(subject,
                                              grader_output,
                                              c.email,
                                              [submission.email, ],
                                              )
                    # Otherwise, send it as an attachment
                    else:
                        email = EmailMessage(subject,
                                              "See attached file for grade results",
                                              c.email,
                                              [submission.email, ],
                                              )
                        email.attach_file(submission.javagrade.grade_log.path)
                    email.send(fail_silently=True)
            
            return render_to_response('assignment.html', {'assignment':assn, 'grader_output':grader_output, 'submission':submission, 'grade':grader})
        
        else: # Invalid form
            return render_to_response('assignment.html', {'assignment':assn, 'form':form}) 
    
    else: # HTTP GET instead of POST
        return HttpResponseRedirect(reverse('collector.views.view_assignment', args=(c.year, c.term, c.course_num, assn.name,)))
