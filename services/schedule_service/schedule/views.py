from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Schedule, Group
from .forms import ScheduleForm
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import connections

logger = logging.getLogger(__name__)

def get_groups_from_main_db():
    with connections['default'].cursor() as cursor:
        # Проверяем все таблицы в базе данных
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'student_performance'
        """)
        tables = cursor.fetchall()
        logger.info(f"Все таблицы в базе данных: {tables}")

        # Проверяем таблицу auth_group
        cursor.execute("""
            SELECT name 
            FROM auth_group 
            ORDER BY name
        """)
        groups = [row[0] for row in cursor.fetchall()]
        logger.info(f"Группы из auth_group: {groups}")

        if not groups:
            # Проверяем таблицу student_group
            cursor.execute("""
                SELECT name 
                FROM student_group 
                ORDER BY name
            """)
            groups = [row[0] for row in cursor.fetchall()]
            logger.info(f"Группы из student_group: {groups}")

        if not groups:
            # Проверяем таблицу student_performance_student
            cursor.execute("""
                SELECT DISTINCT `group` 
                FROM student_performance_student 
                WHERE `group` IS NOT NULL
                ORDER BY `group`
            """)
            groups = [row[0] for row in cursor.fetchall()]
            logger.info(f"Группы из student_performance_student: {groups}")

        return groups or []  # Возвращаем пустой список, если группы не найдены

def get_or_create_group(request):
    group_name = request.GET.get('name')
    if not group_name:
        return JsonResponse({'error': 'Group name is required'}, status=400)
    
    group, created = Group.objects.get_or_create(name=group_name)
    return JsonResponse({
        'id': group.id,
        'name': group.name,
        'created': created
    })

def import_schedule_from_main_db(group, semester):
    # Маппинг числовых дней недели в строковые
    day_mapping = {
        1: 'monday',
        2: 'tuesday',
        3: 'wednesday',
        4: 'thursday',
        5: 'friday',
        6: 'saturday',
        7: 'sunday'
    }

    with connections['default'].cursor() as cursor:
        # Проверяем семестры
        cursor.execute("""
            SELECT id, name, is_current
            FROM performance_semester
            ORDER BY name
        """)
        semesters = cursor.fetchall()
        logger.info(f"Доступные семестры: {semesters}")

        # Проверяем расписание для всех семестров
        cursor.execute("""
            SELECT s.id, s.day_of_week, s.lesson_number, s.teacher, s.room, s.group, 
                   subj.name as subject, sem.name as semester, sem.id as semester_id
            FROM performance_schedule s
            JOIN performance_subject subj ON s.subject_id = subj.id
            JOIN performance_semester sem ON s.semester_id = sem.id
            WHERE s.group = %s
            ORDER BY sem.id, s.day_of_week, s.lesson_number
            LIMIT 5
        """, [group])
        
        sample_schedules = cursor.fetchall()
        logger.info(f"Примеры расписания: {sample_schedules}")

        # Определяем ID семестра для поиска
        target_semester_id = None
        if semester:
            # Если указан конкретный семестр, проверяем его существование
            cursor.execute("""
                SELECT id, name
                FROM performance_semester
                WHERE id = %s
            """, [semester])
            semester_record = cursor.fetchone()
            if semester_record:
                target_semester_id = str(semester_record[0])
                logger.info(f"Найден указанный семестр: {semester_record[1]} (ID: {target_semester_id})")
            else:
                logger.info(f"Указанный семестр {semester} не найден, ищем альтернативы")

        if not target_semester_id and sample_schedules:
            # Если семестр не найден и есть расписание, берем семестр из первого найденного расписания
            target_semester_id = str(sample_schedules[0][8])
            logger.info(f"Используем семестр из существующего расписания: {target_semester_id}")
        
        if not target_semester_id:
            # Если всё еще нет семестра, берем текущий или первый доступный
            current_semester = next((s for s in semesters if s[2] == 1), None)
            if current_semester:
                target_semester_id = str(current_semester[0])
                logger.info(f"Используем текущий семестр: {current_semester[1]} (ID: {target_semester_id})")
            elif semesters:
                target_semester_id = str(semesters[0][0])
                logger.info(f"Используем первый доступный семестр: {semesters[0][1]} (ID: {target_semester_id})")

        if not target_semester_id:
            logger.error("Не удалось определить семестр")
            return False

        logger.info(f"Использую семестр с ID: {target_semester_id}")

        # Получаем расписание для выбранного семестра
        cursor.execute("""
            SELECT s.id, s.day_of_week, s.lesson_number, s.teacher, s.room, s.group, 
                   subj.name as subject, sem.name as semester
            FROM performance_schedule s
            JOIN performance_subject subj ON s.subject_id = subj.id
            JOIN performance_semester sem ON s.semester_id = sem.id
            WHERE s.group = %s AND sem.id = %s
            ORDER BY s.day_of_week, s.lesson_number
        """, [group, target_semester_id])
        
        schedules = cursor.fetchall()
        logger.info(f"Найдено {len(schedules)} занятий в основной базе для группы {group} (ID семестра: {target_semester_id})")
        
        if schedules:
            # Очищаем существующее расписание для этой группы и семестра
            cursor.execute("""
                DELETE FROM schedule_schedule 
                WHERE group_id = %s AND semester = %s
            """, [group, target_semester_id])
            
            # Импортируем новое расписание
            for schedule in schedules:
                # Конвертируем числовой день недели в строковый
                day_of_week = day_mapping.get(schedule[1], 'monday')  # По умолчанию monday, если день не найден
                
                cursor.execute("""
                    INSERT INTO schedule_schedule 
                    (day_of_week, lesson_number, subject, teacher, room, group_id, semester, is_lecture, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, [
                    day_of_week,  # day_of_week (строкой)
                    schedule[2],  # lesson_number
                    schedule[6],  # subject
                    schedule[3],  # teacher
                    schedule[4],  # room
                    schedule[5],  # group_name
                    target_semester_id,  # semester
                    False        # is_lecture
                ])
            
            logger.info(f"Импортировано {len(schedules)} занятий для группы {group}")
            return True
    return False

