from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from sqlalchemy import text

app = FastAPI(title="Simple FastAPI App")

# Монтируем папку со статикой (css, js, картинки)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Главная страница"}
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
