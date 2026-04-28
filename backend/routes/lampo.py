"""
Produzione LAMPO — pipeline ultra-ridotta per film, serie TV e anime.

Flusso:
  POST /api/lampo/start        → crea progetto e avvia background task
  GET  /api/lampo/{pid}/progress → stato avanzamento (0-100% + messaggio)
  POST /api/lampo/{pid}/release  → bottone "Rilascia al Cinema" (film) o "Manda in TV" (serie/anime)

Durata fissa ~2 minuti. AI (Emergent LLM key + nano-banana) genera tutto.
"""
import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database import db
from auth_utils import get_current_user
from utils.studio_quota import check_studio_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/lampo", tags=["lampo"])


# ═══════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════

ContentType = Literal["film", "tv_series", "anime"]
BudgetTier = Literal["low", "mid", "high"]

BUDGET_COSTS = {
    "film":     {"low": 50_000,  "mid": 150_000, "high": 400_000},
    "tv_series":{"low": 80_000,  "mid": 250_000, "high": 700_000},
    "anime":    {"low": 100_000, "mid": 350_000, "high": 900_000},
}
BUDGET_CP = {
    "film":     {"low": 0,  "mid": 3, "high": 8},
    "tv_series":{"low": 0,  "mid": 5, "high": 12},
    "anime":    {"low": 0,  "mid": 6, "high": 15},
}
BUDGET_CWSV_MOD = {"low": -1.0, "mid": 0.0, "high": 0.8}

# CWSv range per studio level tier — più variabilità: i progetti LAMPO possono uscire bene anche a basso livello (rare ma possibili)
CWSV_TABLE = [
    # (lvl_cap, low, high, jackpot_low, jackpot_high, jackpot_prob)
    (5,   2.5, 6.0, 7.5, 8.5, 0.10),   # Lv 0-5: range largo (2.5-6) + jackpot 10% chance fino a 8.5
    (10,  3.5, 6.8, 8.0, 9.0, 0.12),
    (20,  4.5, 7.5, 8.5, 9.2, 0.13),
    (50,  5.5, 8.2, 8.8, 9.5, 0.14),
    (100, 6.5, 8.8, 9.0, 9.7, 0.15),
]
CWSV_UNLIMITED = (7.0, 9.2, 9.3, 9.9, 0.18)

DURATION_SECONDS = 120  # 2 minuti

# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

class StartLampoRequest(BaseModel):
    content_type: ContentType
    title: str = Field(..., min_length=2, max_length=80)
    genre: str
    subgenre: Optional[str] = None
    preplot: str = Field(..., min_length=10, max_length=1000)
    budget_tier: BudgetTier = "mid"
    num_episodes: Optional[int] = 10  # serie/anime only
    target_tv_station_id: Optional[str] = None  # serie/anime only — manda alla mia TV
    vm_rating: Optional[Literal["vm14", "vm16", "vm18"]] = None


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _cwsv_for_studio_level(level: int, budget_tier: str) -> float:
    """Roll a CWSv based on studio level + budget tier modifier."""
    lvl = max(0, int(level or 0))
    chosen = CWSV_UNLIMITED
    for cap, lo, hi, jlo, jhi, jprob in CWSV_TABLE:
        if lvl <= cap:
            chosen = (lo, hi, jlo, jhi, jprob)
            break
    lo, hi, jlo, jhi, jprob = chosen
    # Jackpot?
    if random.random() < jprob:
        score = random.uniform(jlo, jhi)
    else:
        score = random.uniform(lo, hi)
    score += BUDGET_CWSV_MOD.get(budget_tier, 0)
    return round(max(1.0, min(9.8, score)), 1)


async def _pick_random_cast(content_type: str, level: int, num_actors: int = 5, budget_tier: str = "mid", cwsv: float = 5.0, genre: str = "") -> dict:
    """Random NPC cast selection, filtered by player level (reuses level-gating logic).

    Arricchisce ogni membro con: gender_label, age, role_label, character_role (solo attori),
    score (coerente con livello/fama/budget/qualità + piccolo random) e is_guest_star (rara!).
    """
    import random as _rnd
    if level <= 2: max_stars = 2
    elif level <= 5: max_stars = 3
    elif level <= 15: max_stars = 4
    else: max_stars = 5

    is_anime = content_type == "anime"
    # Animation: anche film/tv_series con genere "animation" usano disegnatori e regista anime
    is_animation_film = (genre or "").lower() == "animation" and not is_anime
    use_illustrators = is_anime or is_animation_film
    director_type = "anime_director" if use_illustrators else "director"
    actor_type = "anime_illustrator" if use_illustrators else "actor"
    actor_label_it = "Disegnatore" if use_illustrators else "Attore"

    # Probabilità ridotta che UN membro sia "guest star" (livello > progetto+3)
    # Eventro RARISSIMO: ~3% che capiti almeno un guest in tutto il cast
    guest_pool_max = min(5, max_stars + 3)
    guest_chance = 0.03

    async def _sample(rtype: str, count: int, allow_guest: bool = False):
        cap = guest_pool_max if (allow_guest and _rnd.random() < guest_chance) else max_stars
        pool = await db.people.aggregate([
            {"$match": {"$or": [{"type": rtype}, {"role_type": rtype}], "stars": {"$lte": cap}}},
            {"$sample": {"size": count}},
            {"$project": {"_id": 0}},
        ]).to_list(count)
        # ⚠️ Fallback difensivo: se vuoto, ripeschiamo SENZA filtro stelle per garantire cast non vuoto
        if not pool:
            pool = await db.people.aggregate([
                {"$match": {"$or": [{"type": rtype}, {"role_type": rtype}]}},
                {"$sample": {"size": count}},
                {"$project": {"_id": 0}},
            ]).to_list(count)
        return pool

    director_list = await _sample(director_type, 1, allow_guest=True)
    actors = await _sample(actor_type, num_actors, allow_guest=True)
    writer_list = await _sample("screenwriter" if not is_anime else "writer", 1, allow_guest=True)
    composer_list = await _sample("composer", 1, allow_guest=True)
    director = director_list[0] if director_list else None
    writer = writer_list[0] if writer_list else None
    composer = composer_list[0] if composer_list else None

    # Ruoli occupati (it)
    ROLE_LABELS = {
        "director": "Regista",
        "anime_director": "Regista Anime",
        "actor": "Attore",
        "anime_illustrator": "Disegnatore",
        "screenwriter": "Sceneggiatore",
        "writer": "Scrittore",
        "composer": "Compositore",
    }
    # Ruoli dei personaggi (solo attori)
    CHARACTER_ROLES = ["Protagonista", "Co-protagonista", "Antagonista", "Spalla", "Personaggio secondario", "Cameo"]

    def _enrich(member, role_type, character_role=None):
        if not member:
            return None
        # Gender → label leggibile
        g = (member.get("gender") or "").lower()
        gender_label = "M" if g.startswith("m") else ("F" if g.startswith("f") else "—")
        # Score coerente: base = livello giocatore + stars*5 + budget_mod + cwsv*1.5 + skill_level*0.2 + random
        budget_bonus = {"low": 0, "mid": 6, "high": 12}.get(budget_tier, 6)
        stars_val = int(member.get("stars") or 1)
        skill_val = int(member.get("skill_level") or 50)
        fame_val = float(member.get("fame_score") or 50.0)
        score = (
            level * 0.8
            + stars_val * 5
            + budget_bonus
            + cwsv * 1.5
            + skill_val * 0.2
            + fame_val * 0.15
            + _rnd.uniform(-3, 4)
        )
        score = max(1.0, min(99.0, round(score, 1)))
        # Guest star: stelle del cast > stelle "consentite" da player_level + 3
        is_guest = stars_val > (max_stars + 0)  # qualsiasi cast oltre il cap normale = guest
        out = {
            **member,
            "gender_label": gender_label,
            "role_type": role_type,
            "role_label": ROLE_LABELS.get(role_type, role_type),
            "score": score,
            "is_guest_star": bool(is_guest),
        }
        if character_role:
            out["character_role"] = character_role
        return out

    enriched_actors = []
    if actors:
        # Assegna ruoli specifici al cast (Protagonista per il primo, Co-protagonista per il secondo, ecc.)
        for i, actor in enumerate(actors):
            char_role = CHARACTER_ROLES[i] if i < len(CHARACTER_ROLES) else "Comparsa"
            enriched_actors.append(_enrich(actor, actor_type, character_role=char_role))

    return {
        "director": _enrich(director, director_type),
        "actors": enriched_actors,
        "screenwriters": [_enrich(writer, "screenwriter" if not is_anime else "writer")] if writer else [],
        "composer": _enrich(composer, "composer"),
        "actor_label": actor_label_it,
    }


