# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate - Sessione 09/03/2025

### 1. Reset Totale Player ✅
- Reset COMPLETO con doppia conferma (token 5 minuti)
- Elimina: Film, Infrastrutture, Premi, Voti, Chat, Notifiche
- Ripristina: $10M, Livello 1, 50 Fama, nuovo avatar
- Accessibile solo dal player stesso (Profilo)

### 2. Festival Ufficiali (3 ogni 10 giorni) ✅
- **Golden Stars Awards** ⭐⭐⭐ (Voto Player) - +500 XP, +50 Fama, $100K
- **Spotlight Awards** ⭐⭐ (AI) - +300 XP, +30 Fama, $50K
- **Cinema Excellence Awards** ⭐⭐ (AI) - +300 XP, +30 Fama, $50K
- 10 Categorie Premio
- Classifiche: Mensili, Annuali, Di Sempre

### 3. Festival Personalizzati (Player-Created) ✅
- **Requisiti:** Livello 20+ per creare, Livello 5+ per partecipare
- **Costo Creazione:** Esponenziale basato sul livello ($500K base × 1.15^(level-20))
- **Partecipazione:**
  - Creatore: max 1 film
  - Altri: max 10 film, costo esponenziale per film aggiuntivo
  - 30% del costo → immediato al creatore
  - 70% → montepremi
- **Categorie:** Scelta dal creatore tra 7 opzioni
- **Locandina AI:** Generabile con prompt personalizzato
- **Pubblicità:** Notifica giornale + notifica diretta a tutti i player
- **Cerimonia Live:** Il creatore può avviare la premiazione in diretta

### 4. Altre Feature Completate
- Compositore/Produttore Musicale (Step 6 wizard)
- Colonna Sonora AI con prompt (Step 9 wizard)
- Trailer Video 4/8/12 sec (Sora 2)
- Anteprime Esclusive
- Pagina Crediti con Andreola Fabio

## API Endpoints Nuovi

### Reset Player
```
POST /api/auth/reset/request   - Richiedi token reset (5 min validità)
POST /api/auth/reset/confirm   - Conferma reset con token
```

### Festival Personalizzati
```
GET  /api/custom-festivals                    - Lista festival attivi
GET  /api/custom-festivals/creation-cost      - Costo creazione
GET  /api/custom-festivals/{id}               - Dettagli festival
POST /api/custom-festivals/create             - Crea festival
POST /api/custom-festivals/participate        - Partecipa con film
POST /api/custom-festivals/{id}/vote          - Vota entry
POST /api/custom-festivals/{id}/start-ceremony - Avvia cerimonia live
POST /api/custom-festivals/{id}/award-winners  - Assegna premi
```

### Cerimonie Live
```
GET /api/ceremonies/active - Cerimonie in corso
```

## Backlog

### P1 - Prossime
- [ ] Mini-giochi Versus dalla chat
- [ ] UI Saghe/Serie TV

### P2 - Future
- [ ] Bonus trailer collegato agli incassi
- [ ] Evoluzione abilità cast

## Architettura
```
/app/
├── backend/server.py (6800+ righe)
├── frontend/src/App.js (5100+ righe)
└── memory/PRD.md
```

## 3rd Party Integrations
- OpenAI GPT-5.2, Gemini Nano Banana, Sora 2 (Emergent LLM Key)
