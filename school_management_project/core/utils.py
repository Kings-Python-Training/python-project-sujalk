from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from openpyxl import Workbook
from django.http import HttpResponse


def generate_student_report(student):
    """Generate PDF report for a student"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=30,
        alignment=1,
    )
    elements.append(
        Paragraph(f"Student Report: {student.user.get_full_name()}", title_style)
    )
    elements.append(Spacer(1, 12))

    # Student Info
    info_data = [
        ["Admission Number:", student.admission_number],
        ["Class:", str(student.class_enrolled)],
        ["Roll Number:", str(student.roll_number)],
        ["Parent:", student.parent.get_full_name() if student.parent else "N/A"],
    ]

    info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.grey),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Grades
    elements.append(Paragraph("Academic Performance", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    grades = student.grades.all().order_by("-exam_date")
    if grades:
        grade_data = [["Subject", "Exam Type", "Marks", "Total", "Percentage", "Grade"]]
        for grade in grades:
            grade_data.append(
                [
                    grade.subject.name,
                    grade.exam_type,
                    str(grade.marks_obtained),
                    str(grade.total_marks),
                    f"{grade.percentage()}%",
                    grade.grade_letter(),
                ]
            )

        grade_table = Table(
            grade_data,
            colWidths=[
                1.5 * inch,
                1.2 * inch,
                0.8 * inch,
                0.8 * inch,
                1 * inch,
                0.7 * inch,
            ],
        )
        grade_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(grade_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_class_report(class_obj):
    """Generate Excel report for a class"""
    wb = Workbook()
    ws = wb.active
    ws.title = f"{class_obj.name} - {class_obj.section}"

    # Headers
    headers = ["Roll No", "Name", "Admission No", "Attendance %", "Average Grade"]
    ws.append(headers)

    students = class_obj.students.all()
    for student in students:
        # Calculate attendance percentage
        total_days = student.attendance_records.count()
        present_days = student.attendance_records.filter(status="present").count()
        attendance_pct = (present_days / total_days * 100) if total_days > 0 else 0

        # Calculate average grade
        grades = student.grades.all()
        avg_grade = sum([g.percentage() for g in grades]) / len(grades) if grades else 0

        row = [
            student.roll_number,
            student.user.get_full_name(),
            student.admission_number,
            f"{attendance_pct:.2f}%",
            f"{avg_grade:.2f}%",
        ]
        ws.append(row)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
