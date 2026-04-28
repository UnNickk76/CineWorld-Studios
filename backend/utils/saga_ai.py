"""
CineWorld Studio's — Saga AI (Continuity Engine)
================================================
Genera la pretrama del capitolo successivo coerente con:
  • La pretrama originale del player (capitolo 1)
  • Le pretrame AI dei capitoli precedenti
  • Il cliffhanger flag del capitolo precedente

Genera anche personaggi nuovi/coerenti per il capitolo successivo:
  • Mantiene i personaggi principali (protagonist/antagonist/coprotagonist)
  • Può introdurre 1-3 nuovi personaggi minor/supporting
  • Può rimuovere personaggi morti/usciti di scena
"""
from __future__ import annotations
import os
import json
import re
import uuid
import random
import logging
from typing import Optional

log = logging.getLogger(__name__)


def _parse_json_object(raw: str) -> dict:
    if not raw:
        return {}
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def _parse_json_list(raw: str) -> list[dict]:
    if not raw:
        return []
    m = re.search(r"\[[\s\S]*\]", raw)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


async def generate_next_chapter_pretrama(
    *,
    saga_title: str,
    genre: str,
    chapter_number: int,
    original_pretrama: str,
    previous_pretrames: list[str],
    previous_cliffhanger: bool = False,
) -> str:
    """
    Genera la pretrama del prossimo capitolo, coerente con tutta la storia precedente.
    Ritorna stringa di pretrama (~400-700 caratteri).
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            raise RuntimeError("Missing EMERGENT_LLM_KEY")

        # Costruisci storia precedente
        history_lines = [f"Capitolo 1 (originale del player):\n{original_pretrama[:1500]}"]
        for i, pt in enumerate(previous_pretrames, start=2):
            if pt:
                history_lines.append(f"Capitolo {i}:\n{pt[:800]}")
        history = "\n\n".join(history_lines)

        cliffhanger_note = (
            "\nIl capitolo precedente termina con un CLIFFHANGER aperto: "
            "la nuova pretrama deve riprendere subito da quel cliffhanger.\n"
            if previous_cliffhanger else ""
        )

        system_msg = (
            "Sei uno sceneggiatore italiano esperto di saghe cinematografiche. "
            "Generi pretrama coerenti che fanno avanzare la storia mantenendo i protagonisti, "
            "il tono e l'universo narrativo. Rispondi SOLO con la pretrama in italiano, "
            "nessun preambolo, nessun titolo."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"saga_{saga_title[:20]}_{chapter_number}_{random.randint(1000,9999)}",
            system_message=system_msg,
        )

        prompt = (
            f"Saga: «{saga_title}»\nGenere: {genre}\n\n"
            f"=== STORIA PRECEDENTE ===\n{history}\n{cliffhanger_note}\n"
            f"=== TASK ===\n"
            f"Scrivi la pretrama del CAPITOLO {chapter_number} di questa saga.\n"
            "Requisiti:\n"
            "- Lunghezza: 400-700 caratteri\n"
            "- Mantieni continuità con i protagonisti dei capitoli precedenti\n"
            "- Introduci un nuovo conflitto / tema / luogo coerente con il genere\n"
            "- Lascia spazio a tensione narrativa (non concludere tutto)\n"
            "- Stile narrativo, italiano, in terza persona\n\n"
            "Rispondi SOLO con la pretrama, nient'altro."
        )
        resp = await chat.send_message(UserMessage(text=prompt))
        text = (resp or "").strip()
        # Pulisci eventuali wrap markdown
        text = re.sub(r"^```[a-z]*\n?|```$", "", text, flags=re.MULTILINE).strip()
        if len(text) < 100:
            raise RuntimeError(f"AI returned too-short pretrama: {len(text)} chars")
        return text[:1200]
    except Exception as e:
        log.warning(f"[saga_ai.generate_next_chapter_pretrama] fallback: {e}")
        # Fallback deterministico
        return (
            f"Le vicende di «{saga_title}» proseguono nel capitolo {chapter_number}. "
            f"I protagonisti dei capitoli precedenti devono affrontare una nuova sfida che "
            f"mette in discussione tutto ciò che hanno costruito. Vecchi alleati tornano, "
            f"nuove minacce emergono, e il destino della storia si avvicina a una svolta cruciale."
        )


async def evolve_saga_characters(
    *,
    saga_title: str,
    genre: str,
    chapter_number: int,
    new_pretrama: str,
    previous_characters: list[dict],
) -> dict:
    """
    Date le pretrame e i personaggi precedenti, ritorna:
      {
        "kept": [...],          # personaggi principali mantenuti
        "added": [...],         # nuovi personaggi introdotti
        "removed": [...],       # personaggi rimossi/morti (con motivazione narrativa)
      }
    """
    # Mantieni sempre i personaggi principali (protagonist/antagonist/coprotagonist)
    main_chars = [c for c in (previous_characters or [])
                  if c.get("role_type") in ("protagonist", "antagonist", "coprotagonist")]

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            raise RuntimeError("Missing EMERGENT_LLM_KEY")

        chars_summary = "\n".join(
            f"- {c['name']} ({c.get('role_type')}, {c.get('age')}{c.get('gender','')}): {c.get('description','')[:80]}"
            for c in (previous_characters or [])[:20]
        )
        existing_names = [c.get("name") for c in (previous_characters or []) if c.get("name")]

        system_msg = (
            "Sei un casting director italiano. Ritorni SOLO JSON valido. "
            "Decidi l'evoluzione del cast personaggi tra un capitolo e il successivo di una saga."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"saga_chars_{saga_title[:15]}_{chapter_number}_{random.randint(1000,9999)}",
            system_message=system_msg,
        )
        prompt = (
            f"Saga: «{saga_title}» — Genere: {genre}\n\n"
            f"Personaggi del capitolo precedente:\n{chars_summary}\n\n"
            f"Pretrama capitolo {chapter_number}:\n{new_pretrama[:800]}\n\n"
            "Decidi:\n"
            "- 'added': 1-3 nuovi personaggi coerenti con la nuova pretrama\n"
            "- 'removed': 0-2 personaggi minori/supporting che escono di scena (mai protagonisti/antagonisti)\n"
            "- I personaggi principali (protagonist, antagonist, coprotagonist) NON vanno mai rimossi.\n\n"
            "Formato JSON:\n"
            "{\"added\":[{\"name\":\"...\",\"role_type\":\"supporting|minor\",\"age\":int,\"gender\":\"M|F|N\",\"description\":\"...\"}],"
            "\"removed\":[\"NomeEsistente\"]}\n\n"
            "Vincoli:\n"
            f"- Nomi nuovi: NON usare nomi già presenti: {', '.join(existing_names[:15])}\n"
            "- Età coerenti, descrizione 1 frase max 120 caratteri\n"
            "- Niente 'Luca'\n\n"
            "Ritorna SOLO JSON."
        )
        resp = await chat.send_message(UserMessage(text=prompt))
        data = _parse_json_object((resp or "").strip())

        added_raw = data.get("added", []) if isinstance(data, dict) else []
        removed_raw = data.get("removed", []) if isinstance(data, dict) else []

        # Normalizza added
        added = []
        for obj in (added_raw or [])[:3]:
            try:
                name = str(obj.get("name", "")).strip()[:60]
                if not name or name in existing_names:
                    continue
                rt = str(obj.get("role_type", "supporting")).strip().lower()
                if rt not in ("supporting", "minor"):
                    rt = "supporting"
                age = max(4, min(95, int(obj.get("age", 30))))
                gen = str(obj.get("gender", "N")).strip().upper()
                if gen not in ("M", "F", "N"):
                    gen = "N"
                added.append({
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "role_type": rt,
                    "age": age,
                    "gender": gen,
                    "description": str(obj.get("description", "")).strip()[:160],
                    "introduced_in_chapter": chapter_number,
                })
            except Exception:
                continue

        # Normalizza removed (mai rimuovere main chars)
        main_names = {c.get("name") for c in main_chars}
        removed = []
        for n in (removed_raw or [])[:2]:
            n = str(n).strip()
            if n and n in existing_names and n not in main_names:
                removed.append(n)

        kept = [c for c in (previous_characters or []) if c.get("name") not in removed]

        return {"kept": kept, "added": added, "removed": removed}

    except Exception as e:
        log.warning(f"[saga_ai.evolve_saga_characters] fallback: {e}")
        # Fallback: mantieni tutto, nessun cambio
        return {"kept": list(previous_characters or []), "added": [], "removed": []}
