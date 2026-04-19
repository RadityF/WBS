from fastapi import APIRouter, Depends

from app.deps import get_current_admin
from app.services.kb_service import reindex_knowledge_base


router = APIRouter(prefix="/v1/kb", tags=["knowledge-base"])


@router.post("/reindex")
def reindex(_: object = Depends(get_current_admin)):
    return reindex_knowledge_base()
