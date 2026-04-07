from fastapi import APIRouter
from database import db
from services.film_transaction_service import recover_or_quarantine_film

router = APIRouter()


@router.post("/api/recovery/recover-film/{film_id}")
async def recover_film(film_id: str):
    result = await recover_or_quarantine_film(db, film_id)
    return result