def schedule_list(request):
    # Получаем параметры фильтрации из URL
    semester = request.GET.get('semester', '')
    group = request.GET.get('group', '')
    source = request.GET.get('source', '')
    role = request.GET.get('role', '')
    week = request.GET.get('week')

    logger.info(f"Получены параметры: semester={semester}, group={group}, source={source}, role={role}")

    # Определяем текущую неделю
    today = timezone.now().date()
    if week:
        week_start = datetime.strptime(week, '%Y-%m-%d').date()
    else:
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    # Создаем список дней недели
    days = [week_start + timedelta(days=i) for i in range(7)]

    # Определяем временные слоты
    time_slots = [
        {'number': 1, 'time': '09:00 - 10:30'},
        {'number': 2, 'time': '10:40 - 12:10'},
        {'number': 3, 'time': '12:20 - 13:50'},
        {'number': 4, 'time': '14:30 - 16:00'},
        {'number': 5, 'time': '16:10 - 17:40'},
        {'number': 6, 'time': '17:50 - 19:20'},
        {'number': 7, 'time': '19:30 - 21:00'},
    ]

    try:
        with connections['default'].cursor() as cursor:
            # Получаем группы
            cursor.execute("""
                SELECT DISTINCT name 
                FROM auth_group 
                ORDER BY name
            """)
            groups = [row[0] for row in cursor.fetchall()]
            logger.info(f"Найдены группы: {groups}")
            
            if not group and groups:
                group = groups[0]
                logger.info(f"Выбрана группа по умолчанию: {group}")

            if group:
                # Пытаемся импортировать расписание из основной базы
                imported = import_schedule_from_main_db(group, semester)
                if imported:
                    logger.info(f"Расписание успешно импортировано для группы {group}")

                # Если семестр не указан, проверяем, есть ли расписание в каком-либо семестре
                if not semester:
                    cursor.execute("""
                        SELECT DISTINCT semester 
                        FROM schedule_schedule 
                        WHERE group_id = %s 
                        ORDER BY semester DESC 
                        LIMIT 1
                    """, [group])
                    result = cursor.fetchone()
                    if result:
                        semester = str(result[0])
                        logger.info(f"Использую семестр из существующего расписания: {semester}")
                    else:
                        # Если расписания нет, используем текущий семестр
                        cursor.execute("""
                            SELECT id
                            FROM performance_semester
                            WHERE is_current = 1
                            LIMIT 1
                        """)
                        current_semester = cursor.fetchone()
                        if current_semester:
                            semester = str(current_semester[0])
                            logger.info(f"Использую текущий семестр из базы: {semester}")

            # Получаем расписание
            filter_kwargs = {'group__name': group}
            if semester:
                filter_kwargs['semester'] = semester
            
            schedules = Schedule.objects.filter(
                **filter_kwargs
            ).select_related('group').order_by('day_of_week', 'lesson_number')
            
            logger.info(f"Загружено расписаний: {schedules.count()}")
            for schedule in schedules:
                logger.info(f"Занятие: {schedule.subject} ({schedule.day_of_week}, пара {schedule.lesson_number})")

    except Exception as e:
        logger.error(f"Ошибка при работе с базой данных: {str(e)}")
        groups = []
        schedules = Schedule.objects.none()

    # Подготавливаем данные для отображения
    schedule_data = []
    schedules_dict = {}
    for schedule in schedules:
        key = (schedule.day_of_week, schedule.lesson_number)
        if key not in schedules_dict:
            schedules_dict[key] = []
        schedules_dict[key].append(schedule)

    for slot in time_slots:
        slot_data = {
            'time': slot['time'],
            'days': []
        }
        for day in days:
            day_name = day.strftime('%A').lower()
            key = (day_name, slot['number'])
            slot_data['days'].append({
                'date': day,
                'lessons': schedules_dict.get(key, [])
            })
        schedule_data.append(slot_data)

    context = {
        'schedules': schedules,
        'semester': semester,
        'groups': groups,
        'selected_group': group,
        'is_teacher': role == 'TEACHER',
        'source': source,
        'schedule_data': schedule_data,
        'days': days,
        'week_start': week_start,
        'week_end': week_end,
        'prev_week': prev_week,
        'next_week': next_week,
        'today': today,
        'current_semester': semester
    }
    return render(request, 'schedule/schedule_list.html', context)

