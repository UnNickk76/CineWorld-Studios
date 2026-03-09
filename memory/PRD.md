# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

### Sessione 09/03/2025 - Festival Cinematografici

#### Sistema Festival (NUOVO)
- [x] **3 Festival ogni 10 giorni:**
  - **Golden Stars Awards** ⭐⭐⭐ (Voto Player) - +500 XP, +50 Fama, $100K
  - **Spotlight Awards** ⭐⭐ (AI) - +300 XP, +30 Fama, $50K  
  - **Cinema Excellence Awards** ⭐⭐ (AI) - +300 XP, +30 Fama, $50K

- [x] **10 Categorie Premio:**
  1. Miglior Film
  2. Miglior Regia
  3. Miglior Attore
  4. Miglior Attrice
  5. Miglior Attore Non Protagonista
  6. Miglior Attrice Non Protagonista
  7. Miglior Sceneggiatura
  8. Miglior Colonna Sonora
  9. Miglior Fotografia
  10. Premio del Pubblico

- [x] **Classifiche Premi:** Mensili, Annuali, Di Sempre
- [x] **Traduzioni complete** in 5 lingue (EN, IT, ES, FR, DE)

#### Altre Feature Completate
- [x] Compositore/Produttore Musicale (Step 6 wizard)
- [x] Colonna Sonora AI con prompt (Step 9 wizard)
- [x] Fix Trailer Video (4/8/12 sec - Sora 2)
- [x] Sistema Anteprime Esclusive
- [x] Pagina Crediti con Andreola Fabio e diritti riservati

### Wizard Creazione Film (12 Step)
1. Title, 2. Sponsor, 3. Equipment, 4. Writer, 5. Director, 
6. **Composer**, 7. Cast, 8. Script, 9. **Soundtrack**, 10. Poster, 11. Ads, 12. Review

### Funzionalità Core
- Sistema XP Esponenziale, Incassi Bilanciati, Voti Non Modificabili
- Tutorial 8 step, Credits, Notifiche, Riscossione Incassi
- Saghe/Sequel, Serie TV, Anime, Noleggio Film

## API Endpoints Festival

```
GET  /api/festivals                    - Lista 3 festival
GET  /api/festivals/{id}/current       - Edizione corrente con nominati
POST /api/festivals/vote               - Vota (solo Golden Stars)
POST /api/festivals/{edition_id}/finalize - Assegna premi
GET  /api/festivals/awards/leaderboard - Classifica premi
GET  /api/festivals/my-awards          - Premi vinti
```

## Backlog

### P1 - Prossime
- [ ] Mini-giochi Versus dalla chat
- [ ] UI Saghe/Serie TV

### P2 - Future
- [ ] Bonus trailer collegato agli incassi
- [ ] Evoluzione abilità cast

## 3rd Party Integrations
- OpenAI GPT-5.2 (Sceneggiature, Colonne sonore)
- Gemini Nano Banana (Avatar/Poster)
- Sora 2 (Trailer video)

## Test Reports
- `/app/test_reports/iteration_13.json` - 100% pass (21/21 backend, frontend OK)
