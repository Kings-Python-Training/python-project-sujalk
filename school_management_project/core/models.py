from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("teacher", "Teacher"),
        ("student", "Student"),
        ("parent", "Parent"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"


class Class(models.Model):
    name = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    class_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="class_teacher_of",
        limit_choices_to={"profile__role": "teacher"},
    )
    academic_year = models.CharField(max_length=20, default="2024-2025")

    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ["name", "section", "academic_year"]

    def __str__(self):
        return f"{self.name} - {self.section}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class ClassSubject(models.Model):
    class_obj = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="subjects"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="teaching_subjects",
        limit_choices_to={"profile__role": "teacher"},
    )

    class Meta:
        unique_together = ["class_obj", "subject"]

    def __str__(self):
        return f"{self.class_obj} - {self.subject}"


class Student(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    admission_number = models.CharField(max_length=20, unique=True)
    class_enrolled = models.ForeignKey(
        Class, on_delete=models.SET_NULL, null=True, related_name="students"
    )
    roll_number = models.IntegerField()
    parent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="children",
        limit_choices_to={"profile__role": "parent"},
    )
    admission_date = models.DateField()

    class Meta:
        unique_together = ["class_enrolled", "roll_number"]

    def __str__(self):
        return f"{self.admission_number} - {self.user.get_full_name()}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ["student", "date"]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class Grade(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="grades"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=50)
    marks_obtained = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    total_marks = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )
    exam_date = models.DateField()
    remarks = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def percentage(self):
        if self.total_marks > 0:
            return round((self.marks_obtained / self.total_marks) * 100, 2)
        return 0

    def grade_letter(self):
        pct = self.percentage()
        if pct >= 90:
            return "A+"
        elif pct >= 80:
            return "A"
        elif pct >= 70:
            return "B"
        elif pct >= 60:
            return "C"
        elif pct >= 50:
            return "D"
        else:
            return "F"

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam_type}"


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    class_subject = models.ForeignKey(
        ClassSubject, on_delete=models.CASCADE, related_name="assignments"
    )
    due_date = models.DateTimeField()
    total_marks = models.IntegerField(validators=[MinValueValidator(0)])
    attachment = models.FileField(upload_to="assignments/", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.class_subject}"


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="submissions"
    )
    submission_file = models.FileField(upload_to="submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    marks_obtained = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_submissions",
    )

    class Meta:
        unique_together = ["assignment", "student"]

    def __str__(self):
        return f"{self.student} - {self.assignment.title}"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    target_role = models.CharField(
        max_length=10, choices=UserProfile.ROLE_CHOICES, blank=True
    )
    target_class = models.ForeignKey(
        Class, on_delete=models.CASCADE, null=True, blank=True
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    subject = models.CharField(max_length=200)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.sender} to {self.receiver} - {self.subject}"
