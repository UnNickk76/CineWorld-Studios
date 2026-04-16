# CineWorld Studio's — PRD

## Pipeline V3 — Completa

### CWSv (CineWorld Studio's voto) — Implementato 16/04/2026
Il sistema di valutazione film in stile IMDb. Voto 1.0-10.0, voti X.0 mostrati senza decimale.

**File di calcolo (5 file dedicati):**
- `calc_quality_idea.py` — Step 0: Pre-voto base (titolo, genere, sotto-generi, ambientazione, pre-trama, poster, sceneggiatura, difficoltà genere, casualità) Range: 3.5-8.5
- `calc_quality_hype.py` — Step 1: Modifica ±5% (completamento hype, velocizzazioni malus probabilistico)
- `calc_quality_cast.py` — Step 2: Modifica ±12% (coerenza skill-genere regista/attori/compositore/sceneggiatori, chimica, fama)
- `calc_quality_production.py` — Steps 3+4+5: Modifica ±8% (formato-genere coerenza, comparse, CGI/VFX, velocizzazioni)
- `calc_quality.py` — Step 9: Voto finale CWSv (composizione step + bonus cura totale + malus velocizzazioni cumulative + fattore fortuna gaussiano ±15%)

**Regole chiave:**
- Pre-voti cambiano in percentuale, mai salti assoluti
- CWSv 9+ = rarissimo, richiede eccellenza reale
- CWSv 10 = quasi impossibile
- Step 6/7/8 non influenzano CWSv, alimentano futuro "voto Andamento"
- Pre-voto visibile nel badge header pipeline (al posto di "V3")
- CWSv visibile nella barra viola del film detail modal

### File Calcoli Dedicati (14 totali)
- `calc_shooting.py`, `calc_film_duration.py`, `calc_finalcut.py`, `calc_speedup.py`
- `calc_sponsors.py`, `calc_distribution.py`, `calc_defaults.py`, `calc_production_cost.py`
- `calc_adv.py`
- `calc_quality.py`, `calc_quality_idea.py`, `calc_quality_hype.py`, `calc_quality_cast.py`, `calc_quality_production.py`

### Film Detail V3 Modal (Post-Release)
Layout identico al V2 "The Gratch" (ContentTemplate.jsx) con CWSv nella barra viola.

## Backlog

### P0 - Alta Priorità
- Voto Andamento (dinamico, separato da CWSv): CWSv + fattori esterni (hype, marketing, sponsor, LaPrima, distribuzione, personalità città, concorrenza)
- Serie TV e Anime: stesso sistema CWSv con varianti (episodi, stagioni, binge vs settimanale)

### P1 - Media Priorità
- CinemaStatsModal + ProducerProfileModal con dati reali
- Fase 3 Mercato: vendite TV/Anime e diritti distribuzione
- Verifica casting: attori propri da agenzia acquistata visibili nel casting
- Miglioramento skill cast nel tempo (già esistente, da verificare)

### P2 - Bassa Priorità
- Ripetitività genere: malus saturazione mercato se stesso genere consecutivo
- Concorrenza in sala: fattore Andamento
- Sfide settimanali (minigame rotanti)
- Previsioni Festival e Marketplace diritti TV/Anime

## Promemoria
- Serie TV/Anime: stessa base CWSv ma con varianti
- Voto Andamento: sviluppo futuro basato su CWSv + fattori esterni
- Personalità città: influenza su Andamento
- Concorrenza in sala: fattore Andamento
