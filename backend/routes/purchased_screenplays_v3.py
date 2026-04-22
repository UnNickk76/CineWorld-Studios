"""Purchased Screenplays → Pipeline V3 bridge.

Unified flow for buying a ready-made screenplay (from Emerging public pool
OR from own Agency Scout) and launching it directly into Pipeline V3.

Two modes:
- avanzata: guided pipeline with idea/cast/prep locked, player plays all
           timed steps + marketing/premiere/distribution normally
- veloce:  everything pre-done except poster+trailer. Skips all timers,
           auto-fills marketing with top sponsors, skips La Prima, lands
           directly on distribution step. Costs 2x, gives -50% XP/Fame.

Pricing rules:
- Base: screenplay.full_package_cost (emerging) or screenplay.cost (agency)
- veloce → cost * 2
- source=agency → cost * 0.4 (60% discount, your own scout)
"""

import uuid
import random
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from database import db
from auth_utils import get_current_user

router = APIRouter()


class CreateFromScreenplayBody(BaseModel):
    screenplay_id: str
    source: str  # 'emerging' | 'agency'
    mode: str    # 'avanzata' | 'veloce'


def _calc_price(base_cost: int, mode: str, source: str) -> int:
    cost = int(base_cost or 0)
    if mode == 'veloce':
        cost = int(cost * 2)
    if source == 'agency':
        cost = int(cost * 0.4)  # 60% discount on own agency
    return max(1000, cost)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fetch_screenplay(screenplay_id: str, source: str, user_id: str) -> dict:
    """Fetch screenplay from the correct source collection."""
    if source == 'emerging':
        sp = await db.emerging_screenplays.find_one({'id': screenplay_id}, {'_id': 0})
        if not sp:
            raise HTTPException(404, 'Sceneggiatura non trovata')
        if sp.get('status') != 'available':
            raise HTTPException(400, 'Sceneggiatura non più disponibile')
        if sp.get('expires_at', '') < _now():
            raise HTTPException(400, 'Sceneggiatura scaduta')
        return sp
    elif source == 'agency':
        sp = await db.scout_screenplay_pool.find_one(
            {'id': screenplay_id, 'user_id': user_id, 'purchased': False}, {'_id': 0}
        )
        if not sp:
            raise HTTPException(404, 'Sceneggiatura non trovata o già acquistata')
        return sp
    else:
        raise HTTPException(400, 'source deve essere emerging o agency')


async def _mark_screenplay_consumed(screenplay_id: str, source: str, user_id: str,
                                     project_id: str, mode: str, cost: int):
    """Mark the source screenplay as used."""
    if source == 'emerging':
        await db.emerging_screenplays.update_one(
            {'id': screenplay_id},
            {'$set': {
                'status': 'accepted',
                'accepted_by': user_id,
                'accepted_mode': mode,
                'accepted_at': _now(),
                'used_in_project': project_id,
            }}
        )
    else:  # agency
        await db.scout_screenplay_pool.update_one(
            {'id': screenplay_id},
            {'$set': {'purchased': True, 'used_in_project': project_id, 'used_at': _now()}}
        )


