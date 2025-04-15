from rest_framework import serializers
from .models import Student, Subject, Grade, Semester, Group, Teacher

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'department']

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'user_id', 'first_name', 'last_name', 'email', 'department', 'position']

class SubjectSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    
    class Meta:
        model = Subject
        fields = ['id', 'name', 'semester', 'description', 'teacher', 'created_at', 'updated_at']

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current', 'created_at', 'updated_at']

class StudentSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'user_id', 'first_name', 'last_name', 'email', 'group', 'created_at', 'updated_at']

class GradeSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'subject', 'grade_type', 'score', 
            'max_score', 'date', 'comment', 'created_by', 
            'created_at', 'updated_at'
        ]

class StudentGradesSerializer(serializers.Serializer):
    student = StudentSerializer()
    grades = GradeSerializer(many=True)
    current_semester = SemesterSerializer() 