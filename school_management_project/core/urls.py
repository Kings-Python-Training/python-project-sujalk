from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('parent-dashboard/', views.parent_dashboard, name='parent_dashboard'),
    
    # Student Management
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    
    # Attendance
    path('attendance/mark/<int:class_id>/', views.mark_attendance, name='mark_attendance'),
    
    # Grades
    path('grades/upload/', views.upload_grades, name='upload_grades'),
    
    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    
    # Announcements
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    
    # Messages
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/inbox/', views.inbox, name='inbox'),
    
    # Parent
    path('child/<int:student_id>/', views.view_child_details, name='child_details'),
]