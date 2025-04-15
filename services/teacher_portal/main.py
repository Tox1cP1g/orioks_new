from teaching.routers import homework_router

app = FastAPI()

# Добавляем роутер домашних заданий
app.include_router(homework_router.router)

# Остальные роутеры 