async def _generate_poster_lampo(title: str, genre: str, content_type: str, project_id: str) -> str:
    """Generate AI poster via Emergent OpenAI Image (gpt-image-1) + persist nello storage poster."""
    import os
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return ""
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        from poster_storage import save_poster
        ct_label = {"film": "movie", "tv_series": "TV series", "anime": "anime"}.get(content_type, "movie")
        prompt = (
            f"Cinematic {ct_label} poster, genre: {genre}, title: '{title}'. "
            f"Bold typography, dramatic lighting, professional movie poster composition, vertical 2:3, "
            f"high contrast, atmospheric. No watermark."
        )
        img_gen = OpenAIImageGeneration(api_key=key)
        images = await img_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1,
            quality="low",
        )
        if images and len(images) > 0:
            filename = f"lampo_{project_id}.png"
            await save_poster(filename, images[0], "image/png")
            return f"/api/posters/{filename}"
    except Exception as e:
        logger.warning(f"LAMPO poster generation failed pid={project_id}: {e}")
    return ""


async def _insert_lampo_ready_stub(pid, proj, cast, cwsv, poster_url, screenplay_text, episodes, sponsors, distribution_plan, subgenres=None):
    """Inserisce nello standard films/tv_series uno stub 'lampo_ready' (bozza pre-rilascio).
    Idempotente: se già esiste uno stub con source_project_id == pid, non duplica."""
    ct = proj["content_type"]
    now = datetime.now(timezone.utc).isoformat()
    subgenres = subgenres or []
    if ct == "film":
        existing = await db.films.find_one({"source_project_id": pid}, {"_id": 0, "id": 1})
        if existing:
            return
        film_id = str(uuid.uuid4())
        await db.films.insert_one({
            "id": film_id,
            "user_id": proj["user_id"],
            "pipeline_version": 3,
            "source_project_id": pid,
            "mode": "lampo",
            "is_lampo": True,
            "title": proj["title"],
            "genre": proj["genre"],
            "subgenre": proj.get("subgenre"),
            "subgenres": subgenres,
            "vm_rating": proj.get("vm_rating"),
            "preplot": proj["preplot"],
            "screenplay": screenplay_text or "",
            "synopsis": screenplay_text or proj.get("preplot", ""),
            "poster_url": poster_url or "",
            "cast": cast,
            "quality_score": cwsv,
            "cwsv": cwsv,
            "status": "lampo_ready",
            "prossimamente": True,
            "released_at": None,
            "scheduled_release_at": None,
            "created_at": now,
            "total_revenue": 0,
            "virtual_likes": 0,
            "marketing_tier": proj.get("marketing_tier", "mid"),
            "budget_tier": proj.get("budget_tier"),
            "sponsors": sponsors or [],
            "equipment_tier": proj.get("budget_tier"),
            "distribution_scope": (distribution_plan or {}).get("scope_label"),
            "release_continents": (distribution_plan or {}).get("continents", []),
            "release_countries": (distribution_plan or {}).get("countries", []),
            "release_cities": (distribution_plan or {}).get("cities", []),
            "worldwide": bool((distribution_plan or {}).get("mondo", False)),
            "release_event": None,
        })
        await db.lampo_projects.update_one({"id": pid}, {"$set": {"linked_film_id": film_id}})
        return

    # tv_series / anime
    existing = await db.tv_series.find_one({"source_project_id": pid}, {"_id": 0, "id": 1})
    if existing:
        return
    series_id = str(uuid.uuid4())
    await db.tv_series.insert_one({
        "id": series_id,
        "source_project_id": pid,
        "user_id": proj["user_id"],
        "pipeline_version": 3,
        "mode": "lampo",
        "is_lampo": True,
        "type": ct,
        "title": proj["title"],
        "genre": proj["genre"],
        "genre_name": proj["genre"],
        "subgenres": subgenres,
        "vm_rating": proj.get("vm_rating"),
        "preplot": proj["preplot"],
        "screenplay": screenplay_text or "",
        "synopsis": screenplay_text or proj.get("preplot", ""),
        "poster_url": poster_url or "",
        "cast": cast,
        "episodes": episodes or [],
        "num_episodes": len(episodes or []),
        "total_episodes": len(episodes or []),
        "season_number": 1,
        "status": "lampo_ready",
        "prossimamente_tv": True,
        "scheduled_for_tv": False,
        "target_tv_station_id": proj.get("target_tv_station_id"),
        "quality_score": cwsv,
        "cwsv": cwsv,
        "released_at": None,
        "scheduled_release_at": None,
        "created_at": now,
        "total_revenue": 0,
        "sponsors": sponsors or [],
        "marketing_tier": proj.get("marketing_tier", "mid"),
    })
    await db.lampo_projects.update_one({"id": pid}, {"$set": {"linked_series_id": series_id}})


