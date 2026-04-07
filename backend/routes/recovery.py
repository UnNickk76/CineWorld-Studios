from fastapi import APIRouter
from database import db

router = APIRouter()


@router.post("/api/recovery/recover-film/{film_id}")
async def recover_film(film_id: str):
    # Try by string id first
    film = await db.films.find_one({"id": film_id}, {"_id": 0})

    if not film:
        return {"error": "Film non trovato"}

    update_data = {
        "status": film.get("status", "draft"),
        "poster_url": film.get("poster_url", "/api/posters/drama.jpeg"),
    }

    # Fill missing required fields
    if not film.get("title"):
        update_data["title"] = "Film Recuperato"
    if not film.get("user_id"):
        return {"error": "Film senza proprietario, non recuperabile"}

    await db.films.update_one(
        {"id": film_id},
        {"$set": update_data}
    )

    return {"success": True, "film_id": film_id, "updated": update_data}
