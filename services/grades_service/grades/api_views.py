from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Student, Subject, Grade, Semester
from .serializers import (
    StudentSerializer, SubjectSerializer, GradeSerializer,
    SemesterSerializer, StudentGradesSerializer
)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def grades(self, request, pk=None):
        student = self.get_object()
        grades = Grade.objects.filter(student=student)
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def current_semester_grades(self, request, pk=None):
        student = self.get_object()
        current_semester = Semester.objects.filter(is_current=True).first()
        if not current_semester:
            return Response({"error": "Текущий семестр не найден"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        grades = Grade.objects.filter(
            student=student,
            subject__semester=current_semester
        )
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def grades(self, request, pk=None):
        subject = self.get_object()
        grades = Grade.objects.filter(subject=subject)
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.username)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        semester = Semester.objects.filter(is_current=True).first()
        if not semester:
            return Response({"error": "Текущий семестр не найден"}, 
                          status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(semester)
        return Response(serializer.data) 