async def _generate_screenplay_lampo(title: str, genre: str, content_type: str, preplot: str, num_episodes: int = 0) -> dict:
    """Generate concise screenplay/synopsis text + extract 1-3 sub-genres + (optional) AI-generated episodes via Emergent LLM (gpt-4o-mini).

    Returns: {"screenplay": str, "subgenres": list[str], "episodes": [{title, synopsis}, ...]}
    """
    import os, json, re
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return {"screenplay": "", "subgenres": [], "episodes": []}
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        ct_label = {"film": "film", "tv_series": "serie TV", "anime": "anime"}.get(content_type, "film")
        wants_episodes = (num_episodes or 0) > 0 and content_type in ("tv_series", "anime")
        chat = LlmChat(
            api_key=key,
            session_id=f"lampo-screenplay-{uuid.uuid4()}",
            system_message=(
                "Sei uno sceneggiatore italiano fedele. La tua REGOLA ASSOLUTA è rispettare ESATTAMENTE "
                "la pretrama del produttore: chi fa cosa, chi ama chi, chi uccide chi, ruoli, generi (M/F), "
                "moventi e relazioni. NON invertire MAI i ruoli. NON inventare fatti non presenti. "
                "Se la pretrama dice 'Lei deve uccidere Lui', allora nella sceneggiatura DEVE essere lei "
                "incaricata di ucciderlo, mai il contrario. Rispondi SEMPRE e SOLO con un oggetto JSON "
                "valido, senza markdown, senza testo extra prima o dopo."
            ),
        ).with_model("openai", "gpt-4o-mini")

        # Costruisce dinamicamente la struttura JSON richiesta
        episodes_block = ""
        if wants_episodes:
            n = max(1, min(26, int(num_episodes or 10)))
            episodes_block = (
                f',\n "episodes": [\n'
                f'    {{"title": "<titolo unico ep.1, max 4 parole, italiano, evocativo>", "synopsis": "<mini-trama ep.1 in italiano: 1-2 frasi che descrivono cosa succede>"}},\n'
                f"    ... (esattamente {n} episodi totali, NUMERATI 1..{n}, ciascuno con titolo unico e mini-trama coerente con la sceneggiatura)\n"
                f'  ]'
            )

        prompt = (
            f'TIPO: {ct_label} {genre}\n'
            f'TITOLO: "{title}"\n'
            + (f'NUMERO EPISODI: {num_episodes}\n' if wants_episodes else '')
            + f'PRETRAMA DEL PRODUTTORE (DA RISPETTARE LETTERALMENTE):\n"""\n{preplot}\n"""\n\n'
            f"Restituisci ESATTAMENTE un JSON con questa struttura:\n"
            f'{{"screenplay": "<sceneggiatura sintetica max 350 parole in italiano: logline, conflitto, '
            f'4-5 punti chiave di trama, climax, risoluzione, atmosfera. Paragrafi brevi separati da \\n>",\n'
            f' "subgenres": ["sotto-genere1", "sotto-genere2", "sotto-genere3"]{episodes_block}\n'
            f'}}\n\n'
            f"REGOLE TASSATIVE per la sceneggiatura:\n"
            f"1. RILEGGI la pretrama 2 volte prima di scrivere. Identifica: protagonista, antagonista, "
            f"vittima/e, persone amate, chi compie l'azione e chi la subisce.\n"
            f"2. NON invertire i ruoli (es. se 'lei deve uccidere lui', NON scrivere 'lui deve uccidere lei').\n"
            f"3. NON cambiare i nomi dei personaggi né il loro genere.\n"
            f"4. NON aggiungere personaggi non menzionati a meno che non siano comparse generiche.\n"
            f"5. La logline deve riassumere FEDELMENTE il conflitto della pretrama.\n\n"
            f"REGOLE per i sotto-generi:\n"
            f"- Estrai 1-3 sotto-generi pertinenti analizzando la pretrama (es: 'thriller psicologico', "
            f"'distopico', 'noir', 'survival', 'commedia romantica', 'coming of age', 'mystery', 'satirico', "
            f"'spionaggio', 'soprannaturale', 'biografico', 'guerra', 'storico', 'cyberpunk', "
            f"'mecha', 'isekai', 'slice of life', 'sport', 'musicale', 'epico', ecc.).\n"
            f"- Tutti in italiano, minuscoli, max 3 parole ciascuno.\n"
            f"- NON ripetere il genere principale '{genre}'.\n"
            f"- Devono essere coerenti con la pretrama, non generici."
            + (
                "\n\nREGOLE per gli episodi:\n"
                f"- Esattamente {num_episodes} episodi.\n"
                "- TITOLI: ognuno UNICO (mai ripetere lo stesso titolo), evocativi, max 4 parole, in italiano. "
                "Niente 'Episodio N' come titolo.\n"
                "- SINOSSI: 1-2 frasi che descrivono COSA SUCCEDE in quell'episodio specifico, coerente "
                "con l'arco narrativo della sceneggiatura. Mai generiche tipo 'nuove alleanze, vecchi rancori'.\n"
                "- Gli episodi devono raccontare un arco progressivo: setup → escalation → climax → risoluzione."
                if wants_episodes else ""
            )
        )
        resp = await chat.send_message(UserMessage(text=prompt))
        raw = (resp or "").strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        try:
            data = json.loads(raw)
        except Exception:
            # Fallback: try to find a JSON block
            m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            data = json.loads(m.group(0)) if m else {}
        screenplay = (data.get("screenplay") or "").strip()
        subs = data.get("subgenres") or []
        if not isinstance(subs, list):
            subs = []
        # Sanitize subgenres
        cleaned = []
        for s in subs[:5]:
            if not isinstance(s, str):
                continue
            s2 = s.strip().lower()
            if not s2 or s2 == (genre or "").lower():
                continue
            s2 = " ".join(s2.split()[:3])[:30]
            if s2 and s2 not in cleaned:
                cleaned.append(s2)
            if len(cleaned) >= 3:
                break
        # Sanitize episodes
        episodes_out = []
        if wants_episodes:
            ep_raw = data.get("episodes") or []
            if isinstance(ep_raw, list):
                seen_titles = set()
                for i, ep in enumerate(ep_raw[:num_episodes]):
                    if not isinstance(ep, dict):
                        continue
                    t = (ep.get("title") or "").strip()
                    syn = (ep.get("synopsis") or "").strip()
                    # dedup titles (case-insensitive)
                    tl = t.lower()
                    if tl in seen_titles or not t:
                        t = f"Capitolo {i + 1}"
                    seen_titles.add(t.lower())
                    episodes_out.append({
                        "title": t,
                        "synopsis": syn or f"Episodio {i + 1}",
                    })
        return {"screenplay": screenplay, "subgenres": cleaned, "episodes": episodes_out}
    except Exception as e:
        logger.warning(f"LAMPO screenplay+subgenres+episodes gen failed: {e}")
        return {"screenplay": "", "subgenres": [], "episodes": []}


def _random_episode_minitrama(ep_num: int, genre: str) -> str:
    templates = [
        f"Episodio {ep_num}: i protagonisti affrontano una svolta inaspettata.",
        f"Episodio {ep_num}: un segreto del passato viene a galla.",
        f"Episodio {ep_num}: nuove alleanze, vecchi rancori.",
        f"Episodio {ep_num}: una scelta che cambierà tutto.",
        f"Episodio {ep_num}: un incontro decisivo scuote il gruppo.",
        f"Episodio {ep_num}: tra verità e inganno, qualcuno paga il prezzo.",
    ]
    return random.choice(templates)


