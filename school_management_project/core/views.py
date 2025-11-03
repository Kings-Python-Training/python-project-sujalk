from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import *
from .forms import *


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect("login")


@login_required
def dashboard(request):
    user_role = request.user.profile.role

    if user_role == "admin":
        return redirect("admin_dashboard")
    elif user_role == "teacher":
        return redirect("teacher_dashboard")
    elif user_role == "student":
        return redirect("student_dashboard")
    elif user_role == "parent":
        return redirect("parent_dashboard")
    else:
        messages.error(request, "Invalid user role")
        return redirect("login")


@login_required
def admin_dashboard(request):
    if request.user.profile.role != "admin":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    context = {
        "total_students": Student.objects.count(),
        "total_teachers": UserProfile.objects.filter(role="teacher").count(),
        "total_classes": Class.objects.count(),
        "total_subjects": Subject.objects.count(),
        "recent_students": Student.objects.select_related(
            "user", "class_enrolled"
        ).order_by("-admission_date")[:5],
        "announcements": Announcement.objects.filter(is_active=True).order_by(
            "-created_at"
        )[:5],
    }
    return render(request, "admin_dashboard.html", context)


@login_required
def teacher_dashboard(request):
    if request.user.profile.role != "teacher":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    assigned_subjects = ClassSubject.objects.filter(
        teacher=request.user
    ).select_related("class_obj", "subject")

    context = {
        "assigned_subjects": assigned_subjects,
        "pending_submissions": Submission.objects.filter(
            assignment__created_by=request.user, marks_obtained__isnull=True
        ).count(),
        "announcements": Announcement.objects.filter(
            Q(target_role="teacher") | Q(target_role="")
        )
        .filter(is_active=True)
        .order_by("-created_at")[:5],
        "messages": Message.objects.filter(
            receiver=request.user, is_read=False
        ).count(),
    }
    return render(request, "teacher_dashboard.html", context)


@login_required
def student_dashboard(request):
    if request.user.profile.role != "student":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    student = request.user.student_profile
    recent_attendance = Attendance.objects.filter(student=student).order_by("-date")[
        :10
    ]
    recent_grades = (
        Grade.objects.filter(student=student)
        .select_related("subject")
        .order_by("-exam_date")[:5]
    )

    submitted_assignment_ids = Submission.objects.filter(student=student).values_list(
        "assignment_id", flat=True
    )
    pending_assignments = (
        Assignment.objects.filter(class_subject__class_obj=student.class_enrolled)
        .exclude(id__in=submitted_assignment_ids)
        .order_by("due_date")[:5]
    )

    context = {
        "student": student,
        "recent_attendance": recent_attendance,
        "recent_grades": recent_grades,
        "pending_assignments": pending_assignments,
        "announcements": Announcement.objects.filter(
            Q(target_role="student")
            | Q(target_role="")
            | Q(target_class=student.class_enrolled)
        )
        .filter(is_active=True)
        .order_by("-created_at")[:5],
    }
    return render(request, "student_dashboard.html", context)


@login_required
def parent_dashboard(request):
    if request.user.profile.role != "parent":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    children = Student.objects.filter(parent=request.user).select_related(
        "user", "class_enrolled"
    )

    context = {
        "children": children,
        "announcements": Announcement.objects.filter(
            Q(target_role="parent") | Q(target_role="")
        )
        .filter(is_active=True)
        .order_by("-created_at")[:5],
    }
    return render(request, "parent_dashboard.html", context)


@login_required
def student_list(request):
    if request.user.profile.role != "admin":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    students = Student.objects.select_related("user", "class_enrolled").all()
    return render(request, "student_list.html", {"students": students})