def schedule_detail(request, schedule_id):
    source = request.GET.get('source', '')
    role = request.GET.get('role', '')
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    return render(request, 'schedule/schedule_detail.html', {
        'schedule': schedule,
        'source': source,
        'role': role,
        'is_teacher': role == 'TEACHER',
    })

def add_schedule(request):
    role = request.GET.get('role', '')
    if role != 'TEACHER':
        messages.error(request, 'У вас нет прав для добавления расписания')
        return redirect('schedule_list')

    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Расписание успешно добавлено')
            return redirect('schedule_list')
    else:
        form = ScheduleForm()

    context = {
        'form': form,
        'title': 'Добавление занятия',
        'role': role
    }
    return render(request, 'schedule/schedule_form.html', context)

def edit_schedule(request, pk):
    role = request.GET.get('role', '')
    if role != 'TEACHER':
        messages.error(request, 'У вас нет прав для редактирования расписания')
        return redirect('schedule_list')

    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Расписание успешно обновлено')
            return redirect('schedule_list')
    else:
        form = ScheduleForm(instance=schedule)

    context = {
        'form': form,
        'schedule': schedule,
        'title': 'Редактирование занятия',
        'role': role
    }
    return render(request, 'schedule/schedule_form.html', context)

def delete_schedule(request, pk):
    role = request.GET.get('role', '')
    if role != 'TEACHER':
        messages.error(request, 'У вас нет прав для удаления расписания')
        return redirect('schedule_list')

    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Расписание успешно удалено')
        return redirect('schedule_list')

    context = {
        'schedule': schedule,
        'role': role
    }
    return render(request, 'schedule/schedule_confirm_delete.html', context) 