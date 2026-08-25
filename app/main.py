from pathlib import Path
import csv, re
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, engine, get_db, SessionLocal
from .models import User, Review, Finding, HistoricalRule
from .security import hash_password, verify_password
from .reviewer import analyze, quality_score, summarize, normalize_language

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Intelligent Code Reviewer", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key="replace-in-production")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
Base.metadata.create_all(bind=engine)

def current_user(request: Request, db: Session):
    uid = request.session.get("user_id")
    return db.get(User, uid) if uid else None

def seed():
    db = SessionLocal()
    try:
        if not db.execute(select(HistoricalRule)).first():
            csv_path = BASE_DIR.parent / "data" / "historical_reviews.csv"
            with open(csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    db.add(HistoricalRule(rule_type=row["type"], description=row["description"]))
        if not db.execute(select(User).where(User.email == "demo@example.com")).scalar_one_or_none():
            db.add(User(email="demo@example.com", password_hash=hash_password("Demo@123")))
        db.commit()
    finally:
        db.close()
seed()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == email.lower().strip())).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)

@app.post("/register")
def register(email: str = Form(...), password: str = Form(...), request: Request = None, db: Session = Depends(get_db)):
    email = email.lower().strip()
    if len(password) < 8:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Password must be at least 8 characters"})
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
        return templates.TemplateResponse("login.html", {"request": request, "error": "Account already exists"})
    user = User(email=email, password_hash=hash_password(password))
    db.add(user); db.commit(); db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.post("/api/reviews")
async def create_review(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        raise HTTPException(401, "Authentication required")
    payload = await request.json()
    source = str(payload.get("source_code", ""))
    language = normalize_language(str(payload.get("language", "python")))
    filename = str(payload.get("filename", "submission"))
    if not source.strip():
        raise HTTPException(400, "Source code is required")
    if len(source) > 200_000:
        raise HTTPException(413, "Source code is too large")
    rules = [{"type": r.rule_type, "description": r.description}
             for r in db.execute(select(HistoricalRule)).scalars().all()]
    findings = analyze(source, language, rules)
    score = quality_score(findings)
    review = Review(user_id=user.id, language=language, filename=filename,
                    source_code=source, score=score, summary=summarize(findings, score))
    db.add(review); db.flush()
    for f in findings:
        db.add(Finding(review_id=review.id, category=f.category, severity=f.severity,
                       title=f.title, description=f.description,
                       recommendation=f.recommendation, line_number=f.line_number))
    db.commit()
    return {"id": review.id, "score": score, "summary": review.summary,
            "findings": [f.__dict__ | {"_sa_instance_state": None} for f in []]}

@app.get("/api/reviews")
def list_reviews(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: raise HTTPException(401, "Authentication required")
    rows = db.execute(select(Review).where(Review.user_id == user.id).order_by(Review.created_at.desc())).scalars().all()
    return [{"id": r.id, "filename": r.filename, "language": r.language, "score": r.score,
             "summary": r.summary, "created_at": r.created_at.isoformat()} for r in rows]

@app.get("/api/reviews/{review_id}")
def get_review(review_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    review = db.get(Review, review_id)
    if not user or not review or review.user_id != user.id:
        raise HTTPException(404, "Review not found")
    return {"id": review.id, "filename": review.filename, "language": review.language,
            "score": review.score, "summary": review.summary, "source_code": review.source_code,
            "created_at": review.created_at.isoformat(),
            "findings": [{"category": f.category, "severity": f.severity, "title": f.title,
                          "description": f.description, "recommendation": f.recommendation,
                          "line_number": f.line_number} for f in review.findings]}

@app.get("/api/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: raise HTTPException(401, "Authentication required")
    reviews = db.execute(select(Review).where(Review.user_id == user.id).order_by(Review.created_at.asc())).scalars().all()
    avg = round(sum(r.score for r in reviews) / len(reviews), 1) if reviews else 0
    categories = {}
    for r in reviews:
        for f in r.findings:
            categories[f.category] = categories.get(f.category, 0) + 1
    return {"total_reviews": len(reviews), "average_score": avg,
            "best_score": max((r.score for r in reviews), default=0),
            "trend": [{"date": r.created_at.strftime("%Y-%m-%d"), "score": r.score} for r in reviews[-10:]],
            "categories": categories}

@app.post("/api/historical/import")
async def import_historical(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: raise HTTPException(401, "Authentication required")
    form = await request.form()
    upload = form.get("file")
    if not upload: raise HTTPException(400, "CSV file is required")
    raw = await upload.read()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    added = 0
    for row in reader:
        if row.get("description"):
            db.add(HistoricalRule(rule_type=row.get("type", "historical"), description=row["description"]))
            added += 1
    db.commit()
    return {"imported": added}
