# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), scuola di recitazione, sfide 1v1 e gestione infrastrutture.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), Emergent LLM Key

## Funzionalità Completate
- Acting School, CinePass, Notifiche, UI/UX, Poster AI, Tutorial, Release notes
- Step 1-6: Ordinamento film, fix cinema, traduzioni, costi CinePass, fix performance, indicatori skill
- Step 7 (v0.073): Rimani connesso, +1 CinePass rientro, ultimo accesso, 10 contest, +20% ricavi, +2 CinePass 1v1
- Step 8 (v0.074): Cinema cliccabile → popup distribuzione, legenda CineBoard rimossa, costo festival ribilanciato
- Step 9 (v0.075): Bilanciamento sfide 1v1 (probabilità esplicite), +2 CinePass visibile nel risultato, "UPSET"→"SORPRESA!", fix pareggi/vittorie ingiuste, ultimo accesso nella lista giocatori globale

## Bilanciamento Sfide (v0.075)
- Skill uguali (es. 1v1): ~80% pareggio
- 1 punto differenza (es. 6v5): ~55% pareggio, ~42% più forte vince
- 2 punti (es. 8v6): ~30% pareggio, ~65% più forte vince
- 3+ punti (es. 8v3): ~5% pareggio, ~92% più forte vince
- Upset (sorpresa): 2-8% chance

## Task Prossimi (P2-P3)
- Tutorial popup per nuovi utenti
- CineCoins Purchase System (Stripe)
- Conversione PWA

## Bug Noti Risolti
- CinePass +2 era assegnato nel DB ma non mostrato nel UI (fix: aggiunto display nel riepilogo vittoria)
- Pareggi con punteggi diversi (6v5 → pareggio) - fix: logica probabilistica
- Vittorie con punteggi uguali (1v1 → vittoria) - fix: 80% pareggio per skill uguali
- "UPSET" non tradotto → ora "SORPRESA!"
- Festival costava $356M a livello 67 → ora ~$3M
