# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404

from AssignmentCollectorGrader.collector.models import Course

def course_index(request):
    list = Course.objects.all();
    return render_to_response('collector/index.html', {'course_list':list})

def view_assignments(request, course_id):
    course = get_object_or_404(Course, course_num=course_id)
    assns = course.assignment_set.filter()
    return render_to_response('collector/course.html', {'assignments':assns})
    
def view_assignment(request, course_id, assn_name):
    c = get_object_or_404(Course, course_num=course_id)
    assn = get_object_or_404(Assignment, course=c.pk, name=assn_name) # where the course and assignment name uniquely id the assn