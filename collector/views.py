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
    return render_to_response('collector/index.html', {'course_list':list})

def view_course(request, course_id):
    course = get_object_or_404(Course, course_num=course_id)
    assns = course.assignment_set.all()
    return render_to_response('collector/course.html', {'assignments':assns, 'course':course})
    
def view_assignment(request, course_id, assn_name):
    c = get_object_or_404(Course, course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name) # where the course and assignment name uniquely id the assn
    form = SubmissionForm()
    return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form})

def submit_assignment(request, course_id, assn_name):
    c = get_object_or_404(Course, course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name)
    
    #if now is later than assn.due_date:
    #    return and inform the user that submission is closed
    
    if request.method == 'POST':
        s = Submission(assignment=assn)
        form = SubmissionForm(request.POST, request.FILES, instance=s)
        
        if form.is_valid():
            # either warn the user they have submitted a late assignment
            # or in the validation, check if it is late, and disallow submission
            # then report an error to the user
            form.save()
            
            # Once saved, run the tests on the uploaded assignment and save the output as a string
            
            grader_output = "Upload Successful!" # placeholder for grader code
            
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':SubmissionForm(), 'grader_output':grader_output, })
            # Maybe use a Response redirect to prevent students from refreshing the page and resubmitting the same assignment. 
            # Might not be possible with the grader requirement
            #return HttpResponseRedirect(reverse('sukiyaki.imageboard.views.view_post', args=(tempPost.id,)))
        
        else: # Invalid form
            return render_to_response('collector/assignment.html', {'assignment':assn, 'form':form}) 
    
    else: # HTTP GET instead of POST
        return render_to_response('collector/assignment.html', {'assignment':assn, 'form':SubmissionForm()})
        