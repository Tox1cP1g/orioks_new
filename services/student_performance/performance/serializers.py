from rest_framework import serializers
from .models import Semester, Subject, Grade, Schedule, Attendance, Student

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class GradeSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_type_display = serializers.CharField(source='get_grade_type_display', read_only=True)

    class Meta:
        model = Grade
        fields = ['id', 'student_id', 'subject', 'subject_name', 'grade_type', 
                 'grade_type_display', 'score', 'max_score', 'date', 'comment']

class ScheduleSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    lesson_number_display = serializers.CharField(source='get_lesson_number_display', read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'subject', 'subject_name', 'day_of_week', 'day_of_week_display',
                 'lesson_number', 'lesson_number_display', 'room', 'teacher', 
                 'is_lecture', 'group', 'semester']

class AttendanceSerializer(serializers.ModelSerializer):
    schedule_info = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'student_id', 'schedule_item', 'schedule_info', 
                 'date', 'is_present', 'reason']

    def get_schedule_info(self, obj):
        return f"{obj.schedule_item.subject.name} - {obj.schedule_item.get_day_of_week_display()} - {obj.schedule_item.get_lesson_number_display()}"

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'user_id', 'student_number', 'group', 'faculty']

class StudentGradesSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    subject_name = serializers.CharField()
    total_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    max_possible_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    grades = GradeSerializer(many=True)

class StudentAttendanceSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    subject_name = serializers.CharField()
    total_classes = serializers.IntegerField()
    attended_classes = serializers.IntegerField()
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    attendances = AttendanceSerializer(many=True) 