async def _auto_fill_cast(user_id: str, genre: str) -> dict:
    """Pick best actors from user's agency + NPC fillers (stelle medie).
    Returns a cast dict compatible with pipeline_v3 cast schema.
    """
    cast = {'director': None, 'screenwriters': [], 'actors': [], 'composer': None}

    # 1) Prefer user's hired_stars (agency actors) — sorted by fame/skill
    hired = await db.hired_stars.find({'user_id': user_id}, {'_id': 0}).to_list(50)
    hired.sort(key=lambda x: (x.get('fame_score', 0), x.get('skill_avg', 0)), reverse=True)

    used_ids = set()

    def _actor_from_hired(h: dict, role_type: str) -> dict:
        used_ids.add(h.get('id'))
        return {
            'id': h.get('id'),
            'name': h.get('name'),
            'age': h.get('age'),
            'nationality': h.get('nationality', ''),
            'gender': h.get('gender', ''),
            'stars': h.get('stars', 2),
            'fame': h.get('fame_score', 0),
            'fame_category': h.get('fame_category', 'rookie'),
            'role_type': role_type,
            'cost': h.get('cost_per_film', h.get('cost', 50000)),
            'skills': h.get('skills', {}),
            'primary_skills': h.get('primary_skills', []),
            'crc': h.get('crc', 50),
            'from_agency': True,
        }

    roles_order = ['protagonista', 'antagonista', 'co protagonista', 'supporto', 'generico', 'generico']
    for i, h in enumerate(hired[:6]):
        role = roles_order[i] if i < len(roles_order) else 'generico'
        a = _actor_from_hired(h, 'actor')
        a['cast_role'] = role
        cast['actors'].append(a)

    # 2) Fill with NPC medium-tier actors if needed (target 5-7)
    target = max(5, min(7, len(cast['actors']) + 2))
    if len(cast['actors']) < target:
        npcs = await db.people.find(
            {'type': 'actor', 'stars': {'$gte': 2, '$lte': 3}},
            {'_id': 0}
        ).limit(50).to_list(50)
        random.shuffle(npcs)
        for n in npcs:
            if len(cast['actors']) >= target:
                break
            if n.get('id') in used_ids:
                continue
            used_ids.add(n.get('id'))
            idx = len(cast['actors'])
            role = roles_order[idx] if idx < len(roles_order) else 'generico'
            cast['actors'].append({
                'id': n.get('id'),
                'name': n.get('name'),
                'age': n.get('age'),
                'nationality': n.get('nationality', ''),
                'gender': n.get('gender', ''),
                'stars': n.get('stars', 2),
                'fame': n.get('fame_score', 0),
                'fame_category': n.get('fame_category', 'rookie'),
                'role_type': 'actor',
                'cost': n.get('cost_per_film', n.get('cost', 50000)),
                'skills': n.get('skills', {}),
                'primary_skills': n.get('primary_skills', []),
                'crc': 50,
                'cast_role': role,
                'from_agency': False,
            })

    # 3) Director, composer, screenwriter from NPC pool (medium stars)
    for role_key, field in [('director', 'director'), ('composer', 'composer')]:
        npc = await db.people.find_one(
            {'type': role_key, 'stars': {'$gte': 2, '$lte': 4}}, {'_id': 0}
        )
        if npc:
            cast[field] = {
                'id': npc.get('id'), 'name': npc.get('name'), 'age': npc.get('age'),
                'nationality': npc.get('nationality', ''), 'gender': npc.get('gender', ''),
                'stars': npc.get('stars', 2), 'fame': npc.get('fame_score', 0),
                'fame_category': npc.get('fame_category', 'rookie'),
                'role_type': role_key, 'cost': npc.get('cost_per_film', 50000),
                'skills': npc.get('skills', {}), 'primary_skills': npc.get('primary_skills', []),
                'crc': 50,
            }

    writer = await db.people.find_one(
        {'type': {'$in': ['screenwriter', 'writer']}, 'stars': {'$gte': 2, '$lte': 4}},
        {'_id': 0}
    )
    if writer:
        cast['screenwriters'].append({
            'id': writer.get('id'), 'name': writer.get('name'), 'age': writer.get('age'),
            'nationality': writer.get('nationality', ''), 'gender': writer.get('gender', ''),
            'stars': writer.get('stars', 2), 'fame': writer.get('fame_score', 0),
            'fame_category': writer.get('fame_category', 'rookie'),
            'role_type': 'screenwriter', 'cost': writer.get('cost_per_film', 50000),
            'skills': writer.get('skills', {}), 'primary_skills': writer.get('primary_skills', []),
            'crc': 50,
        })

    return cast


def _auto_fill_prep() -> dict:
    """Preset prep choices (attrezzature, comparse) for purchased screenplays."""
    return {
        'attrezzature_level': 'medium',  # medium tier
        'comparse_level': 'medium',
        'equipment_budget': 500000,
        'extras_count': 50,
        'shooting_days': 60,
    }


