# CineWorld Studio's — PRD

## Pipeline V3 Film — Completa
10 step, CWSv 1-10, 14 file calcolo.

## Pipeline V3 Serie TV & Anime — Completa
9 step, CWSv serie+episodi, titoli AI, cliffhanger, scheduling TV complesso.

## CWSv System
Film: 5 file (idea/hype/cast/production + quality.py). Serie: 1 file (quality_series.py).

## CWTrend System
Score dinamico 1-10. File: calc_cwtrend.py. Indipendente dalla qualità.

## Rinnovo Stagione — Implementato (16/04/2026)
- S2/S3/... creata da serie completata/in_tv/catalog
- CWSv base parte da S1 ±10%
- Lock 30 giorni reali prima del release
- Speedup CP: 15CP=dimezza(15g), 30CP=immediato
- Cast e poster ereditati dalla stagione precedente
- Endpoint: POST /api/pipeline-series-v3/series/{id}/renew-season

## Sezione TV — Implementata
- GET /tv/my-schedule: lista serie in TV con episodi trasmessi/totali
- POST /tv/broadcast-episode/{id}: trasmette prossimo episodio, rivela CWSv
- Tracking aired_count, next_episode, aired_at per episodio

## Prossimamente Dashboard — Implementato
- GET /prossimamente: serie in pipeline + serie in_tv con conteggio ep trasmessi
- Sezione "IN ARRIVO SU TV" nella Dashboard con poster, titolo, ep count
- Mostra sia serie in pipeline (coming soon) che serie in onda (airing)

## ProducerProfileModal — Implementato
Modal con stats produttore, filmografia, CWSv medio, badge.

## Scheduling TV Serie
4 politiche: 1/giorno, 3/giorno, 2 mezze stagioni, tutta insieme.
TV configura: ep per batch, intervallo giorni, split stagione con pausa.

## Backlog
### P0
- (nessuno — tutti P0 completati!)

### P1
- Bug "The Gratch" che ricompare dopo reset
- Sezione "La Mia TV" frontend completa (gestione serie ricevute)

### P2
- Sfide settimanali, Festival, Concorrenza
- Fase Market (film + serie + anime)
- Confronto produttori, Segui produttore, Medaglie
