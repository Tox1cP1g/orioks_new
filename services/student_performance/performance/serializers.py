from rest_framework import serializers
from .models import (
    Semester, Subject, Grade, Schedule, Attendance, 
    Student, Group, Teacher, SubjectTeacher
)

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current']

class TeacherSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Teacher"""
    class Meta:
        model = Teacher
        fields = ['id', 'user_id', 'first_name', 'last_name', 'middle_name', 
                  'academic_degree', 'academic_title', 'department', 'position', 'email']

class TeacherBasicSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['id', 'user_id', 'full_name', 'position', 'department']
        
    def get_full_name(self, obj):
        if obj.middle_name:
            return f"{obj.last_name} {obj.first_name} {obj.middle_name}"
        return f"{obj.last_name} {obj.first_name}"

class SubjectTeacherSerializer(serializers.ModelSerializer):
    """Сериализатор для модели SubjectTeacher (связи преподавателей с предметами)"""
    teacher_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SubjectTeacher
        fields = ['id', 'subject', 'teacher', 'role', 'is_main', 'teacher_name', 'subject_name']
    
    def get_teacher_name(self, obj):
        """Возвращает полное имя преподавателя"""
        return f"{obj.teacher.last_name} {obj.teacher.first_name} {obj.teacher.middle_name or ''}".strip()
    
    def get_subject_name(self, obj):
        """Возвращает название предмета"""
        return obj.subject.name

class SubjectSerializer(serializers.ModelSerializer):
    teachers = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'semester', 'credits', 'description', 'teachers']
        
    def get_teachers(self, obj):
        subject_teachers = SubjectTeacher.objects.filter(subject=obj).order_by('-is_main', 'role')
        return SubjectTeacherSerializer(subject_teachers, many=True).data

class SubjectBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'credits']

class GradeSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Grade
        fields = ['id', 'student_id', 'subject', 'subject_name', 'grade_type', 
                 'score', 'max_score', 'date', 'comment']

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
    schedule_detail = ScheduleSerializer(source='schedule_item', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'student_id', 'schedule_item', 'schedule_detail', 
                 'date', 'is_present', 'reason']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'faculty', 'course']

class StudentSerializer(serializers.ModelSerializer):
    group_details = GroupSerializer(source='group', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'user_id', 'student_number', 'group', 'group_details', 'faculty']

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