def _auto_fill_marketing() -> list:
    """Veloce preset: 3 top sponsors + 1 medium-top marketing campaign."""
    return [
        {'id': 'sponsor_1', 'type': 'sponsor', 'name': 'Top Sponsor A',
         'tier': 'premium', 'cost': 200000, 'revenue_boost': 0.18},
        {'id': 'sponsor_2', 'type': 'sponsor', 'name': 'Top Sponsor B',
         'tier': 'premium', 'cost': 200000, 'revenue_boost': 0.15},
        {'id': 'sponsor_3', 'type': 'sponsor', 'name': 'Top Sponsor C',
         'tier': 'premium', 'cost': 180000, 'revenue_boost': 0.12},
        {'id': 'campaign_1', 'type': 'marketing', 'name': 'Campagna Premium',
         'tier': 'top', 'cost': 600000, 'hype_boost': 25, 'reach': 'global'},
    ]


def _base_cost(screenplay: dict, source: str) -> int:
    if source == 'emerging':
        return int(screenplay.get('full_package_cost', screenplay.get('screenplay_cost', 500000)) or 500000)
    else:  # agency
        return int(screenplay.get('cost', 500000) or 500000)


@router.post("/api/purchased-screenplays/veloce-fast-track/{pid}")
async def veloce_fast_track(pid: str, user: dict = Depends(get_current_user)):
    """Veloce mode only: after player creates poster + trailer, cascade through
    cast/prep/ciak/finalcut/marketing (all pre-filled) and land on distribution.
    Skips La Prima entirely.
    """
    project = await db.film_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(404, 'Progetto non trovato')
    if not project.get('auto_advance_veloce'):
        raise HTTPException(400, 'Questo progetto non è in modalità Veloce')
    if project.get('pipeline_state') != 'hype':
        raise HTTPException(400, f"Fast-track disponibile solo da 'hype' (attuale: {project.get('pipeline_state')})")
    # Require player to have completed poster + trailer
    if not project.get('poster_url'):
        raise HTTPException(400, 'Devi creare la locandina prima di continuare.')
    if not project.get('trailer_url') and not project.get('trailer_generated'):
        # trailer is optional gate — let it through but warn
        pass

    now_iso = _now()
    # Pre-fill all intermediate timers as already complete + set final state
    update = {
        'pipeline_state': 'distribution',
        'pipeline_ui_step': 8,   # distribution index
        'max_step_reached': 8,
        # Hype: mark as completed
        'hype_complete_at': now_iso,
        'hype_progress': 100,
        # Ciak: mark done instantly
        'ciak_started_at': now_iso,
        'ciak_complete_at': now_iso,
        # FinalCut: mark done
        'finalcut_started_at': now_iso,
        'finalcut_complete_at': now_iso,
        'finalcut_hours': 0,
        # La Prima skipped → release_type 'direct'
        'release_type': 'direct',
        'updated_at': now_iso,
    }
    await db.film_projects.update_one({'id': pid, 'user_id': user['id']}, {'$set': update})

    updated = await db.film_projects.find_one({'id': pid, 'user_id': user['id']}, {'_id': 0})
    return {
        'success': True,
        'project': updated,
        'message': 'Fast-track completato! Scegli dove e quando rilasciare il film.',
    }



