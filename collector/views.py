# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404

from assignmentcollectorgrader.collector.models import *

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
        
        if form.is_valid():
            
            if datetime.datetime.now() > assn.due_date:
                late = "Your submission is past the due date.\n"
            else:
                late = ""
            # either warn the user they have submitted a late assignment
            # or in the validation, check if it is late, and disallow submission
            # then report an error to the user
            form.save()
            
            # Once saved, run the tests on the uploaded assignment and save the output as a string
            
            grader_output = "Upload Successful!" + late # placeholder for grader code
            
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':SubmissionForm(), 'grader_output':grader_output, })
            # Maybe use a Response redirect to prevent students from refreshing the page and resubmitting the same assignment. 
            # Might not be possible with the grader requirement
            #return HttpResponseRedirect(reverse('sukiyaki.imageboard.views.view_post', args=(tempPost.id,)))
        
        else: # Invalid form
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form}) 
    
    else: # HTTP GET instead of POST
        return render_to_response('collector/assignment.html', {'assignment':assn, 'form':SubmissionForm()})
        