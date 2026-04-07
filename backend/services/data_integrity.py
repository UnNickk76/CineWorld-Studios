from bson import ObjectId

REQUIRED_FIELDS = ["title", "status"]
OWNER_FIELD = "user_id"


async def validate_film_document(film):
    if not film:
        return False

    for field in REQUIRED_FIELDS:
        if field not in film or film[field] is None:
            return False

    return True


async def clean_invalid_films(db):
    films = await db.films.find().to_list(1000)

    invalid_ids = []

    for film in films:
        is_valid = await validate_film_document(film)
        if not is_valid:
            invalid_ids.append(film["_id"])

    if invalid_ids:
        await db.films.delete_many({"_id": {"$in": invalid_ids}})

    return len(invalid_ids)


async def get_safe_film(db, film_id, user_id=None):
    """Get a validated film by string id or ObjectId."""
    film = None

    # Try string id first (project convention)
    query = {'id': film_id}
    if user_id:
        query['user_id'] = user_id
    film = await db.films.find_one(query, {'_id': 0})

    # Fallback to ObjectId _id
    if not film:
        try:
            oid = ObjectId(film_id) if isinstance(film_id, str) else film_id
            query_oid = {'_id': oid}
            if user_id:
                query_oid['user_id'] = user_id
            film = await db.films.find_one(query_oid)
        except Exception:
            return None

    if not await validate_film_document(film):
        return None

    return film