async def _worker_generate(pid: str):
    """Background worker: 2-min AI generation pipeline (poster + screenplay + cast + CWSv + episodes)."""
    try:
        steps = [
            (5,   "Analizzo la pretrama…"),
            (15,  "AI scrive la sceneggiatura…"),
            (28,  "Casting automatico…"),
            (40,  "Genero la locandina…"),
            (52,  "Scelgo le location…"),
            (62,  "Definisco attrezzature e troupe…"),
            (72,  "Sponsor e marketing…"),
            (82,  "Montaggio finale…"),
            (92,  "Valutazione CWSv…"),
            (100, "Completato!"),
        ]
        step_sleep = DURATION_SECONDS / len(steps)

        # Avvia generazioni AI in parallelo (poster + sceneggiatura)
        proj = await db.lampo_projects.find_one({"id": pid}, {"_id": 0})
        if not proj:
            return

        screenplay_task = asyncio.create_task(
            _generate_screenplay_lampo(
                proj["title"], proj["genre"], proj["content_type"], proj["preplot"],
                num_episodes=int(proj.get("num_episodes") or 0) if proj["content_type"] in ("tv_series", "anime") else 0,
            )
        )
        poster_task = asyncio.create_task(
            _generate_poster_lampo(proj["title"], proj["genre"], proj["content_type"], pid)
        )

        for pct, msg in steps:
            await asyncio.sleep(step_sleep)
            await db.lampo_projects.update_one(
                {"id": pid},
                {"$set": {"progress_pct": pct, "progress_message": msg, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )

        # Wait for parallel AI tasks (with safety timeout)
        try:
            screenplay_data = await asyncio.wait_for(screenplay_task, timeout=20)
        except Exception:
            screenplay_data = {"screenplay": "", "subgenres": [], "episodes": []}
        screenplay_text = (screenplay_data or {}).get("screenplay") or ""
        subgenres = (screenplay_data or {}).get("subgenres") or []
        ai_episodes = (screenplay_data or {}).get("episodes") or []
        try:
            poster_url = await asyncio.wait_for(poster_task, timeout=15)
        except Exception:
            poster_url = ""

        # Studio level for CWSv calculation
        studio_key = "production_studio" if proj["content_type"] == "film" else (
            "studio_anime" if proj["content_type"] == "anime" else "studio_serie_tv"
        )
        studio_doc = await db.infrastructure.find_one(
            {"owner_id": proj["user_id"], "type": studio_key}, {"_id": 0, "level": 1}
        )
        studio_level = (studio_doc or {}).get("level", 1) if studio_key != "production_studio" else max(1, (studio_doc or {}).get("level", 1))

        cwsv = _cwsv_for_studio_level(studio_level, proj["budget_tier"])

        cast = await _pick_random_cast(
            proj["content_type"], studio_level, num_actors=5,
            budget_tier=proj.get("budget_tier", "mid"), cwsv=cwsv,
            genre=proj.get("genre", "")
        )

        # LAMPO auto-include: sostituisci fino a 2 attori NPC con attori
        # del roster del player (scuola/agenzia) se disponibili. Costo 0
        # e badge "is_own_roster" → bonus CWSv/XP automatici al rilascio.
        try:
            own_pool = []
            agency_actors_doc = await db.agency_actors.find(
                {"user_id": proj["user_id"]}, {"_id": 0}
            ).limit(20).to_list(20)
            for a in agency_actors_doc:
                own_pool.append({**a, "_own_source": "agency"})
            school_students = await db.casting_school_students.find(
                {"user_id": proj["user_id"], "status": {"$in": ["training", "max_potential"]}},
                {"_id": 0}
            ).limit(20).to_list(20)
            for s in school_students:
                own_pool.append({**s, "_own_source": "school"})
            # Step 3 — Pre-engaged actors injected con priorità (max 2 garantiti)
            pre_engs = await db.talent_pre_engagements.find(
                {"user_id": proj["user_id"], "role": "actor",
                 "contract_status": {"$in": ["active", "threatened"]}},
                {"_id": 0}
            ).limit(20).to_list(20)
            pre_pool = []
            for e in pre_engs:
                snap = e.get("npc_snapshot", {}) or {}
                # Enrich da people se snapshot sparso
                if not snap.get("skills"):
                    try:
                        full = await db.people.find_one({"id": e.get("npc_id")}, {"_id": 0})
                        if full:
                            snap = {**full, **snap}
                    except Exception:
                        pass
                pre_pool.append({
                    **snap,
                    "id": e.get("npc_id"),
                    "_own_source": "pre_engaged",
                    "_pre_engage_id": e.get("id"),
                })

            if cast.get("actors") and (own_pool or pre_pool):
                import random as _rnd2
                actor_slots = len(cast["actors"])
                used_idx = set()
                # 1. Pre-engaged hanno priorità: max 2, prima del random own pool
                k_pre = min(2, len(pre_pool), actor_slots)
                pre_pick = _rnd2.sample(pre_pool, k_pre) if k_pre > 0 else []
                for ow in pre_pick:
                    # Trova primo slot non usato
                    i = next((idx for idx in range(actor_slots) if idx not in used_idx), None)
                    if i is None:
                        break
                    used_idx.add(i)
                    char_role = cast["actors"][i].get("character_role")
                    enriched = {
                        **ow,
                        "id": ow.get("id"),
                        "name": ow.get("name", "?"),
                        "stars": ow.get("stars", 2),
                        "gender": ow.get("gender", ""),
                        "gender_label": "M" if str(ow.get("gender", "")).lower().startswith("m") else "F",
                        "role_type": "anime_illustrator" if (proj["content_type"] == "anime" or (proj.get("genre") or "").lower() == "animation") else "actor",
                        "role_label": "Disegnatore" if (proj["content_type"] == "anime" or (proj.get("genre") or "").lower() == "animation") else "Attore",
                        "skills": ow.get("skills", {}),
                        "fame_score": ow.get("fame_score", 30),
                        "score": 65 + (ow.get("stars", 2) * 4),
                        "is_guest_star": False,
                        "is_own_roster": True,
                        "own_source": "pre_engaged",
                        "is_agency_actor": True,
                        "is_pre_engaged": True,
                        "pre_engage_id": ow.get("_pre_engage_id"),
                    }
                    if char_role:
                        enriched["character_role"] = char_role
                    cast["actors"][i] = enriched
                # 2. Owned (agency/school) per riempire i restanti slot, max 2 totali
                remaining_own_slots = max(0, 2 - k_pre)
                if remaining_own_slots > 0 and own_pool:
                    k_own = min(remaining_own_slots, len(own_pool), actor_slots - len(used_idx))
                    own_pick = _rnd2.sample(own_pool, k_own) if k_own > 0 else []
                    for ow in own_pick:
                        i = next((idx for idx in range(actor_slots) if idx not in used_idx), None)
                        if i is None:
                            break
                        used_idx.add(i)
                        char_role = cast["actors"][i].get("character_role")
                        enriched = {
                            **ow,
                            "id": ow.get("id"),
                            "name": ow.get("name", "?"),
                            "stars": ow.get("stars", 2),
                            "gender": ow.get("gender", ""),
                            "gender_label": "M" if str(ow.get("gender", "")).lower().startswith("m") else "F",
                            "role_type": "anime_illustrator" if (proj["content_type"] == "anime" or (proj.get("genre") or "").lower() == "animation") else "actor",
                            "role_label": "Disegnatore" if (proj["content_type"] == "anime" or (proj.get("genre") or "").lower() == "animation") else "Attore",
                            "skills": ow.get("skills", {}),
                            "fame_score": ow.get("fame_score", 30),
                            "score": 60 + (ow.get("stars", 2) * 4),
                            "is_guest_star": False,
                            "is_own_roster": True,
                            "own_source": ow.get("_own_source", "agency"),
                            "is_agency_actor": True,
                        }
                        if char_role:
                            enriched["character_role"] = char_role
                        cast["actors"][i] = enriched

            # 3. Pre-engaged registi/sceneggiatori/compositori auto-assegnati se disponibili (no agency_actors equivalente)
            for role_key, cast_field in [("director", "director"), ("screenwriter", "screenwriter"), ("composer", "composer")]:
                try:
                    eng_role = await db.talent_pre_engagements.find_one(
                        {"user_id": proj["user_id"], "role": role_key,
                         "contract_status": {"$in": ["active", "threatened"]}},
                        {"_id": 0}
                    )
                    if not eng_role:
                        continue
                    snap = eng_role.get("npc_snapshot", {}) or {}
                    if not snap.get("skills"):
                        full = await db.people.find_one({"id": eng_role.get("npc_id")}, {"_id": 0})
                        if full:
                            snap = {**full, **snap}
                    enriched = {
                        **snap,
                        "id": eng_role.get("npc_id"),
                        "name": snap.get("name", "?"),
                        "stars": eng_role.get("npc_stars", 2),
                        "gender": snap.get("gender", ""),
                        "skills": snap.get("skills", {}),
                        "fame_score": snap.get("fame_score", 30),
                        "is_own_roster": True,
                        "own_source": "pre_engaged",
                        "is_pre_engaged": True,
                        "pre_engage_id": eng_role.get("id"),
                    }
                    cast[cast_field] = enriched
                except Exception as _e_role:
                    logger.warning(f"LAMPO pre-engaged {role_key} fail pid={pid}: {_e_role}")
        except Exception as _own_err:
            logger.warning(f"LAMPO own-roster injection fail pid={pid}: {_own_err}")

        # Distribuzione automatica (solo film — serie/anime usano il loro flow TV)
        distribution_plan = None
        if proj["content_type"] == "film":
            try:
                from utils.lampo_distribution import build_lampo_distribution
                distribution_plan = await build_lampo_distribution(db)
            except Exception as dist_err:
                logger.warning(f"LAMPO distribution plan fail pid={pid}: {dist_err}")

        # Episodes per serie/anime — usa AI se disponibili, altrimenti fallback templates
        episodes = []
        if proj["content_type"] in ("tv_series", "anime"):
            num_ep = max(1, min(26, int(proj.get("num_episodes") or 10)))
            base_duration = 50 if proj["content_type"] == "tv_series" else 24
            for i in range(1, num_ep + 1):
                # Preferisci episodio AI se presente per questo indice
                ai_ep = ai_episodes[i - 1] if (i - 1) < len(ai_episodes) else None
                if ai_ep and (ai_ep.get("title") or ai_ep.get("synopsis")):
                    ep_title = (ai_ep.get("title") or f"Capitolo {i}").strip()
                    ep_synopsis = (ai_ep.get("synopsis") or _random_episode_minitrama(i, proj["genre"])).strip()
                else:
                    ep_title = f"Capitolo {i}"
                    ep_synopsis = _random_episode_minitrama(i, proj["genre"])
                episodes.append({
                    "episode_number": i,
                    "title": ep_title,
                    "synopsis": ep_synopsis,
                    "duration_minutes": base_duration + random.randint(-3, 7),
                })

        # Sponsor list (più ricca per budget alti)
        sponsor_pool_low = ["StudioPartner"]
        sponsor_pool_mid = ["CineBrand", "StudioPartner", "MovieMag"]
        sponsor_pool_high = ["CineBrand", "StudioPartner", "MovieMag", "PopcornCo", "VisualFX Inc"]
        if proj["budget_tier"] == "high":
            sponsors = random.sample(sponsor_pool_high, k=min(4, len(sponsor_pool_high)))
        elif proj["budget_tier"] == "mid":
            sponsors = random.sample(sponsor_pool_mid, k=min(3, len(sponsor_pool_mid)))
        else:
            sponsors = sponsor_pool_low[:]

        await db.lampo_projects.update_one(
            {"id": pid},
            {"$set": {
                "progress_pct": 100,
                "progress_message": "Pronto!",
                "status": "ready",
                "cast": cast,
                "cwsv": cwsv,
                "poster_url": poster_url or "",
                "screenplay": screenplay_text or "",
                "subgenres": subgenres or [],
                "episodes": episodes,
                "marketing_tier": "high" if proj["budget_tier"] == "high" else ("mid" if proj["budget_tier"] == "mid" else "low"),
                "sponsors": sponsors,
                "equipment_tier": proj["budget_tier"],
                "distribution_plan": distribution_plan,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }}
        )

        # ⚡ Insert "lampo_ready" stub into films/tv_series so drafts appear in standard dashboards
        # Status: lampo_ready → frontend mostra "A breve al cinema" / "A breve in TV"
        try:
            await _insert_lampo_ready_stub(pid, proj, cast, cwsv, poster_url, screenplay_text, episodes, sponsors, distribution_plan, subgenres)
        except Exception as stub_err:
            logger.warning(f"LAMPO ready stub insert failed pid={pid}: {stub_err}")
    except Exception as e:
        logger.error(f"LAMPO worker error pid={pid}: {e}")
        await db.lampo_projects.update_one(
            {"id": pid},
            {"$set": {"status": "error", "progress_message": f"Errore: {str(e)[:100]}"}}
        )


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.post("/start")
async def start_lampo(req: StartLampoRequest, user: dict = Depends(get_current_user)):
    """Avvia una produzione LAMPO. Blocca subito i fondi, parte il worker in background."""
    # Studio quota gating (stessa logica di pipeline normale)
    studio_type = "production_studio" if req.content_type == "film" else (
        "studio_anime" if req.content_type == "anime" else "studio_serie_tv"
    )
    await check_studio_quota(db, user["id"], studio_type, mode="lampo")

    # Funds check (con economy scaling)
    base_cost = BUDGET_COSTS[req.content_type][req.budget_tier]
    base_cp = BUDGET_CP[req.content_type][req.budget_tier]
    try:
        from utils.economy_scaling import compute_scaling_bundle
        bundle = compute_scaling_bundle(user, source="production", budget_tier=req.budget_tier)
        scaled_cost = max(0, int(round(base_cost * bundle["multiplier"])))
    except Exception:
        scaled_cost = base_cost

    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "funds": 1, "cinepass": 1})
    if (user_doc or {}).get("funds", 0) < scaled_cost:
        raise HTTPException(400, f"Fondi insufficienti: servono ${scaled_cost:,}")
    if (user_doc or {}).get("cinepass", 0) < base_cp:
        raise HTTPException(400, f"CinePass insufficienti: servono {base_cp} CP")

    # Deduct
    if scaled_cost or base_cp:
        await db.users.update_one(
            {"id": user["id"]},
            {"$inc": {"funds": -scaled_cost, "cinepass": -base_cp}}
        )

    pid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    # Content filter + auto VM
    from utils.content_filter import censor_text
    title_safe = censor_text(req.title.strip())
    preplot_safe = censor_text(req.preplot.strip())
    genre_l = (req.genre or "").lower()
    auto_vm = "vm16" if genre_l == "erotic" else ("vm14" if genre_l == "horror" else None)
    vm_rating = req.vm_rating or auto_vm
    doc = {
        "id": pid,
        "user_id": user["id"],
        "mode": "lampo",
        "content_type": req.content_type,
        "title": title_safe,
        "genre": req.genre,
        "subgenre": req.subgenre,
        "preplot": preplot_safe,
        "vm_rating": vm_rating,
        "budget_tier": req.budget_tier,
        "base_cost": base_cost,
        "paid_cost": scaled_cost,
        "paid_cp": base_cp,
        "num_episodes": req.num_episodes if req.content_type != "film" else None,
        "target_tv_station_id": req.target_tv_station_id,
        "status": "generating",
        "progress_pct": 0,
        "progress_message": "Avvio produzione LAMPO…",
        "created_at": now,
        "updated_at": now,
        "cast": None,
        "cwsv": None,
        "poster_url": None,
        "episodes": [],
        "released": False,
    }
    await db.lampo_projects.insert_one(doc)

    # Start background worker
    asyncio.create_task(_worker_generate(pid))

    doc.pop("_id", None)
    return {"success": True, "project": doc, "scaled_cost": scaled_cost}


