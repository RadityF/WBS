from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_admin
from app.models import CaseStatusLog, Report, ReportAttachment, ReportMessage
from app.schemas import (
    AdminCaseDetail,
    AdminCaseItem,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMessageRequest,
    AdminUpdateStatusRequest,
    GenericMessage,
)
from app.security import create_access_token, verify_value


router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    from app.models import AdminUser

    user = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if not user or not verify_value(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username/password salah")

    token = create_access_token(user.username)
    return AdminLoginResponse(access_token=token)


@router.get("/cases", response_model=list[AdminCaseItem])
def list_cases(status: Optional[str] = None, _: object = Depends(get_current_admin), db: Session = Depends(get_db)):
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    rows = query.order_by(Report.updated_at.desc()).all()

    return [
        AdminCaseItem(
            ticket_id=r.ticket_id,
            status=r.status,
            scenario=r.scenario,
            category=r.category,
            urgency=r.urgency,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get("/cases/{ticket_id}", response_model=AdminCaseDetail)
def case_detail(ticket_id: str, _: object = Depends(get_current_admin), db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.ticket_id == ticket_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Case tidak ditemukan")

    messages = db.query(ReportMessage).filter(ReportMessage.report_id == report.id).order_by(ReportMessage.id.asc()).all()
    attachments = db.query(ReportAttachment).filter(ReportAttachment.report_id == report.id).all()

    return AdminCaseDetail(
        ticket_id=report.ticket_id,
        status=report.status,
        category=report.category,
        scenario=report.scenario,
        urgency=report.urgency,
        summary=report.summary,
        reason=report.reason,
        latest_response_to_reporter=report.latest_response_to_reporter,
        followup_round=report.followup_round,
        messages=[
            {
                "sender_type": m.sender_type,
                "message_type": m.message_type,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in messages
        ],
        attachments=[
            {
                "filename": a.filename,
                "saved_path": a.saved_path,
                "content_type": a.content_type,
                "created_at": a.created_at,
            }
            for a in attachments
        ],
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post("/cases/{ticket_id}/status", response_model=GenericMessage)
def update_case_status(
    ticket_id: str,
    payload: AdminUpdateStatusRequest,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.ticket_id == ticket_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Case tidak ditemukan")

    old = report.status
    report.status = payload.new_status
    db.add(
        CaseStatusLog(
            report_id=report.id,
            old_status=old,
            new_status=payload.new_status,
            actor=f"admin:{admin.username}",
            notes=payload.notes,
        )
    )
    db.commit()
    return GenericMessage(message=f"Status {ticket_id} diubah ke {payload.new_status}")


@router.post("/cases/{ticket_id}/message", response_model=GenericMessage)
def send_message_to_reporter(
    ticket_id: str,
    payload: AdminMessageRequest,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.ticket_id == ticket_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Case tidak ditemukan")

    db.add(
        ReportMessage(
            report_id=report.id,
            sender_type="admin",
            message_type="admin_message",
            content=payload.message,
        )
    )
    report.latest_response_to_reporter = payload.message
    if payload.mark_needs_info:
        old = report.status
        report.status = "NEEDS_INFO"
        db.add(
            CaseStatusLog(
                report_id=report.id,
                old_status=old,
                new_status=report.status,
                actor=f"admin:{admin.username}",
                notes="Admin meminta klarifikasi tambahan ke pelapor",
            )
        )
    db.commit()
    return GenericMessage(message="Pesan admin sudah dikirim ke pelapor")
