# CineWorld Studio's — PRD

## Pipeline V3 Film — Completa
10 step sequenziali con CWSv. 14 file calcolo in `/app/backend/utils/calc_*.py`.

## Pipeline V3 Serie TV & Anime — Completa (16/04/2026)
9 step con CWSv serie, titoli episodi AI, CWSv per episodio, cliffhanger system.
Scheduling TV complesso: 4 politiche produttore + opzioni TV (ep per batch, intervallo, split stagione).

## CWSv System — 1.0-10
5 file film + 1 file serie. Pre-voto visibile ad ogni step. CWSv 9+ rarissimo.

## CWTrend System — Implementato
Score dinamico 1-10 che cambia nel tempo. File: `calc_cwtrend.py`.
Fattori: 40% CWSv + 15% marketing + 10% sponsor + 15% hype + 10% distribuzione + 10% tempo + casualità.
Nota: CWTrend può essere scarso anche per film ottimi e viceversa (è il "momento", non la qualità).

## ProducerProfileModal — Implementato
Modal profilo produttore con stats, filmografia, CWSv medio, badge livello.
Si apre cliccando "una produzione [Studio]" nel film detail.
Endpoint: `GET /api/players/{id}/profile` (evoluto con CWSv, serie, anime, filmografia).

## Sistema Scheduling TV Serie/Anime
### Dal produttore (release policy):
- 1 al giorno → TV non ha scelta
- 3 al giorno → TV sceglie 1/2/3 ep al giorno
- Due mezze stagioni → TV può split + scegliere ep/intervallo
- Tutta insieme → TV piena libertà (binge, split, programmazione custom)
### Dalla TV (entro limiti policy):
- EP per trasmissione: 1, 2, 3
- Intervallo: ogni 1, 2, 3 giorni
- Split stagione: sì/no + pausa 7/14/21/30 giorni

## Backlog
### P0
- Rinnovo Stagione (S2 da CWSv S1 ±10%)
- Sezione TV gestione: ricezione serie, configurazione programmazione, trasmissione episodi

### P1
- Prossimamente in Dashboard per serie/anime
- CWSv episodio revealed alla trasmissione

### P2
- Sfide settimanali, Festival, Concorrenza, Fase Market
