from django.contrib import admin
from .models import (
    Student, Subject, Grade, Schedule,
    Attendance, Semester, HomeworkAssignment,
    HomeworkSubmission, Group, Teacher, SubjectTeacher
)
import requests
from django.contrib import messages

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester', 'credits')
    list_filter = ('semester', 'credits')
    search_fields = ('name', 'code')
    actions = ['import_from_teacher_portal']
    
    def import_from_teacher_portal(self, request, queryset):
        try:
            # Получаем данные из API преподавательского портала
            api_url = 'http://localhost:8004/api/raw-json-api/teachers/'
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Словарь для отслеживания предметов по ID
                processed_subjects = {}
                success_count = 0
                
                for item in data:
                    try:
                        subject_id = item.get('subject_id')
                        subject_name = item.get('subject_name', '')
                        subject_code = item.get('subject_code', '')
                        
                        # Пропускаем, если этот предмет уже обработан или не содержит ID
                        if not subject_id or subject_id in processed_subjects:
                            continue
                            
                        # Запоминаем, что этот предмет уже обработан
                        processed_subjects[subject_id] = True
                        
                        # Поиск или создание предмета по ID
                        subject, created = Subject.objects.update_or_create(
                            id=subject_id,
                            defaults={
                                'name': subject_name,
                                'code': subject_code,
                                # Другие поля можно установить значениями по умолчанию
                                'semester': 1,  # Семестр по умолчанию
                                'credits': 0,   # Кредиты по умолчанию
                                'description': f'Импортировано из API: {subject_name}'
                            }
                        )
                        
                        success_count += 1
                    except Exception as e:
                        # Пропускаем запись при ошибке и продолжаем
                        continue
                
                messages.success(request, f"Успешно импортировано {success_count} предметов из API.")
            else:
                messages.error(request, f"Ошибка API: HTTP {response.status_code}")
        except Exception as e:
            messages.error(request, f"Произошла ошибка при импорте из API: {str(e)}")
    
    import_from_teacher_portal.short_description = "Импортировать предметы из API"

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'subject', 'grade_type', 'score', 'max_score', 'date')
    list_filter = ('grade_type', 'subject', 'date')
    search_fields = ('student_id', 'subject__name')
    date_hierarchy = 'date'

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'get_day_of_week_display', 'get_lesson_number_display', 'room', 'teacher', 'is_lecture', 'group')
    list_filter = ('day_of_week', 'is_lecture', 'semester')
    search_fields = ('subject__name', 'teacher', 'room', 'group')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'schedule_item', 'date', 'is_present')
    list_filter = ('is_present', 'date', 'schedule_item__subject')
    search_fields = ('student_id', 'schedule_item__subject__name')
    date_hierarchy = 'date'

@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'deadline')
    list_filter = ('subject', 'deadline')
    search_fields = ('name', 'description', 'subject__name')
    ordering = ('-deadline',)

@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'submitted_at', 'grade')
    list_filter = ('status', 'submitted_at', 'assignment__subject')
    search_fields = ('student__user_id', 'assignment__name')
    date_hierarchy = 'submitted_at'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'student_number', 'group', 'faculty')
    list_filter = ('group', 'faculty')
    search_fields = ('user_id', 'student_number', 'group__name')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'course')
    list_filter = ('faculty', 'course')
    search_fields = ('name', 'faculty')
    ordering = ('course', 'name')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'last_name', 'first_name', 'department', 'position', 'email')
    list_filter = ('department', 'position', 'academic_degree')
    search_fields = ('user_id', 'last_name', 'first_name', 'department')
    ordering = ('last_name', 'first_name')
    actions = ['import_from_teacher_portal']
    
    def import_from_teacher_portal(self, request, queryset):
        try:
            # Попытаемся получить данные из API преподавательского портала
            api_url = 'http://localhost:8004/api/raw-json-api/teachers/'
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                success_count = 0
                for item in data:
                    try:
                        teacher_id = item.get('teacher_id')
                        
                        # Поиск или создание преподавателя по идентификатору пользователя
                        teacher, created = Teacher.objects.update_or_create(
                            user_id=teacher_id,
                            defaults={
                                'first_name': item.get('teacher_full_name', '').split()[1] if len(item.get('teacher_full_name', '').split()) > 1 else '',
                                'last_name': item.get('teacher_full_name', '').split()[0] if item.get('teacher_full_name', '') else '',
                                'email': '',  # API может не предоставлять email
                                'department': '',  # API может не предоставлять департамент
                                'position': '',  # API может не предоставлять должность
                            }
                        )
                        
                        success_count += 1
                    except Exception as e:
                        # Пропускаем запись при ошибке и продолжаем
                        continue
                        
                messages.success(request, f"Успешно импортировано {success_count} записей преподавателей из API.")
            else:
                messages.error(request, f"Ошибка API: HTTP {response.status_code}")
        except Exception as e:
            messages.error(request, f"Произошла ошибка при импорте из API: {str(e)}")
    
    import_from_teacher_portal.short_description = "Импортировать преподавателей из API"

@admin.register(SubjectTeacher)
class SubjectTeacherAdmin(admin.ModelAdmin):
    list_display = ('subject', 'teacher', 'role', 'is_main')
    list_filter = ('role', 'is_main', 'subject')
    search_fields = ('subject__name', 'teacher__last_name', 'teacher__first_name')
    ordering = ('subject', '-is_main', 'role')
    actions = ['import_from_teacher_portal']
    
    def import_from_teacher_portal(self, request, queryset):
        try:
            # Получаем данные из API преподавательского портала
            api_url = 'http://localhost:8004/api/raw-json-api/teachers/'
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                success_count = 0
                for item in data:
                    try:
                        teacher_id = item.get('teacher_id')
                        subject_id = item.get('subject_id')
                        
                        # Проверяем, существуют ли преподаватель и предмет
                        try:
                            teacher = Teacher.objects.get(user_id=teacher_id)
                        except Teacher.DoesNotExist:
                            # Если преподавателя нет, создаем его с минимальной информацией
                            teacher = Teacher.objects.create(
                                user_id=teacher_id,
                                first_name=item.get('teacher_full_name', '').split()[1] if len(item.get('teacher_full_name', '').split()) > 1 else '',
                                last_name=item.get('teacher_full_name', '').split()[0] if item.get('teacher_full_name', '') else ''
                            )
                        
                        try:
                            subject = Subject.objects.get(id=subject_id)
                        except Subject.DoesNotExist:
                            # Если предмета нет, пропускаем эту связь
                            continue
                        
                        # Определяем роль преподавателя
                        role = item.get('role', 'LECTURER')
                        is_main = item.get('is_main', False)
                        
                        # Создаем или обновляем связь
                        relation, created = SubjectTeacher.objects.update_or_create(
                            subject=subject,
                            teacher=teacher,
                            defaults={
                                'role': role,
                                'is_main': is_main
                            }
                        )
                        
                        success_count += 1
                    except Exception as e:
                        # Пропускаем запись при ошибке и продолжаем
                        continue
                
                messages.success(request, f"Успешно импортировано {success_count} связей преподавателей с предметами из API.")
            else:
                messages.error(request, f"Ошибка API: HTTP {response.status_code}")
        except Exception as e:
            messages.error(request, f"Произошла ошибка при импорте из API: {str(e)}")
    
    import_from_teacher_portal.short_description = "Импортировать связи преподаватель-предмет из API" 