@router.post("/api/purchased-screenplays/create-v3-project")
async def create_v3_from_screenplay(
    req: CreateFromScreenplayBody,
    user: dict = Depends(get_current_user)
):
    """Unified endpoint: buy a screenplay (any source) and launch it in Pipeline V3."""
    if req.mode not in ('avanzata', 'veloce'):
        raise HTTPException(400, "mode deve essere 'avanzata' o 'veloce'")
    if req.source not in ('emerging', 'agency'):
        raise HTTPException(400, "source deve essere 'emerging' o 'agency'")

    screenplay = await _fetch_screenplay(req.screenplay_id, req.source, user['id'])
    base_cost = _base_cost(screenplay, req.source)
    final_cost = _calc_price(base_cost, req.mode, req.source)

    # Check funds (but don't deduct yet — only after project is safely created)
    fresh_user = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    funds = int(fresh_user.get('funds', 0) or 0)
    if funds < final_cost:
        raise HTTPException(400, f'Fondi insufficienti. Servono ${final_cost:,}')

    # Extract screenplay data (normalize from both sources)
    title = screenplay.get('title', 'Film Senza Titolo')
    genre = screenplay.get('genre', 'drama')
    subgenres = screenplay.get('subgenres') or [screenplay.get('subgenre', '')]
    subgenres = [s for s in subgenres if s]
    preplot = screenplay.get('synopsis') or screenplay.get('logline') or ''
    full_text = screenplay.get('full_text') or screenplay.get('screenplay') or ''
    base_quality = int(screenplay.get('quality', screenplay.get('idea_score', 60)) or 60)
    writer_name = screenplay.get('writer_name') or screenplay.get('writer', 'Sconosciuto')

    # Auto-fill cast (for both modes — idea/cast/prep locked in both)
    cast = await _auto_fill_cast(user['id'], genre)
    prep = _auto_fill_prep()

    # Build V3 project
    pid = str(uuid.uuid4())
    now = _now()
    doc = {
        'id': pid,
        'user_id': user['id'],
        'pipeline_version': 3,
        'type': 'film',
        'title': title,
        'genre': genre,
        'subgenre': subgenres[0] if subgenres else None,
        'subgenres': subgenres,
        'preplot': preplot,
        'pipeline_state': 'hype',   # idea step already complete
        'pipeline_ui_step': 1,
        'poster_source': None,
        'poster_prompt': '',
        'poster_prompt_note': '',
        'poster_url': '',            # player will create
        'screenplay_source': 'purchased',
        'screenplay_prompt': '',
        'screenplay_text': full_text,
        'hype_notes': '',
        'hype_budget': 0,
        'cast': cast,
        'cast_notes': 'Cast pre-assegnato dalla sceneggiatura',
        'chemistry_mode': 'auto',
        'prep_notes': 'Pre-produzione pre-impostata',
        'prep_options': prep,
        'ciak_started_at': None,
        'ciak_complete_at': None,
        'finalcut_notes': '',
        'marketing_packages': [],
        'release_type': None,
        'release_date_label': None,
        'distribution_world': True,
        'distribution_zones': [],
        'quality_score': None,
        'final_quality': None,
        'status': 'pipeline_active',
        # Purchased-screenplay flags
        'from_purchased_screenplay': True,
        'purchased_screenplay_id': req.screenplay_id,
        'purchased_screenplay_source': req.source,      # 'emerging' | 'agency'
        'purchased_screenplay_mode': req.mode,          # 'avanzata' | 'veloce'
        'purchased_writer_name': writer_name,
        'purchased_base_quality': base_quality,
        'purchased_cost_paid': final_cost,
        # UI lock hints (read-only phases)
        'idea_locked': True,
        'cast_locked': True,
        'prep_locked': True,
        'created_at': now,
        'updated_at': now,
    }

    # Veloce extras: preset marketing + skip la_prima
    if req.mode == 'veloce':
        doc['marketing_packages'] = _auto_fill_marketing()
        doc['marketing_locked'] = True
        doc['skip_la_prima'] = True
        doc['auto_advance_veloce'] = True  # signals advance_state to cascade

    await db.film_projects.insert_one(doc)
    doc.pop('_id', None)

    # Mark source screenplay as consumed
    await _mark_screenplay_consumed(req.screenplay_id, req.source, user['id'], pid,
                                      req.mode, final_cost)

    # Deduct funds LAST — only now that project + consume are both committed.
    # If anything above fails, no money was deducted (fail-safe).
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -final_cost}})

    # XP reward — halved for veloce (easier path = less progression)
    try:
        from utils.xp_fame import award_milestone
        milestone = 'screenplay_done'
        bonus_xp = 5 if req.mode == 'veloce' else 15
        bonus_fame = 0 if req.mode == 'veloce' else 1
        await award_milestone(
            db, user['id'], milestone,
            bonus_xp=bonus_xp, bonus_fame=bonus_fame, title=f'Sceneggiatura pronta: {title}'
        )
    except Exception:
        pass

    return {
        'success': True,
        'project_id': pid,
        'project': doc,
        'cost_paid': final_cost,
        'base_cost': base_cost,
        'discount_applied': req.source == 'agency',
        'mode': req.mode,
        'message': (
            f'"{title}" pronta! Modalità {req.mode.upper()}. -${final_cost:,}. '
            f"{'Crea locandina, trailer e rilascia il film.' if req.mode == 'veloce' else 'Continua dalla fase Hype.'}"
        ),
    }