@router.get("/{pid}/progress")
async def get_lampo_progress(pid: str, user: dict = Depends(get_current_user)):
    doc = await db.lampo_projects.find_one({"id": pid, "user_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Progetto LAMPO non trovato")
    return doc


@router.get("/mine")
async def get_my_lampo_projects(user: dict = Depends(get_current_user)):
    """Lista progetti LAMPO dell'utente (ready da rilasciare + in generazione)."""
    docs = await db.lampo_projects.find(
        {"user_id": user["id"], "released": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    return {"projects": docs}


# ─── Autosave bozza form (richiesta utente) ─────────────────────────
class LampoDraftFormReq(BaseModel):
    content_type: Literal["film", "tv_series", "anime"]
    title: Optional[str] = ""
    genre: Optional[str] = None
    subgenre: Optional[str] = None
    preplot: Optional[str] = ""
    budget_tier: Optional[Literal["low", "mid", "high"]] = "mid"
    num_episodes: Optional[int] = None
    target_tv_station_id: Optional[str] = None


@router.post("/draft-form")
async def save_lampo_draft_form(req: LampoDraftFormReq, user: dict = Depends(get_current_user)):
    """Salva la bozza del form LAMPO (autosave dal momento in cui si scrive il titolo).

    Una bozza per (user_id, content_type). Sopravvive a refresh / chiusure pagina.
    """
    now = datetime.now(timezone.utc).isoformat()
    payload = req.model_dump()
    payload["user_id"] = user["id"]
    payload["updated_at"] = now
    await db.lampo_form_drafts.update_one(
        {"user_id": user["id"], "content_type": req.content_type},
        {"$set": payload, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return {"success": True, "draft": payload}


@router.get("/draft-form")
async def get_lampo_draft_form(
    content_type: Literal["film", "tv_series", "anime"],
    user: dict = Depends(get_current_user),
):
    """Recupera l'ultima bozza del form LAMPO per il content_type indicato."""
    doc = await db.lampo_form_drafts.find_one(
        {"user_id": user["id"], "content_type": content_type}, {"_id": 0}
    )
    return {"draft": doc}


@router.delete("/draft-form")
async def delete_lampo_draft_form(
    content_type: Literal["film", "tv_series", "anime"],
    user: dict = Depends(get_current_user),
):
    """Elimina la bozza dopo che la produzione è stata avviata."""
    await db.lampo_form_drafts.delete_one(
        {"user_id": user["id"], "content_type": content_type}
    )
    return {"success": True}


async def _upsert_lampo_film(film_doc: dict) -> str:
    pid = film_doc.get("source_project_id")
    existing = await db.films.find_one({"source_project_id": pid}, {"_id": 0, "id": 1}) if pid else None
    if existing:
        fid = existing["id"]
        film_doc["id"] = fid
        # Don't overwrite created_at on update
        film_doc.pop("created_at", None)
        await db.films.update_one({"id": fid}, {"$set": film_doc})
        return fid
    await db.films.insert_one(film_doc)
    return film_doc["id"]


async def _upsert_lampo_series(series_doc: dict) -> str:
    pid = series_doc.get("source_project_id")
    existing = await db.tv_series.find_one({"source_project_id": pid}, {"_id": 0, "id": 1}) if pid else None
    if existing:
        sid = existing["id"]
        series_doc["id"] = sid
        series_doc.pop("created_at", None)
        await db.tv_series.update_one({"id": sid}, {"$set": series_doc})
        return sid
    await db.tv_series.insert_one(series_doc)
    return series_doc["id"]


@router.post("/{pid}/release")
async def release_lampo(
    pid: str,
    payload: dict = None,
    user: dict = Depends(get_current_user),
):
    """Rilascia il progetto LAMPO con timing.

    Body:
      release_in_hours: int  (0=immediato, 6/12/18, 24*1/2/4/6/8, oppure custom)
      release_at: ISO str opzionale (sovrascrive release_in_hours, formato '2026-04-30T20:00:00Z')

    Comportamenti:
      • Immediato (release_in_hours <= 0): inserisce film/serie con status finale (in_theaters / in_tv) e ritorna release_event.
      • Programmato: inserisce film/serie con status di "lampo_scheduled" + released_at futuro + hype_bonus
        invisibile (1.18-1.32, leggermente superiore al sistema classico). Lo scheduler lo finalizzerà.
    """
    payload = payload or {}
    proj = await db.lampo_projects.find_one({"id": pid, "user_id": user["id"]}, {"_id": 0})
    if not proj:
        raise HTTPException(404, "Progetto non trovato")
    if proj.get("status") != "ready":
        raise HTTPException(400, "Il progetto non è ancora pronto")
    if proj.get("released"):
        raise HTTPException(400, "Già rilasciato")

    # ─── SAGA: gate rilascio (cap. precedente fuori sala) ───
    try:
        from utils.saga_release_hook import check_saga_release_gate
        ok_saga, reason_saga = await check_saga_release_gate(proj, user["id"])
        if not ok_saga:
            raise HTTPException(400, reason_saga)
    except HTTPException:
        raise
    except Exception:
        pass

    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    ct = proj["content_type"]

    # ── Calcola data di rilascio ──
    release_in_hours = int(payload.get("release_in_hours") or 0)
    release_at_str = payload.get("release_at")
    if release_at_str:
        try:
            release_dt = datetime.fromisoformat(str(release_at_str).replace("Z", "+00:00"))
            if release_dt.tzinfo is None:
                release_dt = release_dt.replace(tzinfo=timezone.utc)
        except Exception:
            raise HTTPException(400, "Formato release_at non valido (usa ISO 8601)")
    elif release_in_hours > 0:
        release_dt = now_dt + timedelta(hours=release_in_hours)
    else:
        release_dt = now_dt

    is_scheduled = release_dt > now_dt + timedelta(minutes=2)

    # ─── Theater duration (FILM only) — 5-45 giorni in base a qualità/budget/cast/random ───
    def _calc_theater_days() -> int:
        import random as _rnd
        cwsv = float(proj.get("cwsv") or 5.0)  # 0-10
        budget_mod = {"low": 0, "mid": 4, "high": 9}.get(proj.get("budget_tier", "mid"), 4)
        cast_actors = (proj.get("cast") or {}).get("actors") or []
        cast_stars = sum(int(a.get("stars") or a.get("popularity") or 0) for a in cast_actors)
        cast_mod = min(8, cast_stars // 2)
        # base = qualità * 3 → 0-30 giorni
        base = cwsv * 3
        rnd_mod = _rnd.randint(-3, 6)
        days = int(base + budget_mod + cast_mod + rnd_mod)
        return max(5, min(45, days))

    theater_days = _calc_theater_days() if ct == "film" else None
    theater_weeks_val = max(1, round(theater_days / 7)) if theater_days else None

    # Hype bonus invisibile (silenzioso) — leggermente > del sistema classico (1.10-1.20)
    # per dare valore alla scelta di posticipare. Più tempo aspetti, più hype maturi.
    hype_bonus = 1.0
    if is_scheduled:
        hours = max(1.0, (release_dt - now_dt).total_seconds() / 3600.0)
        # 6h → +18%, 24h → +24%, 48h → +28%, 96h → +30%, 192h (8gg) → +32%
        # Curva soft-cap: 1 + 0.10 * log2(hours) clamp 1.18..1.32
        import math
        boost = 0.10 * math.log2(hours)
        hype_bonus = max(1.18, min(1.32, 1.0 + boost))

    # ───────────────── FILM ─────────────────
    if ct == "film":
        film_id = str(uuid.uuid4())
        if is_scheduled:
            # Stub coming-soon LAMPO. Nessun release_event ora — lo scheduler lo genererà.
            film_doc = {
                "id": film_id,
                "user_id": user["id"],
                "pipeline_version": 3,
                "source_project_id": pid,
                "mode": "lampo",
                "is_lampo": True,
                "lampo_scheduled": True,
                "lampo_hype_bonus": round(hype_bonus, 3),
                "title": proj["title"],
                "genre": proj["genre"],
                "subgenre": proj.get("subgenre"),
                "subgenres": proj.get("subgenres", []),
                "preplot": proj["preplot"],
                "screenplay": proj.get("screenplay", ""),
                "synopsis": proj.get("screenplay", "") or proj.get("preplot", ""),
                "poster_url": proj.get("poster_url", ""),
                "cast": proj.get("cast", {}),
                "quality_score": proj.get("cwsv"),
                "cwsv": proj.get("cwsv"),
                "status": "lampo_scheduled",
                "prossimamente": True,
                "released_at": release_dt.isoformat(),
                "scheduled_release_at": release_dt.isoformat(),
                "created_at": now,
                "total_revenue": 0,
                "virtual_likes": 0,
                "marketing_tier": proj.get("marketing_tier", "mid"),
                "budget_tier": proj.get("budget_tier"),
                "sponsors": proj.get("sponsors", []),
                "equipment_tier": proj.get("equipment_tier"),
                "attendance_trend": [],
                "theater_days": theater_days,
                "theater_weeks": theater_weeks_val,
                "distribution_scope": (proj.get("distribution_plan") or {}).get("scope_label"),
                "distribution_bucket": (proj.get("distribution_plan") or {}).get("bucket"),
                "release_continents": (proj.get("distribution_plan") or {}).get("continents", []),
                "release_countries": (proj.get("distribution_plan") or {}).get("countries", []),
                "release_cities": (proj.get("distribution_plan") or {}).get("cities", []),
                "worldwide": bool((proj.get("distribution_plan") or {}).get("mondo", False)),
                "release_event": None,
                # SAGA flags (pre-inserted so scheduler can finalize correctly)
                "saga_id": proj.get("saga_id"),
                "saga_chapter_number": proj.get("saga_chapter_number"),
                "saga_subtitle": proj.get("saga_subtitle", ""),
                "is_saga_chapter": bool(proj.get("saga_id")),
                "is_saga_first": bool(proj.get("is_saga_first")),
                "saga_cliffhanger": bool(proj.get("saga_cliffhanger")),
            }
            film_id = await _upsert_lampo_film(film_doc)
            await db.lampo_projects.update_one(
                {"id": pid},
                {"$set": {"released": True, "released_film_id": film_id, "scheduled_release_at": release_dt.isoformat(), "updated_at": now}}
            )
            return {
                "success": True, "type": "film", "released_id": film_id, "scheduled": True,
                "release_at": release_dt.isoformat(),
                "theater_days": theater_days,
                "message": f"'{proj['title']}' uscirà nei cinema il {release_dt.strftime('%d/%m/%Y %H:%M')} UTC.",
            }

        # Immediato — release_event + XP
        release_event = None
        xp_event_bonus = 0
        try:
            from routes.film_pipeline import generate_release_event
            release_event = generate_release_event(
                {"title": proj["title"]}, proj.get("cast", {}),
                int(round(float(proj.get("cwsv") or 5) * 10)),
                proj["genre"]
            )
            if release_event:
                ev_id = release_event.get("id", "")
                XP_EVENT_BONUS = {
                    "cultural_phenomenon": 300, "surprise_hit": 150, "critics_rave": 120,
                    "award_buzz": 100, "cult_following": 80, "soundtrack_charts": 40,
                    "public_flop": 30, "polarizing": 20, "scandal": 15, "controversy": 15,
                }
                xp_event_bonus = XP_EVENT_BONUS.get(ev_id, 10)
        except Exception:
            pass

        film_doc = {
            "id": film_id,
            "user_id": user["id"],
            "pipeline_version": 3,
            "source_project_id": pid,
            "mode": "lampo",
            "is_lampo": True,
            "title": proj["title"],
            "genre": proj["genre"],
            "subgenre": proj.get("subgenre"),
            "subgenres": proj.get("subgenres", []),
            "preplot": proj["preplot"],
            "screenplay": proj.get("screenplay", ""),
            "synopsis": proj.get("screenplay", "") or proj.get("preplot", ""),
            "poster_url": proj.get("poster_url", ""),
            "cast": proj.get("cast", {}),
            "quality_score": proj.get("cwsv"),
            "cwsv": proj.get("cwsv"),
            "status": "in_theaters",
            "released_at": now,
            "created_at": now,
            "total_revenue": 0,
            "virtual_likes": 0,
            "marketing_tier": proj.get("marketing_tier", "mid"),
            "budget_tier": proj.get("budget_tier"),
            "sponsors": proj.get("sponsors", []),
            "equipment_tier": proj.get("equipment_tier"),
            "attendance_trend": [],
            "theater_days": theater_days,
            "theater_weeks": theater_weeks_val,
            "distribution_scope": (proj.get("distribution_plan") or {}).get("scope_label"),
            "distribution_bucket": (proj.get("distribution_plan") or {}).get("bucket"),
            "release_continents": (proj.get("distribution_plan") or {}).get("continents", []),
            "release_countries": (proj.get("distribution_plan") or {}).get("countries", []),
            "release_cities": (proj.get("distribution_plan") or {}).get("cities", []),
            "worldwide": bool((proj.get("distribution_plan") or {}).get("mondo", False)),
            "release_event": release_event,
        }
        film_id = await _upsert_lampo_film(film_doc)
        try:
            base_xp = int((proj.get("cwsv") or 5) * 10)
            total_xp = base_xp + xp_event_bonus
            await db.users.update_one({"id": user["id"]}, {"$inc": {"total_xp": total_xp, "xp": total_xp}})
        except Exception:
            pass
        await db.lampo_projects.update_one(
            {"id": pid},
            {"$set": {"released": True, "released_film_id": film_id, "release_event": release_event, "updated_at": now}}
        )

        # ─── SAGA: propaga metadati + fan-base + post-release update ───
        saga_bonuses = {"trilogy_bonus": 0, "saga_concluded": False}
        if proj.get("saga_id"):
            try:
                from utils.saga_release_hook import (
                    attach_saga_metadata, apply_fan_base_hype_modifier, post_release_update_saga,
                )
                attach_saga_metadata(film_doc, proj)
                await db.films.update_one(
                    {"id": film_id},
                    {"$set": {
                        "saga_id": film_doc.get("saga_id"),
                        "saga_chapter_number": film_doc.get("saga_chapter_number"),
                        "saga_subtitle": film_doc.get("saga_subtitle", ""),
                        "is_saga_chapter": True,
                        "is_saga_first": film_doc.get("is_saga_first", False),
                        "saga_cliffhanger": film_doc.get("saga_cliffhanger", False),
                    }}
                )
                # Per LAMPO immediate: opening_day_revenue è in cwsv-driven, ma non sempre presente; calcoliamo se manca
                film_doc["user_id"] = user["id"]
                new_open = await apply_fan_base_hype_modifier(film_doc, proj)
                if film_doc.get("saga_fan_base_modifier"):
                    await db.films.update_one(
                        {"id": film_id},
                        {"$set": {
                            "opening_day_revenue": new_open,
                            "saga_fan_base_modifier": film_doc.get("saga_fan_base_modifier"),
                            "saga_prev_cwsv": film_doc.get("saga_prev_cwsv"),
                        }}
                    )
                film_doc["id"] = film_id
                saga_bonuses = await post_release_update_saga(film_doc, proj, user["id"])
            except Exception:
                pass

        ev_label = (release_event or {}).get("name", "")
        msg = f"'{proj['title']}' è al cinema!" + (f" Evento: {ev_label}" if ev_label else "")
        return {"success": True, "type": "film", "released_id": film_id, "scheduled": False, "theater_days": theater_days, "message": msg, "release_event": release_event, "xp_gained": xp_event_bonus + int((proj.get('cwsv') or 5) * 10), "saga_bonuses": saga_bonuses}

    # ───────────────── tv_series / anime ─────────────────
    target_station_id = proj.get("target_tv_station_id")
    if target_station_id:
        st = await db.tv_stations.find_one({"id": target_station_id, "user_id": user["id"]}, {"_id": 0, "id": 1})
        if not st:
            target_station_id = None
    if not target_station_id:
        st = await db.tv_stations.find_one({"user_id": user["id"]}, {"_id": 0, "id": 1}, sort=[("created_at", 1)])
        if st:
            target_station_id = st["id"]

    in_tv = bool(target_station_id)
    series_id = str(uuid.uuid4())
    series_doc = {
        "id": series_id,
        "source_project_id": pid,
        "user_id": user["id"],
        "pipeline_version": 3,
        "mode": "lampo",
        "is_lampo": True,
        "type": ct,
        "title": proj["title"],
        "genre": proj["genre"],
        "genre_name": proj["genre"],
        "subgenres": proj.get("subgenres", []),
        "preplot": proj["preplot"],
        "screenplay": proj.get("screenplay", ""),
        "synopsis": proj.get("screenplay", "") or proj.get("preplot", ""),
        "poster_url": proj.get("poster_url", ""),
        "cast": proj.get("cast", {}),
        "episodes": proj.get("episodes", []),
        "num_episodes": len(proj.get("episodes", [])),
        "total_episodes": len(proj.get("episodes", [])),
        "season_number": 1,
        "scheduled_for_tv_station": target_station_id,
        "target_tv_station_id": target_station_id,
        "tv_schedule_accepted_at": None,
        "quality_score": proj.get("cwsv"),
        "cwsv": proj.get("cwsv"),
        "created_at": now,
        "total_revenue": 0,
    }

    if is_scheduled:
        series_doc.update({
            "status": "lampo_scheduled",
            "lampo_scheduled": True,
            "lampo_hype_bonus": round(hype_bonus, 3),
            "prossimamente_tv": True,
            "scheduled_for_tv": True,
            "released_at": release_dt.isoformat(),
            "scheduled_release_at": release_dt.isoformat(),
        })
        series_id = await _upsert_lampo_series(series_doc)
        await db.lampo_projects.update_one(
            {"id": pid},
            {"$set": {"released": True, "released_series_id": series_id, "scheduled_release_at": release_dt.isoformat(), "updated_at": now}}
        )
        return {
            "success": True, "type": ct, "released_id": series_id, "scheduled": True,
            "release_at": release_dt.isoformat(), "in_tv": in_tv,
            "message": f"'{proj['title']}' arriverà in TV il {release_dt.strftime('%d/%m/%Y %H:%M')} UTC.",
        }

    # Immediato serie/anime
    series_doc.update({
        "status": "in_tv" if in_tv else "catalog",
        "prossimamente_tv": in_tv,
        "scheduled_for_tv": in_tv,
        "released_at": now,
    })
    series_id = await _upsert_lampo_series(series_doc)
    try:
        base_xp = int((proj.get("cwsv") or 5) * 8)
        series_event = None
        roll = random.random()
        cwsv_val = float(proj.get("cwsv") or 5)
        if cwsv_val < 4.0 and roll < 0.30:
            series_event = {"id": "series_flop", "name": "Flop Clamoroso", "type": "negative", "xp": 40}
        elif cwsv_val >= 8.0 and roll < 0.25:
            series_event = {"id": "series_phenomenon", "name": "Fenomeno Streaming", "type": "positive", "xp": 250}
        elif roll < 0.08:
            series_event = {"id": "series_cult", "name": "Serie Cult", "type": "neutral", "xp": 100}
        event_xp = (series_event or {}).get("xp", 0)
        total_xp = base_xp + event_xp
        await db.users.update_one({"id": user["id"]}, {"$inc": {"total_xp": total_xp, "xp": total_xp}})
        if series_event:
            await db.tv_series.update_one({"id": series_id}, {"$set": {"release_event": series_event}})
    except Exception:
        series_event = None
    await db.lampo_projects.update_one({"id": pid}, {"$set": {"released": True, "released_series_id": series_id, "updated_at": now}})
    msg = f"'{proj['title']}' in arrivo su TV!" if in_tv else f"'{proj['title']}' aggiunto al tuo catalogo."
    if series_event:
        msg += f" Evento: {series_event['name']}"
    return {"success": True, "type": ct, "released_id": series_id, "scheduled": False, "in_tv": in_tv, "message": msg, "release_event": series_event}


@router.post("/{pid}/discard")
async def discard_lampo(pid: str, user: dict = Depends(get_current_user)):
    """Scarta un progetto LAMPO prima del rilascio (no refund). Rimuove anche eventuali stub bozza/schedulati."""
    proj = await db.lampo_projects.find_one({"id": pid, "user_id": user["id"]}, {"_id": 0})
    if not proj:
        raise HTTPException(404, "Progetto non trovato")
    # Rimuovi qualsiasi stub LAMPO non ancora finalizzato (lampo_ready / lampo_scheduled)
    await db.films.delete_many({"source_project_id": pid, "status": {"$in": ["lampo_ready", "lampo_scheduled"]}})
    await db.tv_series.delete_many({"source_project_id": pid, "status": {"$in": ["lampo_ready", "lampo_scheduled"]}})
    await db.lampo_projects.update_one(
        {"id": pid, "user_id": user["id"]},
        {"$set": {"status": "discarded", "released": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"success": True}


# ═══════════════════════════════════════════════════════════════
# Scheduler finalizer — esposto per essere chiamato dallo scheduler globale
# ═══════════════════════════════════════════════════════════════

async def finalize_scheduled_lampo_releases():
    """Trova film/serie LAMPO con status='lampo_scheduled' e released_at <= now e li promuove a in_theaters/in_tv.
    Applica il hype bonus invisibile (boost a virtual_likes e marketing_tier) e genera release_event.
    Chiamato periodicamente dal scheduler APS."""
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()

    # ─── Films ───
    pending_films = await db.films.find(
        {"status": "lampo_scheduled", "is_lampo": True},
        {"_id": 0}
    ).to_list(200)
    for film in pending_films:
        try:
            ra = film.get("scheduled_release_at") or film.get("released_at")
            if not ra:
                continue
            rdt = datetime.fromisoformat(str(ra).replace("Z", "+00:00"))
            if rdt.tzinfo is None:
                rdt = rdt.replace(tzinfo=timezone.utc)
            if rdt > now_dt:
                continue  # not yet
            release_event = None
            xp_event_bonus = 0
            try:
                from routes.film_pipeline import generate_release_event
                release_event = generate_release_event(
                    {"title": film["title"]}, film.get("cast", {}),
                    int(round(float(film.get("cwsv") or 5) * 10)),
                    film["genre"]
                )
                if release_event:
                    XP_EVENT_BONUS = {
                        "cultural_phenomenon": 300, "surprise_hit": 150, "critics_rave": 120,
                        "award_buzz": 100, "cult_following": 80, "soundtrack_charts": 40,
                        "public_flop": 30, "polarizing": 20, "scandal": 15, "controversy": 15,
                    }
                    xp_event_bonus = XP_EVENT_BONUS.get(release_event.get("id", ""), 10)
            except Exception:
                pass
            hype = film.get("lampo_hype_bonus", 1.0) or 1.0
            initial_likes = int(50 * hype)  # boost iniziale invisibile
            # Backfill theater_days/theater_weeks se mancanti (LAMPO pre-feature default 10g)
            existing_td = film.get("theater_days")
            theater_days_fix = existing_td if existing_td else 10
            theater_weeks_fix = max(1, round(theater_days_fix / 7))
            await db.films.update_one(
                {"id": film["id"]},
                {"$set": {
                    "status": "in_theaters",
                    "prossimamente": False,
                    "released_at": now,
                    "release_event": release_event,
                    "lampo_finalized_at": now,
                    "theater_days": theater_days_fix,
                    "theater_weeks": theater_weeks_fix,
                }, "$inc": {"virtual_likes": initial_likes}}
            )

            # ─── SAGA: post-release update se questo film è capitolo di una saga ───
            if film.get("saga_id"):
                try:
                    from utils.saga_release_hook import apply_fan_base_hype_modifier, post_release_update_saga
                    proj_stub = {
                        "saga_id": film["saga_id"],
                        "saga_chapter_number": film.get("saga_chapter_number"),
                        "saga_subtitle": film.get("saga_subtitle", ""),
                        "is_saga_first": film.get("is_saga_first", False),
                        "saga_cliffhanger": film.get("saga_cliffhanger", False),
                        "user_id": film["user_id"],
                    }
                    new_open = await apply_fan_base_hype_modifier(film, proj_stub)
                    if film.get("saga_fan_base_modifier"):
                        await db.films.update_one(
                            {"id": film["id"]},
                            {"$set": {
                                "opening_day_revenue": new_open,
                                "saga_fan_base_modifier": film.get("saga_fan_base_modifier"),
                                "saga_prev_cwsv": film.get("saga_prev_cwsv"),
                            }}
                        )
                    await post_release_update_saga(film, proj_stub, film["user_id"])
                except Exception as _e_saga:
                    pass
            base_xp = int((film.get("cwsv") or 5) * 10)
            total_xp = base_xp + xp_event_bonus
            await db.users.update_one(
                {"id": film["user_id"]}, {"$inc": {"total_xp": total_xp, "xp": total_xp}}
            )
            # Notifica al giocatore
            try:
                from social_system import create_notification
                notif = create_notification(
                    film["user_id"], "lampo_release",
                    "⚡ Il tuo film LAMPO è uscito!",
                    f"'{film['title']}' è ora al cinema. {('Evento: ' + release_event['name']) if release_event else ''}",
                    data={"film_id": film["id"]},
                    link=f"/films/{film['id']}"
                )
                await db.notifications.insert_one(notif)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error finalizing scheduled LAMPO film {film.get('id')}: {e}")

    # ─── Series / anime ───
    pending_series = await db.tv_series.find(
        {"status": "lampo_scheduled", "is_lampo": True},
        {"_id": 0}
    ).to_list(200)
    for s in pending_series:
        try:
            ra = s.get("scheduled_release_at") or s.get("released_at")
            if not ra:
                continue
            rdt = datetime.fromisoformat(str(ra).replace("Z", "+00:00"))
            if rdt.tzinfo is None:
                rdt = rdt.replace(tzinfo=timezone.utc)
            if rdt > now_dt:
                continue
            in_tv = bool(s.get("target_tv_station_id"))
            series_event = None
            roll = random.random()
            cwsv_val = float(s.get("cwsv") or 5)
            if cwsv_val < 4.0 and roll < 0.30:
                series_event = {"id": "series_flop", "name": "Flop Clamoroso", "type": "negative", "xp": 40}
            elif cwsv_val >= 8.0 and roll < 0.25:
                series_event = {"id": "series_phenomenon", "name": "Fenomeno Streaming", "type": "positive", "xp": 250}
            elif roll < 0.08:
                series_event = {"id": "series_cult", "name": "Serie Cult", "type": "neutral", "xp": 100}
            await db.tv_series.update_one(
                {"id": s["id"]},
                {"$set": {
                    "status": "in_tv" if in_tv else "catalog",
                    "prossimamente_tv": in_tv,
                    "released_at": now,
                    "release_event": series_event,
                    "lampo_finalized_at": now,
                }}
            )
            base_xp = int((s.get("cwsv") or 5) * 8)
            event_xp = (series_event or {}).get("xp", 0)
            await db.users.update_one(
                {"id": s["user_id"]}, {"$inc": {"total_xp": base_xp + event_xp, "xp": base_xp + event_xp}}
            )
            try:
                from social_system import create_notification
                notif = create_notification(
                    s["user_id"], "lampo_release",
                    "⚡ Il tuo " + ("anime" if s.get("type") == "anime" else "serie") + " LAMPO è uscito!",
                    f"'{s['title']}' è ora disponibile.",
                    data={"series_id": s["id"]},
                    link=f"/tv-series/{s['id']}"
                )
                await db.notifications.insert_one(notif)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error finalizing scheduled LAMPO series {s.get('id')}: {e}")
