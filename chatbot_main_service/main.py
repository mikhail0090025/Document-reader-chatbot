from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from routers.auth_router import router as auth_router
from routers.user_router import router as user_router

from database.base import Base
from database.session import engine

from sqlalchemy import text

app = FastAPI(title="Simple FastAPI App")

# Монтируем папку со статикой (css, js, картинки)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")

app.include_router(auth_router)
app.include_router(user_router)

@app.on_event("startup")
def startup():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Главная страница"}
    )

@app.get("/health")
async def health():
    return {"status": "ok"}