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
- v0.073: Rimani connesso, +1 CinePass rientro, ultimo accesso, 10 contest, +20% ricavi, +2 CinePass 1v1
- v0.074: Cinema cliccabile → popup distribuzione, legenda CineBoard rimossa, costo festival ribilanciato
- v0.075: Bilanciamento sfide 1v1 (probabilità esplicite), +2 CinePass visibile nel risultato, "UPSET"→"SORPRESA!"
- v0.076: Sistema donazioni PayPal (pulsante fisso, menu, popup ad ogni accesso)
- v0.077: Pannello Admin (toggle donazioni, ruoli utente), tutorial 14 sezioni, ribilanciamento entrate (base +60%, bonus cinema multipli, +50% presenze)
- v0.078: Fix costo doppio CinePass per sceneggiature emergenti (acquisto sceneggiatura non addebita più 20 CinePass alla creazione film)

## Sistema Admin
- Solo NeoMorpheus ha accesso al pannello admin
- Toggle donazioni: attiva/disattiva da profilo
- Assegnazione ruoli: POST /api/admin/set-user-role (moderatore, VIP, tester)

## Bug Fix Recenti
- **Costo doppio CinePass:** L'acquisto di una sceneggiatura emergente (10 CP) + creazione film (20 CP) ora addebita solo i 10 CP dell'acquisto. Il create_film salta il costo se `emerging_screenplay_id` è presente.

## Task Prossimi (P0-P1)
- Verificare layout mobile pagina Contest (/games)
- Verifica utente premio +2 CinePass sfide 1v1 offline

## Task Futuri (P2-P3)
- Sistema ruoli Admin avanzato (moderatore, VIP, tester con poteri specifici)
- Tutorial popup per nuovi utenti (primo accesso)
- CineCoins Purchase System (Stripe)
- Conversione PWA
- Espansione ruoli admin (moderatore con poteri di chat, VIP con badge)
