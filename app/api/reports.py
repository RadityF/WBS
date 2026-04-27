from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Report, ReportAttachment, ReportFollowupQuestion, ReportMessage
from app.schemas import GenericMessage, ReportStatusResponse, SubmitReportResponse
from app.security import hash_value, verify_value
from app.services.rag_service import analyze_report, can_access_with_pin, lock_pin_if_needed
from app.services.utils import generate_pin, generate_ticket_id


router = APIRouter(prefix="/v1/reports", tags=["reports"])


@router.post("/submit", response_model=SubmitReportResponse)
def submit_report(
    narrative: str = Form(..., min_length=10, max_length=6000),
    attachments: Optional[list[UploadFile]] = File(default=None),
    db: Session = Depends(get_db),
):
    os.makedirs(settings.upload_dir, exist_ok=True)

    pin = generate_pin()
    report = None
    ticket_id = ""
    for _ in range(5):
        ticket_id = generate_ticket_id()
        report = Report(
            ticket_id=ticket_id,
            pin_hash=hash_value(pin),
            status="SUBMITTED",
        )
        db.add(report)
        try:
            db.flush()
            break
        except IntegrityError:
            db.rollback()
            report = None

    if report is None:
        raise HTTPException(status_code=500, detail="Gagal generate ticket unik, coba ulangi")

    db.add(
        ReportMessage(
            report_id=report.id,
            sender_type="reporter",
            message_type="initial",
            content=narrative,
        )
    )

    _save_attachments(db, report, ticket_id, attachments)

    ai_result = analyze_report(db, report, narrative)
    db.commit()

    return SubmitReportResponse(
        ticket_id=report.ticket_id,
        pin=pin,
        status=report.status,
        message=ai_result.respons_pelapor,
    )


def _save_attachments(db: Session, report: Report, ticket_id: str, attachments: Optional[list[UploadFile]]) -> None:
    if not attachments:
        return

    os.makedirs(settings.upload_dir, exist_ok=True)
    for file in attachments:
        filename = f"{ticket_id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
        safe_path = os.path.join(settings.upload_dir, filename)
        with open(safe_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        db.add(
            ReportAttachment(
                report_id=report.id,
                filename=file.filename,
                saved_path=safe_path,
                content_type=file.content_type,
            )
        )


def _get_report_by_ticket(db: Session, ticket_id: str) -> Report:
    report = db.query(Report).filter(Report.ticket_id == ticket_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket tidak ditemukan")
    return report


@router.get("/{ticket_id}/status", response_model=ReportStatusResponse)
def get_report_status(ticket_id: str, pin: str, db: Session = Depends(get_db)):
    report = _get_report_by_ticket(db, ticket_id)

    can_access, reason = can_access_with_pin(report)
    if not can_access:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=reason)

    if not verify_value(pin, report.pin_hash):
        report.pin_failed_attempts += 1
        lock_pin_if_needed(report)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="PIN tidak valid")

    report.pin_failed_attempts = 0
    report.pin_locked_until = None
    db.commit()

    followups = (
        db.query(ReportFollowupQuestion)
        .filter(ReportFollowupQuestion.report_id == report.id, ReportFollowupQuestion.answered.is_(False))
        .all()
    )
    questions = [q.question for q in followups]

    return ReportStatusResponse(
        ticket_id=report.ticket_id,
        status=report.status,
        category=report.category,
        scenario=report.scenario,
        urgency=report.urgency,
        summary=report.summary,
        response_to_reporter=report.latest_response_to_reporter,
        follow_up_questions=questions,
        followup_round=report.followup_round,
        updated_at=report.updated_at,
    )


@router.post("/{ticket_id}/reply", response_model=GenericMessage)
def reply_followup(
    ticket_id: str,
    pin: str = Form(...),
    message: str = Form(..., min_length=3, max_length=3000),
    attachments: Optional[list[UploadFile]] = File(default=None),
    db: Session = Depends(get_db),
):
    report = _get_report_by_ticket(db, ticket_id)
    if report.status != "NEEDS_INFO":
        raise HTTPException(status_code=400, detail="Kasus tidak dalam status klarifikasi")

    can_access, reason = can_access_with_pin(report)
    if not can_access:
        raise HTTPException(status_code=429, detail=reason)

    if not verify_value(pin, report.pin_hash):
        report.pin_failed_attempts += 1
        lock_pin_if_needed(report)
        db.commit()
        raise HTTPException(status_code=401, detail="PIN tidak valid")

    report.pin_failed_attempts = 0
    report.pin_locked_until = None

    db.add(
        ReportMessage(
            report_id=report.id,
            sender_type="reporter",
            message_type="followup_reply",
            content=message,
        )
    )
    _save_attachments(db, report, ticket_id, attachments)

    unanswered = (
        db.query(ReportFollowupQuestion)
        .filter(ReportFollowupQuestion.report_id == report.id, ReportFollowupQuestion.answered.is_(False))
        .all()
    )
    for item in unanswered:
        item.answered = True

    report.followup_round += 1
    if report.followup_round > 3:
        report.status = "NEEDS_REVIEW"
        report.latest_response_to_reporter = "Batas klarifikasi tercapai. Kasus diteruskan ke admin untuk review manual."
        db.commit()
        return GenericMessage(message=report.latest_response_to_reporter)

    all_messages = db.query(ReportMessage).filter(ReportMessage.report_id == report.id).order_by(ReportMessage.id.asc()).all()
    combined_text = "\n".join([m.content for m in all_messages if m.sender_type == "reporter"])

    analyze_report(db, report, combined_text)
    db.commit()
    return GenericMessage(message=report.latest_response_to_reporter or "Jawaban Anda sudah diterima")
