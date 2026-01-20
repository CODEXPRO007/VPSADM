from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from database import SessionLocal, engine
from models import Base, Paste
from datetime import datetime, timedelta
import secrets

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_expiry(val):
    if val == "10m": return datetime.utcnow() + timedelta(minutes=10)
    if val == "1h": return datetime.utcnow() + timedelta(hours=1)
    if val == "1d": return datetime.utcnow() + timedelta(days=1)
    return None

@app.get("/", response_class=HTMLResponse)
def home(req: Request):
    return templates.TemplateResponse("index.html", {"request": req})

@app.post("/create")
def create_paste(
    content: str = Form(...),
    language: str = Form("text"),
    password: str = Form(None),
    expire: str = Form("never")
):
    db = SessionLocal()
    pid = secrets.token_hex(4)

    paste = Paste(
        paste_id=pid,
        content=content,
        language=language,
        password=password or None,
        expire_at=get_expiry(expire)
    )
    db.add(paste)
    db.commit()

    return {
        "url": f"/{pid}",
        "raw": f"/raw/{pid}"
    }

@app.get("/{pid}", response_class=HTMLResponse)
def view_paste(req: Request, pid: str):
    db = SessionLocal()
    paste = db.query(Paste).filter_by(paste_id=pid).first()
    if not paste:
        raise HTTPException(404)

    if paste.expire_at and paste.expire_at < datetime.utcnow():
        raise HTTPException(410, "Expired")

    return templates.TemplateResponse(
        "view.html",
        {"request": req, "paste": paste}
    )

@app.post("/raw/{pid}", response_class=PlainTextResponse)
def raw(pid: str, password: str = Form(None)):
    db = SessionLocal()
    paste = db.query(Paste).filter_by(paste_id=pid).first()

    if not paste:
        raise HTTPException(404)

    if paste.expire_at and paste.expire_at < datetime.utcnow():
        raise HTTPException(410)

    if paste.password and paste.password != password:
        raise HTTPException(403, "Wrong password")

    return paste.content