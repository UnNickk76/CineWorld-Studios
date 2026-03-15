# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), scuola di recitazione, sfide 1v1 e gestione infrastrutture.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), Emergent LLM Key

## Funzionalità Completate
- Acting School (reclutamento, formazione, graduazione)
- CinePass (valuta virtuale, login rewards, contest giornalieri)
- Notifiche interattive
- UI/UX (background, branding, nav mobile)
- Poster AI con titolo/genere
- Tutorial e release notes aggiornati
- **Step 1:** Ordinamento film dal più recente, icone genere colorate (rosa/blu)
- **Step 2:** Fix bug aggiunta film al cinema (calcolo schermi per livello)
- **Step 3:** Traduzione italiana completa (login, dashboard, film, profilo, backend errors, factors)
- **Step 4:** Costo CinePass per upgrade infrastrutture (esponenziale), +2 CinePass vittoria 1v1, limiti sfide (5/ora, 20/giorno)
- **Step 5:** Fix "Voci del Pubblico" (collection sbagliata), fix /catchup/process (datetime), ottimizzazione API (78MB→770KB), Major Studios funzionante
- **Step 6:** Indicatori skill attori, +15% presenze film propri, durata 1-4 settimane, estensione singola, traduzione fattori performance
- **Step 7 (v0.073):** Checkbox "Ricordami" (sessione 90gg), +1 CinePass rientro (1h), ultimo accesso lista giocatori, 10 contest giornalieri (50 CinePass), +20% ricavi infra/film, fix +2 CinePass 1v1
- **Step 8 (v0.074):** Cinema cliccabile -> popup distribuzione per paese, rimossa legenda CineBoard, costo festival ribilanciato (~$3M lv.67), festival creabile da qualsiasi livello, migrazione vecchi contest 3->10

## Task Prossimi (P2-P3)
- Tutorial popup per nuovi utenti
- CineCoins Purchase System (Stripe)
- Conversione PWA

## Bug Noti Risolti
- CinePass balance non aggiornato (Pydantic model duplicato)
- Film non aggiungibili al cinema (calcolo schermi ignorava livello)
- Voci dal Pubblico vuota (collection sbagliata)
- catchup/process errore datetime offset
- API responses 78MB (base64 poster data nei listing)
- Estensioni 3->1, max settimane 12->4
- Contest vecchi 3 non migravano ai nuovi 10 (fix migrazione automatica)
