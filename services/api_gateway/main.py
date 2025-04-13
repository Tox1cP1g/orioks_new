from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ОРИОКС API Gateway")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация сервисов
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8002")
PERFORMANCE_SERVICE_URL = os.getenv("PERFORMANCE_SERVICE_URL", "http://localhost:8003")
TEACHER_SERVICE_URL = os.getenv("TEACHER_SERVICE_URL", "http://localhost:8004")

async def get_token_header(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return authorization

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Маршруты аутентификации
@app.post("/api/auth/token")
async def login(username: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/api/token/",
            data={"username": username, "password": password}
        )
        return response.json()

@app.post("/api/auth/register")
async def register(user_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/api/register/",
            json=user_data
        )
        return response.json()

# Маршруты успеваемости
@app.get("/api/performance/students/{student_id}")
async def get_student_performance(
    student_id: int,
    token: str = Depends(get_token_header)
):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PERFORMANCE_SERVICE_URL}/api/students/{student_id}/performance/",
            headers={"Authorization": token}
        )
        return response.json()

@app.get("/api/performance/students/{student_id}/statistics")
async def get_student_statistics(
    student_id: int,
    semester: Optional[int] = None,
    year: Optional[int] = None,
    token: str = Depends(get_token_header)
):
    params = {}
    if semester:
        params["semester"] = semester
    if year:
        params["year"] = year

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PERFORMANCE_SERVICE_URL}/api/students/{student_id}/statistics/",
            params=params,
            headers={"Authorization": token}
        )
        return response.json()

@app.get("/api/performance/courses")
async def get_courses(token: str = Depends(get_token_header)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PERFORMANCE_SERVICE_URL}/api/courses/",
            headers={"Authorization": token}
        )
        return response.json()

@app.get("/api/performance/grades")
async def get_grades(
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    grade_type: Optional[str] = None,
    token: str = Depends(get_token_header)
):
    params = {}
    if student_id:
        params["student"] = student_id
    if course_id:
        params["course"] = course_id
    if grade_type:
        params["type"] = grade_type

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PERFORMANCE_SERVICE_URL}/api/grades/",
            params=params,
            headers={"Authorization": token}
        )
        return response.json()

# Маршруты портала преподавателя
@app.get("/api/teacher/subjects")
async def get_teacher_subjects(token: str = Depends(get_token_header)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TEACHER_SERVICE_URL}/api/subjects/",
            headers={"Authorization": token}
        )
        return response.json()

@app.get("/api/teacher/schedule")
async def get_teacher_schedule(token: str = Depends(get_token_header)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TEACHER_SERVICE_URL}/api/schedule/",
            headers={"Authorization": token}
        )
        return response.json()

@app.get("/api/teacher/attendance")
async def get_teacher_attendance(token: str = Depends(get_token_header)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TEACHER_SERVICE_URL}/api/attendance/",
            headers={"Authorization": token}
        )
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 