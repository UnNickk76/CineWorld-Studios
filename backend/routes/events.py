# CineWorld Studio's - World Events Routes
# GET /events/active, GET /events/all

from fastapi import APIRouter

from game_systems import get_active_world_events, WORLD_EVENTS

router = APIRouter()


@router.get("/events/active")
async def get_active_events():
    """Get currently active world events."""
    events = get_active_world_events()
    return {
        'events': events,
        'count': len(events)
    }


@router.get("/events/all")
async def get_all_events():
    """Get all possible world events."""
    return list(WORLD_EVENTS.values())
