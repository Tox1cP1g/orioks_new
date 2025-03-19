from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models import HomeworkSubmission, Teacher
from ..dependencies import get_current_teacher

router = APIRouter(prefix="/api/homework", tags=["homework"])

class HomeworkNotification(BaseModel):
    submission_id: int
    student_name: str
    assignment_name: str
    subject_name: str

@router.post("/notify")
async def notify_homework_submission(
    notification: HomeworkNotification,
    teacher: Teacher = Depends(get_current_teacher)
):
    try:
        # Создаем запись о новом домашнем задании
        submission = HomeworkSubmission(
            submission_id=notification.submission_id,
            student_name=notification.student_name,
            assignment_name=notification.assignment_name,
            subject_name=notification.subject_name,
            received_at=datetime.now(),
            status="RECEIVED"
        )
        
        # Сохраняем в базу данных
        await submission.save()

        # В будущем здесь можно добавить отправку уведомления преподавателю
        # через WebSocket или другой механизм

        return {"status": "success", "message": "Notification received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions")
async def get_homework_submissions(
    teacher: Teacher = Depends(get_current_teacher),
    status: Optional[str] = None
):
    try:
        query = HomeworkSubmission.objects
        if status:
            query = query.filter(status=status)
        
        submissions = await query.order_by("-received_at").all()
        return submissions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/grade/{submission_id}")
async def grade_homework(
    submission_id: int,
    grade: float,
    feedback: Optional[str] = None,
    teacher: Teacher = Depends(get_current_teacher)
):
    try:
        submission = await HomeworkSubmission.objects.get(submission_id=submission_id)
        submission.grade = grade
        submission.feedback = feedback
        submission.status = "GRADED"
        submission.graded_at = datetime.now()
        await submission.save()

        # Отправляем оценку обратно в сервис студента
        # Здесь должен быть код для отправки оценки через API

        return {"status": "success", "message": "Homework graded successfully"}
    except HomeworkSubmission.DoesNotExist:
        raise HTTPException(status_code=404, detail="Submission not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 