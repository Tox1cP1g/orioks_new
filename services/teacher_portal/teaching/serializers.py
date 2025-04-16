from rest_framework import serializers
from .models import Teacher, Course, LearningMaterial, Assignment, GradingCriteria, StudentSubmission, Grade, Subject, StudentAssignment, Schedule, Attendance, SubjectTeacher
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['id', 'user', 'department', 'position', 'academic_degree', 'phone', 'office_hours', 'full_name']
        
    def get_full_name(self, obj):
        return obj.user.get_full_name()

class TeacherBasicSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для модели Teacher"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['id', 'full_name', 'position', 'academic_degree']
        
    def get_full_name(self, obj):
        return obj.user.get_full_name()

class CourseSerializer(serializers.ModelSerializer):
    teachers = TeacherSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'teachers', 'semester', 'created_at', 'updated_at']

class LearningMaterialSerializer(serializers.ModelSerializer):
    created_by = TeacherSerializer(read_only=True)
    
    class Meta:
        model = LearningMaterial
        fields = ['id', 'course', 'title', 'type', 'content', 'file', 'created_by', 'created_at', 'updated_at']

class GradingCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingCriteria
        fields = ['id', 'assignment', 'description', 'max_score']

class AssignmentSerializer(serializers.ModelSerializer):
    created_by = TeacherSerializer(read_only=True)
    criteria = GradingCriteriaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Assignment
        fields = ['id', 'course', 'created_by', 'title', 'description', 'type', 'max_score', 
                 'deadline', 'created_at', 'updated_at', 'criteria']

class StudentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentSubmission
        fields = ['id', 'assignment', 'student_id', 'status', 'submission_text', 
                 'files', 'submitted_at']

class GradeSerializer(serializers.ModelSerializer):
    graded_by = TeacherSerializer(read_only=True)
    submission = StudentSubmissionSerializer(read_only=True)
    
    class Meta:
        model = Grade
        fields = ['id', 'submission', 'graded_by', 'score', 'feedback', 'graded_at']

class SubjectTeacherSerializer(serializers.ModelSerializer):
    """Сериализатор для связи преподавателей с предметами"""
    teacher = TeacherBasicSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(),
        source='teacher',
        write_only=True
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        source='subject',
        write_only=True
    )
    subject_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = SubjectTeacher
        fields = [
            'id', 'subject', 'subject_id', 'subject_name', 
            'teacher', 'teacher_id', 'role', 'role_display', 
            'is_main', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        
    def get_subject_name(self, obj):
        return obj.subject.name

class SubjectSerializer(serializers.ModelSerializer):
    """Сериализатор для предметов"""
    teacher_name = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()
    teachers = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'description', 'teacher', 
            'teacher_name', 'semester', 'students_count', 
            'created_at', 'updated_at', 'teachers'
        ]
        read_only_fields = ['teacher', 'teacher_name', 'students_count', 'teachers']

    def get_teacher_name(self, obj):
        return obj.teacher.user.get_full_name()

    def get_students_count(self, obj):
        # MySQL не поддерживает distinct с параметром поля
        students = StudentAssignment.objects.filter(
            assignment__course__teachers=obj.teacher
        ).values_list('student_id', flat=True)
        return len(set(students))  # Используем set для удаления дубликатов
        
    def get_teachers(self, obj):
        """Получает всех преподавателей предмета через связи"""
        subject_teachers = SubjectTeacher.objects.filter(subject=obj)
        return SubjectTeacherSerializer(subject_teachers, many=True).data

class ScheduleSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    lesson_number_display = serializers.CharField(source='get_lesson_number_display', read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id', 'subject', 'subject_name', 'teacher', 'teacher_name',
            'day_of_week', 'day_of_week_display', 'lesson_number',
            'lesson_number_display', 'room', 'is_active'
        ]
        read_only_fields = ['teacher', 'teacher_name', 'subject_name', 'day_of_week_display', 'lesson_number_display']

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    schedule_info = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'schedule_item', 'schedule_info', 'student', 'student_name', 'date', 'is_present', 'note']
        read_only_fields = ['schedule_info']

    def get_schedule_info(self, obj):
        return {
            'subject': obj.schedule_item.subject.name,
            'day_of_week': obj.schedule_item.get_day_of_week_display(),
            'lesson_number': obj.schedule_item.get_lesson_number_display(),
            'room': obj.schedule_item.room
        }

class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
        read_only_fields = ['username', 'full_name', 'email'] 