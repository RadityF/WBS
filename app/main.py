import os

from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.kb import router as kb_router
from app.api.reports import router as reports_router
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.models import AdminUser
from app.security import hash_value


app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.upload_dir, exist_ok=True)

    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == settings.admin_default_username).first()
        if not admin:
            db.add(
                AdminUser(
                    username=settings.admin_default_username,
                    password_hash=hash_value(settings.admin_default_password),
                )
            )
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(kb_router)
