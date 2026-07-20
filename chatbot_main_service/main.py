print("1")
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
print("2")
from routers.document_router import router as document_router
from routers.chat_router import router as chat_router
print("3")

app = FastAPI(title="Simple FastAPI App")

# Монтируем папку со статикой (css, js, картинки)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")

app.include_router(document_router)
app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Главная страница"}
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
