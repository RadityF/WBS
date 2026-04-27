from __future__ import annotations

from datetime import datetime
from typing import Literal
from typing import Optional

from pydantic import BaseModel, Field


class LawReference(BaseModel):
    uu: Optional[str] = None
    pasal: Optional[str] = None
    ayat: Optional[str] = None
    isi_singkat: Optional[str] = None


class PasalCandidate(BaseModel):
    uu: Optional[str] = None
    pasal: Optional[str] = None
    ayat: Optional[str] = None
    alasan_relevansi: Optional[str] = None
    skor_relatif: Optional[float] = None


class AiOutput(BaseModel):
    kategori: Optional[str] = None
    skenario: Literal[1, 2, 3]
    alasan: str
    referensi_hukum: list[LawReference] = Field(default_factory=list)
    pasal_utama: Optional[PasalCandidate] = None
    pasal_kandidat: list[PasalCandidate] = Field(default_factory=list)
    urgensi: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
    summary: Optional[str] = None
    respons_pelapor: str
    follow_up_questions: list[str] = Field(default_factory=list)
    needs_human_review: bool = False
    needs_escalation: bool = False
    ticket_id: Optional[str] = None
    redirect_to: Optional[str] = None


class SubmitReportResponse(BaseModel):
    ticket_id: str
    pin: str
    status: str
    message: str


class ReportStatusResponse(BaseModel):
    ticket_id: str
    status: str
    category: Optional[str] = None
    scenario: Optional[int] = None
    urgency: Optional[str] = None
    summary: Optional[str] = None
    response_to_reporter: Optional[str] = None
    follow_up_questions: list[str] = Field(default_factory=list)
    followup_round: int
    updated_at: datetime


class ReplyRequest(BaseModel):
    pin: str
    message: str = Field(min_length=3, max_length=3000)


class GenericMessage(BaseModel):
    message: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminCaseItem(BaseModel):
    ticket_id: str
    status: str
    scenario: Optional[int] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminCaseDetail(BaseModel):
    ticket_id: str
    status: str
    category: Optional[str] = None
    scenario: Optional[int] = None
    urgency: Optional[str] = None
    summary: Optional[str] = None
    reason: Optional[str] = None
    latest_response_to_reporter: Optional[str] = None
    followup_round: int
    messages: list[dict]
    attachments: list[dict]
    created_at: datetime
    updated_at: datetime


class AdminUpdateStatusRequest(BaseModel):
    new_status: str
    notes: Optional[str] = None


class AdminMessageRequest(BaseModel):
    message: str = Field(min_length=3, max_length=3000)
    mark_needs_info: bool = True