@login_required
def student_create(request):
    if request.user.profile.role != "admin":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        student_form = StudentForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid() and student_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.role = "student"
            profile.save()

            student = student_form.save(commit=False)
            student.user = user
            student.save()

            messages.success(request, "Student created successfully")
            return redirect("student_list")
    else:
        user_form = UserRegisterForm()
        profile_form = UserProfileForm()
        student_form = StudentForm()

    return render(
        request,
        "student_form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "student_form": student_form,
        },
    )


@login_required
def mark_attendance(request, class_id):
    if request.user.profile.role not in ["admin", "teacher"]:
        messages.error(request, "Access denied")
        return redirect("dashboard")

    class_obj = get_object_or_404(Class, id=class_id)
    students = Student.objects.filter(class_enrolled=class_obj).select_related("user")

    if request.method == "POST":
        date = request.POST.get("date")
        for student in students:
            status = request.POST.get(f"status_{student.id}")
            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    date=date,
                    defaults={"status": status, "marked_by": request.user},
                )
        messages.success(request, "Attendance marked successfully")
        return redirect("teacher_dashboard")

    today = timezone.now().date()
    return render(
        request,
        "mark_attendance.html",
        {"class_obj": class_obj, "students": students, "today": today},
    )


@login_required
def upload_grades(request):
    if request.user.profile.role != "teacher":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    if request.method == "POST":
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.uploaded_by = request.user
            grade.save()
            messages.success(request, "Grade uploaded successfully")
            return redirect("teacher_dashboard")
    else:
        form = GradeForm()

    return render(request, "grade_form.html", {"form": form})


@login_required
def assignment_create(request):
    if request.user.profile.role != "teacher":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    if request.method == "POST":
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, "Assignment created successfully")
            return redirect("teacher_dashboard")
    else:
        form = AssignmentForm()

    return render(request, "assignment_form.html", {"form": form})


@login_required
def assignment_list(request):
    if request.user.profile.role == "student":
        student = request.user.student_profile
        assignments = Assignment.objects.filter(
            class_subject__class_obj=student.class_enrolled
        ).order_by("-created_at")
    elif request.user.profile.role == "teacher":
        assignments = Assignment.objects.filter(created_by=request.user).order_by(
            "-created_at"
        )
    else:
        assignments = Assignment.objects.all().order_by("-created_at")

    return render(request, "assignment_list.html", {"assignments": assignments})


@login_required
def submit_assignment(request, assignment_id):
    if request.user.profile.role != "student":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user.student_profile

    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = student
            submission.save()
            messages.success(request, "Assignment submitted successfully")
            return redirect("student_dashboard")
    else:
        form = SubmissionForm()

    return render(
        request, "submission_form.html", {"form": form, "assignment": assignment}
    )


@login_required
def announcement_create(request):
    if request.user.profile.role not in ["admin", "teacher"]:
        messages.error(request, "Access denied")
        return redirect("dashboard")

    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, "Announcement created successfully")
            return redirect("dashboard")
    else:
        form = AnnouncementForm()

    return render(request, "announcement_form.html", {"form": form})


@login_required
def send_message(request):
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, "Message sent successfully")
            return redirect("dashboard")
    else:
        form = MessageForm()

    return render(request, "message_form.html", {"form": form})


@login_required
def inbox(request):
    received_messages = Message.objects.filter(receiver=request.user).order_by(
        "-sent_at"
    )
    sent_messages = Message.objects.filter(sender=request.user).order_by("-sent_at")

    return render(
        request,
        "inbox.html",
        {"received_messages": received_messages, "sent_messages": sent_messages},
    )


@login_required
def view_child_details(request, student_id):
    if request.user.profile.role != "parent":
        messages.error(request, "Access denied")
        return redirect("dashboard")

    student = get_object_or_404(Student, id=student_id, parent=request.user)
    attendance = Attendance.objects.filter(student=student).order_by("-date")[:20]
    grades = Grade.objects.filter(student=student).order_by("-exam_date")

    context = {"student": student, "attendance": attendance, "grades": grades}
    return render(request, "child_details.html", context)
