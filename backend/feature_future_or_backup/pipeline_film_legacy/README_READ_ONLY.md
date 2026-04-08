LEGACY BACKUP – DO NOT EDIT / DO NOT USE IN PRODUCTION.

# Pipeline Film Legacy Backup

Backup storico della pipeline film legacy. Non usare in produzione. Solo riferimento/recupero.

## Files
- `film_pipeline_legacy.py` — Route backend pipeline film originale
- `FilmPipeline_legacy.jsx` — Componente frontend pipeline film originale

## Flow Vecchio (Status)
draft → proposed → coming_soon → ready_for_casting → casting → sponsor → ciak → produzione → prima → uscita → completed/released

## Problemi Noti
- Status ambigui che causavano loop infiniti
- Frontend dipendente da status backend per UI step (incoerente)
- Film nel limbo (completati ma mai rilasciati nella collection films)
- Mancanza di snapshot/checkpoint → impossibile recovery
- Bottoni incoerenti con stato reale
- Sceneggiatura, pre-prod, ciak e remaster tutti dentro "produzione"
- Nessun sistema di lock anti-race-condition

## Sostituito da
Pipeline Film V2 (`/app/backend/routes/pipeline_v2.py` + `/app/frontend/src/pages/PipelineV2.jsx`)
