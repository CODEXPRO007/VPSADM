from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from database import SessionLocal, engine
from models import Base, Paste
from datetime import datetime, timedelta
import secrets

DOMAIN = "https://vpsadm.onrender.com"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pastebin Clone")
templates = Jinja2Templates(directory="templates")

def get_expiry(value: str):
    if value == "10m":
        return datetime.utcnow() + timedelta(minutes=10)
    if value == "1h":
        return datetime.utcnow() + timedelta(hours=1)
    if value == "1d":
        return datetime.utcnow() + timedelta(days=1)
    return None

# 🌐 HOME
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 📤 CREATE PASTE (API + WEB)
@app.post("/api/create")
def create_paste(
    content: str = Form(...),
    language: str = Form("text"),
    expire: str = Form("never"),
    password: str = Form(None)
):
    if len(content) > 500000:
        raise HTTPException(413, "Paste too large")

    db = SessionLocal()
    pid = secrets.token_hex(3)  # short unique id

    paste = Paste(
        paste_id=pid,
        content=content,
        language=language,
        password=password or None,
        expire_at=get_expiry(expire)
    )
    db.add(paste)
    db.commit()
    db.close()

    return {
        "paste": f"{DOMAIN}/{pid}",
        "raw": f"{DOMAIN}/raw/{pid}"
    }

# 📄 RAW VIEW
@app.get("/raw/{pid}", response_class=PlainTextResponse)
def raw_paste(pid: str):
    db = SessionLocal()
    paste = db.query(Paste).filter(Paste.paste_id == pid).first()
    db.close()

    if not paste:
        raise HTTPException(404, "Paste not found")

    if paste.expire_at and paste.expire_at < datetime.utcnow():
        raise HTTPException(410, "Paste expired")

    return paste.content

# 👁️ VIEW PASTE (IMPORTANT: KEEP LAST)
@app.get("/{pid}", response_class=HTMLResponse)
def view_paste(request: Request, pid: str):
    db = SessionLocal()
    paste = db.query(Paste).filter(Paste.paste_id == pid).first()
    db.close()

    if not paste:
        raise HTTPException(404, "Paste not found")

    if paste.expire_at and paste.expire_at < datetime.utcnow():
        raise HTTPException(410, "Paste expired")

    return templates.TemplateResponse(
        "view.html",
        {"request": request, "paste": paste}
    )
