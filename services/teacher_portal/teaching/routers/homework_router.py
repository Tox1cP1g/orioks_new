from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models import HomeworkSubmission
from django.core.exceptions import ObjectDoesNotExist

router = APIRouter(prefix="/api/homework", tags=["homework"])

class HomeworkNotification(BaseModel):
    submission_id: int
    student_name: str
    assignment_name: str
    subject_name: str

class GradeSubmission(BaseModel):
    grade: float
    feedback: Optional[str] = None

@router.post("/notify")
async def receive_homework(notification: HomeworkNotification):
    try:
        # Создаем или обновляем запись о домашнем задании
        submission, created = HomeworkSubmission.objects.get_or_create(
            submission_id=notification.submission_id,
            defaults={
                'student_name': notification.student_name,
                'assignment_name': notification.assignment_name,
                'subject_name': notification.subject_name,
                'status': 'SUBMITTED'
            }
        )
        
        if not created:
            # Если запись уже существует, обновляем её
            submission.student_name = notification.student_name
            submission.assignment_name = notification.assignment_name
            submission.subject_name = notification.subject_name
            submission.save()
        
        return {"status": "ok", "message": "Homework notification received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions")
async def list_submissions():
    try:
        submissions = HomeworkSubmission.objects.all().order_by('-received_at')
        return [{
            'id': sub.id,
            'submission_id': sub.submission_id,
            'student_name': sub.student_name,
            'assignment_name': sub.assignment_name,
            'subject_name': sub.subject_name,
            'received_at': sub.received_at.isoformat(),
            'status': sub.status,
            'grade': float(sub.grade) if sub.grade else None,
            'feedback': sub.feedback,
            'graded_at': sub.graded_at.isoformat() if sub.graded_at else None
        } for sub in submissions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submissions/{submission_id}/grade")
async def grade_submission(submission_id: int, grade_data: GradeSubmission):
    try:
        submission = HomeworkSubmission.objects.get(submission_id=submission_id)
        submission.grade = grade_data.grade
        submission.feedback = grade_data.feedback
        submission.status = 'GRADED'
        submission.save()
        return {"status": "ok", "message": "Submission graded successfully"}
    except ObjectDoesNotExist:
        raise HTTPException(status_code=404, detail="Submission not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 