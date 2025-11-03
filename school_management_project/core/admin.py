from django.contrib import admin
from .models import *


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "phone"]
    list_filter = ["role"]
    search_fields = ["user__username", "user__email", "phone"]


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ["name", "section", "class_teacher", "academic_year"]
    list_filter = ["academic_year"]
    search_fields = ["name", "section"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ["class_obj", "subject", "teacher"]
    list_filter = ["class_obj"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["admission_number", "user", "class_enrolled", "roll_number"]
    list_filter = ["class_enrolled"]
    search_fields = ["admission_number", "user__username"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["student", "date", "status", "marked_by"]
    list_filter = ["status", "date"]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "exam_type", "marks_obtained", "total_marks"]
    list_filter = ["exam_type", "subject"]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "class_subject", "due_date", "total_marks"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "assignment", "submitted_at", "marks_obtained"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "target_role", "created_by", "created_at", "is_active"]
    list_filter = ["target_role", "is_active"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "receiver", "subject", "sent_at", "is_read"]
    list_filter = ["is_read"]
