from __future__ import annotations

import re
import secrets
from datetime import datetime


def generate_ticket_id() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    suffix = secrets.token_hex(2).upper()
    return f"WBS-{ts}-{suffix}"


def generate_pin() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def mask_pii(text: str) -> str:
    masked = text
    masked = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL]", masked)
    masked = re.sub(r"\b(?:\+62|62|0)8[0-9]{8,12}\b", "[PHONE]", masked)
    masked = re.sub(r"\b[0-9]{16}\b", "[NIK]", masked)
    return masked
