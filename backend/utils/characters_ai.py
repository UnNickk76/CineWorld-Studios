"""
AI Character Generator — genera lista personaggi (5-20) coerente con la trama/sceneggiatura.

Ogni personaggio ha: id, name, role_type, age, gender, description, importance.

role_type (ordine di importanza):
  - protagonist:    ruolo principale (1-2)
  - antagonist:     antagonista (0-2)
  - coprotagonist:  co-protagonista / spalla (0-3)
  - supporting:     ruoli di supporto (2-8)
  - minor:          figure minori, camei (0-5)

Matching età ↔ attore (logica client/server):
  - bambino (age <= 12): forbice ±3 anni
  - adolescente (12-17): forbice ±3 anni
  - adulto giovane (18-35): forbice ±8 anni
  - adulto (35-60): forbice ±10 anni
  - anziano (60+): forbice ±12 anni
"""
from __future__ import annotations
import os
import json
import re
import uuid
import logging
import random
from typing import Optional

log = logging.getLogger(__name__)


def age_tolerance_for(char_age: int) -> int:
    """Forbice anni ammessa per matching attore↔personaggio."""
    a = int(char_age or 30)
    if a <= 12:
        return 3
    if a <= 17:
        return 3
    if a <= 35:
        return 8
    if a <= 60:
        return 10
    return 12


def is_actor_compatible(char_age: int, actor_age: Optional[int]) -> bool:
    """True se l'attore può interpretare il personaggio per età."""
    if actor_age is None:
        return True  # attori senza età → tolleranti (fallback)
    tol = age_tolerance_for(char_age)
    return abs(int(actor_age) - int(char_age)) <= tol


ROLE_LABELS_IT = {
    "protagonist":   "Protagonista",
    "antagonist":    "Antagonista",
    "coprotagonist": "Co-protagonista",
    "supporting":    "Supporto",
    "minor":         "Minore",
}


def _fallback_characters(title: str, genre: str, count: int = 6) -> list[dict]:
    """Fallback deterministico in caso AI non disponibile."""
    names = [
        ("Marco Valenti", "M", 34), ("Elena Russo", "F", 29), ("Yuki Tanaka", "F", 27),
        ("Amir Khoury", "M", 41), ("Sven Eriksson", "M", 52), ("Nadia Popov", "F", 38),
        ("Zara Mendez", "F", 24), ("Kenji Morita", "M", 46), ("Sofia Lindqvist", "F", 19),
        ("Tiberio Marchetti", "M", 61), ("Leila Nasser", "F", 31), ("Hugo Laurent", "M", 44),
    ]
    importance_seq = ["protagonist", "antagonist", "coprotagonist",
                      "supporting", "supporting", "supporting", "minor", "minor"]
    chars = []
    for i in range(min(count, len(names))):
        name, gen, age = names[i]
        rt = importance_seq[i] if i < len(importance_seq) else "minor"
        chars.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "role_type": rt,
            "age": age,
            "gender": gen,
            "description": f"{ROLE_LABELS_IT[rt]} in {title}",
        })
    return chars


def _parse_json_list(raw: str) -> list[dict]:
    """Estrae una lista JSON da un testo che può contenere wrapper markdown."""
    if not raw:
        return []
    # Cerca primo blocco [ ... ]
    m = re.search(r"\[[\s\S]*\]", raw)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return data


async def generate_characters_ai(
    *,
    title: str,
    genre: str,
    subgenre: Optional[str],
    plot: str,
    content_kind: str = "film",  # 'film' | 'anime' | 'animation' | 'tv_series'
    desired_count: int = 8,
) -> list[dict]:
    """Chiede all'LLM una lista personaggi e la normalizza."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            raise RuntimeError("Missing EMERGENT_LLM_KEY")

        kind_label = {
            "film": "film live-action",
            "anime": "anime (serie animata giapponese)",
            "animation": "film d'animazione",
            "tv_series": "serie TV",
        }.get(content_kind, "opera audiovisiva")

        system_msg = (
            "Sei uno sceneggiatore e casting director italiano. Ritorni SOLO JSON valido "
            "(nessun testo fuori dall'array JSON). Generi cast di personaggi coerenti, "
            "con nomi variati (italiani, stranieri, poco comuni) e età realistiche."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"chars_{title[:20]}_{random.randint(1000,9999)}",
            system_message=system_msg,
        )

        cnt = max(5, min(20, int(desired_count)))
        prompt = (
            f"Genera {cnt} personaggi per un {kind_label}.\n"
            f"Titolo: {title}\nGenere: {genre}"
            + (f"\nSottogenere: {subgenre}" if subgenre else "")
            + f"\nTrama: {plot[:1200]}\n\n"
            "Regole:\n"
            f"- Esattamente {cnt} personaggi.\n"
            "- 1 protagonist, 1 antagonist (se il genere lo permette), 1-2 coprotagonist, "
            "il resto supporting o minor.\n"
            "- Nomi variati: italiani, stranieri, poco comuni. Niente 'Luca'.\n"
            "- Età coerenti con il ruolo (es. bambini solo per ruoli ad-hoc).\n"
            "- Descrizione in italiano, 1 frase massimo 120 caratteri.\n\n"
            "Formato: array JSON di oggetti con esattamente questi campi:\n"
            "[{\"name\":\"...\",\"role_type\":\"protagonist|antagonist|coprotagonist|supporting|minor\","
            "\"age\":int,\"gender\":\"M|F|N\",\"description\":\"...\"}]\n\n"
            "Ritorna SOLO l'array JSON, niente altro."
        )
        resp = await chat.send_message(UserMessage(text=prompt))
        raw = (resp or "").strip()
        data = _parse_json_list(raw)
        if not data:
            raise RuntimeError("AI returned no parseable JSON")

        out = []
        seen_names = set()
        for obj in data[:20]:
            try:
                name = str(obj.get("name", "")).strip()[:60]
                if not name or name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())
                rt = str(obj.get("role_type", "supporting")).strip().lower()
                if rt not in ROLE_LABELS_IT:
                    rt = "supporting"
                age = int(obj.get("age", 30))
                age = max(4, min(95, age))
                gen = str(obj.get("gender", "N")).strip().upper()
                if gen not in ("M", "F", "N"):
                    gen = "N"
                desc = str(obj.get("description", "")).strip()[:160]
                out.append({
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "role_type": rt,
                    "age": age,
                    "gender": gen,
                    "description": desc,
                })
            except Exception:
                continue

        # Garantisci almeno 1 protagonist
        if out and not any(c["role_type"] == "protagonist" for c in out):
            out[0]["role_type"] = "protagonist"

        if len(out) < 5:
            raise RuntimeError(f"AI returned only {len(out)} chars")

        return out
    except Exception as e:
        log.warning(f"[characters_ai] fallback due to: {e}")
        return _fallback_characters(title, genre, desired_count)
