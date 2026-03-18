# Emittente TV — Design Document

## Panoramica
L'Emittente TV è un'infrastruttura che i giocatori possono costruire per trasmettere Serie TV e Anime.
È il "cinema" delle serie: così come i film vanno nei cinema, le serie vanno sull'emittente.

---

## 1. INFRASTRUTTURA

### Livelli (1-10)
| Livello | Slot Palinsesto | Reach Audience | Costo Upgrade | Entrate Pubblicitarie |
|---------|-----------------|----------------|---------------|----------------------|
| 1       | 2 slot          | 100K spettatori | $500K        | x1.0                 |
| 2       | 3 slot          | 250K           | $1M           | x1.2                 |
| 3       | 4 slot          | 500K           | $2M           | x1.5                 |
| 4       | 5 slot          | 1M             | $4M           | x1.8                 |
| 5       | 6 slot          | 2.5M           | $8M           | x2.2                 |
| 6-10    | +1 per livello  | scaling        | scaling       | scaling              |

### Costo Costruzione
- $2M per costruire (livello 1)
- Requisiti: Livello 10 + almeno 1 serie TV completata

---

## 2. PALINSESTO (Programmazione)

### Fasce Orarie (3 fasce)
| Fascia       | Orario        | Audience Base | Costo Slot/Giorno | Note                          |
|-------------|---------------|---------------|-------------------|-------------------------------|
| **Daytime**     | 10:00-18:00   | x0.5          | $5,000            | Pubblico giovane/casalinghi  |
| **Prime Time**  | 20:00-23:00   | x1.5          | $15,000           | Massima audience              |
| **Late Night**  | 23:00-02:00   | x0.8          | $8,000            | Pubblico adulto/nicchia       |

### Come Funziona
1. Il giocatore **assegna una serie/anime a uno slot** del palinsesto
2. Ogni giorno di gioco, viene "trasmesso" un episodio della serie in quello slot
3. L'episodio genera **ascolti** basati su: qualità serie × fascia oraria × reach emittente × fattori random
4. Gli ascolti generano **entrate pubblicitarie**
5. Quando finiscono gli episodi della stagione, lo slot si libera

### Regole Palinsesto
- Una serie può occupare **un solo slot** alla volta
- Non si può trasmettere la stessa serie su due slot diversi
- Lo slot rimane occupato fino a fine stagione (o cancellazione manuale)
- Si possono mettere in coda serie successive per lo stesso slot (auto-programmazione)

---

## 3. ASCOLTI (Audience Rating System)

### Formula Ascolti per Episodio
```
base_audience = emittente_reach × fascia_multiplier
quality_factor = serie_quality / 100  (0.1 - 1.0)
episode_factor = episode_curve(episode_number, total_episodes)
competition_factor = 1.0 / (1 + competing_series_in_same_slot)
random_factor = gaussian(1.0, 0.15)  -- ±15% variazione

audience = base_audience × quality_factor × episode_factor × competition_factor × random_factor
```

### Curva Episodi (episode_curve)
- **Episodio 1 (Premiere):** x1.3 (curiosità)
- **Episodi 2-4:** x0.9 (calo fisiologico)
- **Episodi centrali:** x1.0 (stabilizzazione)
- **Penultimo:** x1.1 (build-up)
- **Finale di stagione:** x1.5 (evento)
- **Anime bonus:** I fan sono più fedeli, il calo è solo x0.95 invece di x0.9

### Share e Competizione
- Se DUE giocatori trasmettono alla stessa ora nella stessa fascia:
  - L'audience totale della fascia viene **divisa** proporzionalmente alla qualità
  - Serie con qualità 80 vs qualità 60: split 57% / 43%
- Questo crea competizione reale tra giocatori!

---

## 4. ENTRATE PUBBLICITARIE

### Formula Revenue per Episodio
```
ad_revenue = audience × CPM × emittente_ad_multiplier
```

| Fascia     | CPM (costo per 1000 spettatori) |
|-----------|--------------------------------|
| Daytime    | $2-4                           |
| Prime Time | $8-15                          |
| Late Night | $5-8                           |

### Sponsor Speciali (Futuro)
- Sponsor possono pagare per "sponsorizzare" uno slot specifico
- Revenue extra + bonus al brand dello sponsor

---

## 5. RINNOVO / CANCELLAZIONE

### Dopo ogni Stagione
In base alla **media ascolti della stagione**:
| Media Ascolti vs Reach | Risultato | Effetto |
|------------------------|-----------|---------|
| > 70%                  | **Hit!**  | +20% audience prossima stagione, bonus fama |
| 50-70%                 | **Buona** | Rinnovo normale |
| 30-50%                 | **Tiepida** | Il giocatore sceglie se rinnovare (costo aumentato) |
| < 30%                  | **Flop**  | Cancellazione forzata, malus fama |

### Longevità
- Stagione 1-3: nessun malus longevità
- Stagione 4-6: -5% audience per stagione (il pubblico si stanca)
- Stagione 7+: -10% per stagione (solo le serie eccezionali sopravvivono)

---

## 6. DB SCHEMA (Preparazione)

### Collection: `tv_broadcasts`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "emittente_id": "uuid",           // infrastruttura dell'emittente
  "series_id": "uuid",              // serie/anime in onda
  "season_number": 1,
  "timeslot": "prime_time",         // daytime, prime_time, late_night
  "slot_index": 0,                  // quale slot del palinsesto (0-based)
  "status": "in_onda",              // in_onda, completata, cancellata
  "current_episode": 3,
  "total_episodes": 10,
  "started_at": "ISO",
  "daily_cost": 15000,              // costo slot per giorno
  "episodes_aired": [
    {
      "episode_number": 1,
      "title": "Pilot - L'inizio",
      "mini_plot": "...",            // mini trama generata AI
      "audience": 450000,
      "ad_revenue": 5400,
      "aired_at": "ISO"
    }
  ]
}
```

### Campi da aggiungere a `series` (esistente)
```json
{
  "broadcast_status": "non_trasmessa",  // non_trasmessa, in_onda, conclusa
  "broadcast_channel": null,             // id dell'emittente che la trasmette
  "seasons": [
    {
      "season_number": 1,
      "episodes_count": 10,
      "quality_score": 72,
      "cast": { ... },
      "status": "completed",
      "average_audience": 380000
    }
  ]
}
```

### Campi infrastruttura `emittente_tv`
```json
{
  "type": "emittente_tv",
  "level": 1,
  "slots": [
    { "index": 0, "timeslot": "prime_time", "broadcast_id": "uuid_or_null" },
    { "index": 1, "timeslot": "daytime", "broadcast_id": null }
  ],
  "total_audience_reached": 0,
  "total_ad_revenue": 0
}
```

---

## 7. FLUSSO GIOCATORE

```
1. Costruisci Emittente TV ($2M)
2. Crea una Serie TV (pipeline completa per stagione)
3. Apri palinsesto → Scegli slot (Daytime/PrimeTime/LateNight)
4. Assegna serie allo slot
5. Ogni giorno:
   - Episodio trasmesso automaticamente
   - Mini-trama generata AI per l'episodio
   - Ascolti calcolati (con competizione altri giocatori)
   - Entrate pubblicitarie accreditate
6. Fine stagione → Rinnovo/Cancellazione
7. Se rinnovata → Nuova stagione (casting aggiornato, nuova sceneggiatura)
```

---

## 8. INTERAZIONE CON ALTRI SISTEMI

| Sistema | Interazione |
|---------|------------|
| **CineBoard** | Classifica "Serie più viste", "Anime più seguiti" |
| **Festival** | Premio "Miglior Serie dell'Anno" |
| **Social Feed** | "X ha iniziato a trasmettere Y su Prime Time!" |
| **Equipment** | Attrezzature migliorano qualità serie come per i film |
| **Sponsor** | Sponsor possono sponsorizzare slot specifici |
| **CinePass** | Velocizzare produzione stagione con crediti |
