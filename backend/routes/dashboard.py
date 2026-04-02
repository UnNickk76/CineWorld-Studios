# CineWorld Studio's - Dashboard / CineBoard / Release Notes / News Routes
# Cineboard rankings, release notes, cinema news, journal, leaderboard

import os
import uuid
import random
import logging
import time as _time
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import db
from auth_utils import get_current_user

router = APIRouter()


class TTLCache:
    def __init__(self):
        self._data = {}
    def get(self, key, ttl=30):
        entry = self._data.get(key)
        if entry and (_time.time() - entry[1]) < ttl:
            return entry[0]
        return None
    def set(self, key, value):
        self._data[key] = (value, _time.time())
    def invalidate(self, prefix=None):
        if prefix:
            self._data = {k: v for k, v in self._data.items() if not k.startswith(prefix)}
        else:
            self._data.clear()

_cache = TTLCache()

CREATOR_NICKNAME = "NeoMorpheus"



# ==================== CINEBOARD SCORE HELPER ====================

def calculate_cineboard_score(film: dict) -> float:
    """
    Calculate CineBoard score for a film based on multiple factors:
    - Quality: 30%
    - Revenue: 25%
    - Popularity (likes): 20%
    - Awards: 15%
    - Longevity: 10%
    """
    quality = film.get('quality_score', 0)
    revenue = film.get('total_revenue', 0)
    likes = film.get('likes_count', 0)
    awards_count = len(film.get('awards', []))
    
    quality_score = min(100, quality)
    revenue_score = min(100, (revenue / 10000000) * 100)
    likes_score = min(100, likes * 1)
    awards_score = min(100, awards_count * 25)
    weeks = film.get('actual_weeks_in_theater', film.get('weeks_in_theater', 1))
    longevity_score = min(100, weeks * 10)
    
    total_score = (
        quality_score * 0.30 +
        revenue_score * 0.25 +
        likes_score * 0.20 +
        awards_score * 0.15 +
        longevity_score * 0.10
    )
    
    return round(total_score, 2)


class NewReleaseNote(BaseModel):
    title: str
    changes: List[str]
    version: Optional[str] = None


# ==================== RELEASE NOTES DATA ====================

RELEASE_NOTES = [
    {'version': '0.153', 'date': '2026-03-19', 'title': 'Agenzia di Casting Personale',
     'changes': [
         {'type': 'new', 'text': 'Agenzia di Casting: recluta attori permanenti nella tua agenzia personale!'},
         {'type': 'new', 'text': 'Nome automatico: "[Il tuo Studio] Agency" con gestione slot per livello'},
         {'type': 'new', 'text': 'Livello 1: max 12 attori effettivi e 8 reclute settimanali (aumentano col livello)'},
         {'type': 'new', 'text': 'Ogni attore ha 2 generi forti e 1 genere adattabile visibili nel profilo'},
         {'type': 'new', 'text': 'Doppia scelta casting: "Dalla tua Agenzia" o "Dal Mercato" per Film, Serie TV e Anime'},
         {'type': 'new', 'text': 'Bonus XP/Fama esponenziale: 1 attore +25%, 2 +35%, 3 +50%, 4+ +70%'},
         {'type': 'new', 'text': 'Crescita graduale: gli attori migliorano dopo ogni film in base alla qualita'},
         {'type': 'new', 'text': 'Talento nascosto: ogni attore ha un cap su certe skill che puo non superare mai'},
         {'type': 'new', 'text': 'Licenziamento: attori licenziati tornano sul mercato globale per tutti'},
         {'type': 'new', 'text': 'Studenti scuola recitazione disponibili per il casting (continuano la formazione)'},
         {'type': 'new', 'text': 'Pulsante "Agenzia" nel menu Produci! per accesso rapido'},
     ]},
    {'version': '0.152', 'date': '2026-03-19', 'title': 'Fix Incassi, Poster Giornale & Score Dashboard',
     'changes': [
         {'type': 'fix', 'text': 'Fix critico: gli Incassi totali non calano piu dopo il ricalcolo dello scheduler'},
         {'type': 'fix', 'text': 'Fix Giornale del Cinema: le locandine dei film ora visibili (erano escluse dalla query)'},
         {'type': 'fix', 'text': 'Fix Dashboard: score Like, Social e Char ora mostrano i valori reali (non piu fissi a 50)'},
         {'type': 'improvement', 'text': 'Formula revenue: usa max(box_office_realistico, revenue_totale) per non diminuire mai'},
     ]},
    {'version': '0.150', 'date': '2026-03-18', 'title': 'CineBoard: Classifiche Emittenti TV',
     'changes': [
         {'type': 'new', 'text': 'Classifica "Emittenti Piu Viste": top emittenti per spettatori di sempre'},
         {'type': 'new', 'text': 'Classifica "Share Settimanale": top emittenti per share della settimana'},
         {'type': 'new', 'text': 'Classifica "Share Giornaliero": share live aggiornato ogni 5 minuti'},
         {'type': 'new', 'text': 'Sezione "Emittenti TV" nel popup CineBoard con 3 opzioni di classifica'},
         {'type': 'improvement', 'text': 'Tab rapidi nella pagina classifica per passare tra Di Sempre, Settimanale, Giornaliero'},
     ]},
    {'version': '0.149', 'date': '2026-03-18', 'title': 'Emittenti TV: Sistema Completo Netflix-Style',
     'changes': [
         {'type': 'new', 'text': 'Acquisto multiplo Emittenti TV: costi, livello e fama crescono esponenzialmente'},
         {'type': 'new', 'text': 'Setup Wizard: Step 1 (Nome permanente + Nazione), Step 2 (Pubblicita + Contenuti)'},
         {'type': 'new', 'text': 'Dashboard TV stile Netflix: sezioni Consigliati, Del Momento, I Piu Visti'},
         {'type': 'new', 'text': 'Gestione contenuti: file orizzontali scrollabili per Film, Serie TV, Anime'},
         {'type': 'new', 'text': 'Slider pubblicita: piu secondi = piu incasso ma meno share (modificabile)'},
         {'type': 'new', 'text': 'Film inseribili solo dopo uscita dal cinema'},
         {'type': 'new', 'text': 'Pagina pubblica "Emittenti TV" per vedere tutte le emittenti dei giocatori'},
         {'type': 'new', 'text': 'Tasto "Le Mie TV!" sulla Dashboard con popup lista stazioni'},
         {'type': 'new', 'text': 'Icona TV nella navbar inferiore per accedere alle emittenti'},
         {'type': 'new', 'text': 'Revenue system automatico ogni ora basato su qualita, share e volume contenuti'},
         {'type': 'improvement', 'text': 'Requisiti ridotti: Studio Serie TV -40%, Studio Anime -40%, Emittente TV -60%'},
     ]},
    {'version': '0.148', 'date': '2026-03-18', 'title': 'Fix CineBoard Popup Mobile',
     'changes': [
         {'type': 'bugfix', 'text': 'Popup CineBoard ora visibile correttamente su mobile (era tagliato fuori schermo)'},
         {'type': 'improvement', 'text': 'Popup CineBoard a tutta larghezza su mobile, dropdown classico su desktop'},
     ]},
    {'version': '0.147', 'date': '2026-03-18', 'title': 'Fix Sfide Online 1v1: Accettazione Sfide',
     'changes': [
         {'type': 'bugfix', 'text': 'Corretto il flusso di accettazione sfide online: popup porta alla selezione film'},
         {'type': 'bugfix', 'text': 'Pulsante "Unisciti" nelle sfide in attesa ora apre la selezione film'},
         {'type': 'bugfix', 'text': 'Notifica sfida dalla pagina Notifiche ora apre il flusso di accettazione'},
         {'type': 'new', 'text': 'Polling notifiche sfide ogni 30 secondi senza bisogno di refresh'},
         {'type': 'improvement', 'text': 'UI: banner "Sei stato sfidato!", pulsante "ACCETTA SFIDA!" differenziato'},
     ]},
    {'version': '0.146', 'date': '2026-03-18', 'title': 'Emittente TV Potenziata: Live Ratings & Storico Episodi',
     'changes': [
         {'type': 'new', 'text': 'Live Ratings: audience in tempo reale con aggiornamento automatico ogni 5 secondi'},
         {'type': 'new', 'text': 'Sparkline animata per ogni broadcast attivo'},
         {'type': 'new', 'text': 'Share % e indicatore trend (crescita/calo/stabile) per episodio'},
         {'type': 'new', 'text': 'Sistema Momentum: serie di qualita guadagnano pubblico episodio dopo episodio'},
         {'type': 'new', 'text': 'Storico Episodi: grafico a barre audience, dettaglio e analytics per episodio'},
         {'type': 'improvement', 'text': 'Banner LIVE con stats rete: Live Viewers, Ricavi Ads, Slot Attivi'},
     ]},
    {'version': '0.145', 'date': '2026-03-18', 'title': 'Dashboard Rinnovata: Ultimi Aggiornamenti & Sezioni Produzioni',
     'changes': [
         {'type': 'new', 'text': 'Sezione "Ultimi Aggiornamenti": 5 produzioni piu recenti di TUTTI i giocatori'},
         {'type': 'new', 'text': 'Sezione "Le Mie Serie TV": 5 locandine con link Vedi Tutti'},
         {'type': 'new', 'text': 'Sezione "I Miei Anime": 5 locandine con link Vedi Tutti'},
         {'type': 'improvement', 'text': '"I Miei Film" ottimizzati: 5 locandine in fila unica per mobile'},
         {'type': 'improvement', 'text': 'Rimossa sezione "Film in Attesa" per layout piu pulito'},
     ]},
    {'version': '0.144', 'date': '2026-03-18', 'title': 'Menu "I Miei Contenuti" & Visualizzazione Produzioni',
     'changes': [
         {'type': 'new', 'text': 'Popup "I Miei" nella navbar: Film, Serie TV, Anime in un menu'},
         {'type': 'new', 'text': 'Pagina I Miei Film ora visualizza Film, Serie TV o Anime tramite parametro URL'},
         {'type': 'improvement', 'text': 'Navigazione piu veloce tra le produzioni'},
     ]},
    {'version': '0.143', 'date': '2026-03-18', 'title': 'CineBoard Popup & Classifiche Trend Settimanali',
     'changes': [
         {'type': 'new', 'text': 'Popup CineBoard nella navbar superiore: Film, Serie TV, Anime'},
         {'type': 'new', 'text': 'Classifica Trend Settimanale per Serie TV'},
         {'type': 'new', 'text': 'Classifica Trend Settimanale per Anime'},
         {'type': 'improvement', 'text': 'Pagina CineBoard gestisce le nuove viste tramite parametro URL'},
     ]},
    {'version': '0.142', 'date': '2026-03-18', 'title': 'Emittente TV: Sistema Broadcasting',
     'changes': [
         {'type': 'new', 'text': 'Emittente TV sbloccabile nelle Infrastrutture (Livello 18, Fama 200, $5M)'},
         {'type': 'new', 'text': 'Palinsesto con 3 fasce: Daytime (x0.5), Prime Time (x1.5), Late Night (x0.8)'},
         {'type': 'new', 'text': 'Assegna serie completate agli slot e manda in onda episodi'},
         {'type': 'new', 'text': 'Ricavi pubblicitari automatici basati su audience e qualita'},
     ]},
    {'version': '0.141', 'date': '2026-03-18', 'title': 'Pipeline Anime Completa',
     'changes': [
         {'type': 'new', 'text': '8 generi anime: Shonen, Seinen, Shojo, Mecha, Isekai, Slice of Life, Horror, Fantasy'},
         {'type': 'new', 'text': 'Costi ridotti rispetto a Serie TV, tempi di produzione piu lunghi'},
         {'type': 'new', 'text': 'Pipeline completa: creazione, casting, sceneggiatura AI, produzione, release'},
         {'type': 'new', 'text': 'Integrazione completa con Emittente TV e CineBoard'},
     ]},
    {'version': '0.140', 'date': '2026-03-18', 'title': 'Pipeline Serie TV Completa',
     'changes': [
         {'type': 'new', 'text': '10 generi Serie TV: Drama, Comedy, Thriller, Sci-Fi, Fantasy, Horror, Romance, Crime, Medical, Legal'},
         {'type': 'new', 'text': 'Pipeline completa: creazione con numero episodi, casting, sceneggiatura AI'},
         {'type': 'new', 'text': 'Produzione episodi con tracking progresso e qualita'},
         {'type': 'new', 'text': 'Release e distribuzione con sistema audience'},
     ]},
    {'version': '0.139', 'date': '2026-03-18', 'title': 'Pipeline Sequel Completa',
     'changes': [
         {'type': 'new', 'text': 'Crea sequel dei tuoi film: eredita cast con sconto 30% sul cachet'},
         {'type': 'new', 'text': 'Bonus saga crescente: +5% (2o), +8% (3o), +12% (4o), +15% (5o+)'},
         {'type': 'new', 'text': 'Rischio fatigue: audience potrebbe calare se la qualita non regge'},
         {'type': 'new', 'text': 'Pipeline ridotta: salta le fasi gia completate nel film originale'},
     ]},
    {'version': '0.138', 'date': '2026-03-18', 'title': 'Menu Produci! Rinnovato a 5 Pulsanti',
     'changes': [
         {'type': 'new', 'text': 'Menu Produci! con 5 opzioni: Film, Sequel, Serie TV, Anime, La Tua TV'},
         {'type': 'new', 'text': 'Badge con conteggio studi sbloccabili'},
         {'type': 'new', 'text': 'Pulsanti bloccati/sbloccati in base alle infrastrutture possedute'},
         {'type': 'improvement', 'text': 'Card PRODUCI sulla Dashboard apre il menu produzione condiviso'},
     ]},
    {'version': '0.137', 'date': '2026-03-18', 'title': 'Navigazione Produzioni & Contesti Condivisi',
     'changes': [
         {'type': 'new', 'text': 'ProductionMenuContext: stato condiviso tra Dashboard e navbar per menu produzione'},
         {'type': 'new', 'text': 'Card "PRODUCI!" sulla Dashboard collegata al menu della navbar'},
         {'type': 'improvement', 'text': 'Navigazione fluida tra Dashboard e menu di produzione'},
     ]},
    {'version': '0.136', 'date': '2026-03-18', 'title': 'CineBoard Giornaliera/Settimanale & Sistema Sponsor',
     'changes': [
         {'type': 'new', 'text': 'CineBoard: nuove classifiche Giornaliera e Settimanale (sostituita Hall of Fame)'},
         {'type': 'new', 'text': 'Sistema Sponsor: fino a 6 sponsor per film, offrono denaro in cambio di % sugli incassi'},
         {'type': 'new', 'text': 'La fama degli sponsor aumenta l\'affluenza al cinema (non il punteggio IMDb)'},
         {'type': 'new', 'text': 'Nomi sponsor visibili nel popup di rilascio del film'},
         {'type': 'new', 'text': 'Sistema Equipment: ~10 pacchetti attrezzature (base/pro/premium) nella fase Casting'},
         {'type': 'improvement', 'text': 'CineBoard ora con 4 tab: In Sala, Giornaliera, Settimanale, Affluenze'},
     ]},
    {'version': '0.135', 'date': '2026-03-17', 'title': 'Casting Avanzato v2 & Locandine Personalizzabili',
     'changes': [
         {'type': 'new', 'text': 'Casting: dettagli arricchiti con genere, eta, nazionalita, fama, trend crescita'},
         {'type': 'new', 'text': 'Casting dinamico: proposte basate sulla fama del giocatore'},
         {'type': 'new', 'text': 'Locandine personalizzabili: AI da script, AI da prompt personalizzato, o template classici'},
         {'type': 'new', 'text': 'Rilascio film completo: poster AI, recensioni, punteggio IMDb, box office dettagliato'},
         {'type': 'fix', 'text': 'Fix acquisto sceneggiature: ora crea correttamente il progetto nella pipeline'},
         {'type': 'fix', 'text': 'Fix pulsante Scarta in tutte le fasi della pipeline'},
         {'type': 'fix', 'text': 'Fix selezione attori: rimosso limite errato a 1 attore'},
         {'type': 'fix', 'text': 'Fix calcolo IMDb: punteggio ora realistico (non sempre 10.0)'},
     ]},
    {'version': '0.134', 'date': '2026-03-17', 'title': 'Mercato Film & Marketplace Rinnovato',
     'changes': [
         {'type': 'new', 'text': 'Mercato Film: compra e vendi film scartati tra giocatori'},
         {'type': 'new', 'text': 'Card Mercato nella dashboard con accesso rapido'},
         {'type': 'new', 'text': 'Popup dettagli film nel marketplace con poster e statistiche'},
         {'type': 'improvement', 'text': 'Card Produci! ingrandita nella dashboard'},
         {'type': 'fix', 'text': 'Quiz Registi nel Contest ora funzionante'},
     ]},
    {'version': '0.133', 'date': '2026-03-17', 'title': 'Admin: Gestione Denaro & Riparazione Film',
     'changes': [
         {'type': 'new', 'text': 'Endpoint admin per aggiungere/rimuovere denaro ai giocatori'},
         {'type': 'new', 'text': 'Endpoint admin per riparare film incompleti (poster, recensioni, IMDb)'},
     ]},
    {'version': '0.132', 'date': '2026-03-17', 'title': 'Navigazione Rinnovata & Dropdown Generi',
     'changes': [
         {'type': 'new', 'text': 'Nuovo pulsante "Produci!" nella barra di navigazione con icona Ciak'},
         {'type': 'improvement', 'text': 'Selezione genere e sottogenere ora con menu a tendina (dropdown) nella pipeline'},
         {'type': 'improvement', 'text': 'Card "CIAK!" in dashboard ora apre direttamente il tab riprese nella pipeline'},
         {'type': 'improvement', 'text': 'Rimossa card "In Attesa" dalla dashboard (già inclusa nella pipeline di produzione)'},
         {'type': 'improvement', 'text': 'Tutti i link "Crea Film" ora portano alla nuova pipeline di produzione'},
     ]},
    {'version': '0.131', 'date': '2026-03-17', 'title': 'Scuola Recitazione Potenziata & Bug Fix',
     'changes': [
         {'type': 'new', 'text': 'Nuova sezione "Studenti dall\'Agenzia Casting" nella Scuola di Recitazione'},
         {'type': 'new', 'text': 'Attributo età aggiunto a tutti gli attori'},
         {'type': 'new', 'text': 'Diploma attori dopo 24 ore di formazione con costi giornalieri'},
         {'type': 'fix', 'text': 'Fix infrastrutture uniche: Scuola e Studio non più acquistabili due volte'},
         {'type': 'fix', 'text': 'Fix valore $NaN nel contest Box Office'},
         {'type': 'fix', 'text': 'Risposte trivia ora mescolate (non più sempre la prima corretta)'},
         {'type': 'fix', 'text': 'Contest "Cast Perfetto": aggiunte skill attori per scelta informata'},
     ]},
    {'version': '0.130', 'date': '2026-03-17', 'title': 'Pipeline di Produzione Cinematografica',
     'changes': [
         {'type': 'new', 'text': 'Nuovo sistema di produzione film in 6 fasi: Creazione, Proposte, Casting, Sceneggiatura, Pre-Produzione, Riprese'},
         {'type': 'new', 'text': 'Barra navigazione con 6 icone + badge conteggio per ogni fase'},
         {'type': 'new', 'text': 'Pre-valutazione IMDb automatica basata su genere, sinossi e location'},
         {'type': 'new', 'text': 'Casting con proposte temporizzate degli agenti e speed-up a crediti'},
         {'type': 'new', 'text': 'Sceneggiatura AI generata automaticamente con locandina del film'},
         {'type': 'new', 'text': 'Fase di Remastering con timer e miglioramento qualità'},
         {'type': 'new', 'text': 'Sezione "Buzz": vedi i film in produzione degli altri giocatori'},
         {'type': 'new', 'text': 'Limite film simultanei basato sul livello del giocatore'},
         {'type': 'fix', 'text': 'Fix stabilità sessione: niente più logout improvvisi durante la navigazione'},
     ]},
    {'version': '0.129', 'date': '2026-03-15', 'title': 'Velocità Mobile & Fix Vari',
     'changes': [
         {'type': 'improvement', 'text': 'Navigazione mobile molto più veloce: transizioni pagina dimezzate e cache dati intelligente'},
         {'type': 'fix', 'text': 'Fix "autenticazione fallita" al refresh: il token scaduto viene ora gestito automaticamente senza dover ricaricare più volte'},
         {'type': 'improvement', 'text': 'Retry automatico: se una chiamata fallisce per problemi di rete, il gioco riprova 1 volta da solo'},
         {'type': 'improvement', 'text': 'Timeout API ridotto da 2 minuti a 30 secondi per maggiore reattività'},
         {'type': 'fix', 'text': 'Corretto orario azzeramento giorno: 11:00 italiane (era scritto 12:00)'},
         {'type': 'fix', 'text': 'Dashboard mobile: griglia film ora mostra 9 film (3x3 perfetto, non più 1 film orfano)'},
     ]},
    {'version': '0.128', 'date': '2026-03-15', 'title': 'Fix CinePass & Contest Migliorati',
     'changes': [
         {'type': 'fix', 'text': 'Fix costo doppio CinePass: acquistare una sceneggiatura emergente non addebita più 20 CinePass extra alla creazione del film'},
         {'type': 'improvement', 'text': 'Contest: domande molto più varie e meno ripetitive (banca domande ampliata)'},
         {'type': 'fix', 'text': 'Fix layout mobile pagina Contest: titolo ora visibile e pagina completamente scrollabile'},
     ]},
    {'version': '0.127', 'date': '2026-03-15', 'title': 'Admin, Tutorial & Bilanciamento',
     'changes': [
         {'type': 'new', 'text': 'Pannello Admin: toggle donazioni nel profilo (solo NeoMorpheus)'},
         {'type': 'new', 'text': 'Sistema ruoli utente: l\'admin può assegnare moderatore, VIP, tester'},
         {'type': 'improvement', 'text': 'Tutorial aggiornato: 14 sezioni con sfide 1v1, 10 contest, donazioni'},
         {'type': 'improvement', 'text': 'Entrate orarie ribilanciate: base +60%, bonus per cinema multipli, +50% presenze'},
     ]},
    {'version': '0.126', 'date': '2026-03-15', 'title': 'Donazioni, UI & Bilanciamento Sfide',
     'changes': [
         {'type': 'new', 'text': 'Pulsante donazioni: supporta lo sviluppo con una donazione libera tramite PayPal'},
         {'type': 'new', 'text': 'Barra donazione fissa in basso (mobile) + icona nel menu'},
         {'type': 'fix', 'text': 'Premio +2 CinePass ora visibile nel riepilogo vittoria (era assegnato ma non mostrato)'},
         {'type': 'improvement', 'text': 'Bilanciamento sfide: skill uguali → ~80% pareggio, 1 punto differenza → ~55% pareggio'},
         {'type': 'improvement', 'text': 'Tradotto "UPSET" in "SORPRESA!" nel riepilogo round'},
         {'type': 'improvement', 'text': 'Cinema cliccabile nel dettaglio film: popup con distribuzione per paese'},
         {'type': 'improvement', 'text': 'Rimossa legenda punteggi dal CineBoard (calcolo invariato)'},
         {'type': 'fix', 'text': 'Costo creazione festival ribilanciato (costo scala col livello)'},
     ]},
    {'version': '0.125', 'date': '2026-03-14', 'title': 'Sessione Persistente, Skill & Ottimizzazione',
     'changes': [
         {'type': 'new', 'text': 'Checkbox "Ricordami" al login (sessione 90 giorni)'},
         {'type': 'new', 'text': '+1 CinePass automatico al rientro (cooldown 1 ora)'},
         {'type': 'new', 'text': 'Ultimo accesso visibile nella lista giocatori'},
         {'type': 'new', 'text': '10 contest giornalieri (50 CinePass totali) con sblocco progressivo'},
         {'type': 'improvement', 'text': '+20% guadagni su tutte le infrastrutture e incassi orari film'},
         {'type': 'new', 'text': 'Indicatori ▲/▼ per variazioni skill degli attori'},
         {'type': 'new', 'text': '+15% presenze per film di proprietà programmati nei cinema'},
         {'type': 'fix', 'text': 'Fix sezione "Voci dal Pubblico" nel Cinema Journal (era vuota)'},
         {'type': 'improvement', 'text': 'Ottimizzazione API: da 78MB a 770KB per il Cinema Journal'},
     ]},
    {'version': '0.124', 'date': '2026-03-14', 'title': 'Traduzione, CinePass Sfide & Fix Cinema',
     'changes': [
         {'type': 'improvement', 'text': 'Traduzione completa interfaccia e messaggi errore in italiano'},
         {'type': 'improvement', 'text': 'Film ordinati dal più recente nella pagina "I Miei Film"'},
         {'type': 'new', 'text': 'Costo CinePass per upgrade infrastrutture (formula esponenziale)'},
         {'type': 'new', 'text': '+2 CinePass per vittoria sfide 1v1'},
         {'type': 'new', 'text': 'Limiti sfide: 5 all\'ora, 20 al giorno con contatore visivo'},
         {'type': 'fix', 'text': 'Fix aggiunta film al cinema (calcolo schermi per livello)'},
     ]},
    # Latest first - These will be migrated to database on startup
    {'version': '0.123', 'date': '2026-03-14', 'title': 'Nuovo Logo & Sfondo Cinematografico',
     'changes': [
         {'type': 'new', 'text': 'Sfondo cinematografico sfocato fisso su tutte le pagine del gioco'},
         {'type': 'new', 'text': 'Logo CineWorld Studios nella pagina di login'},
         {'type': 'new', 'text': 'Logo CineWorld Studios nella pagina crediti'},
         {'type': 'improvement', 'text': 'Aggiornata sezione tecnologie nei crediti (GPT-4o, GPT-Image-1, Shadcn/UI, APScheduler)'},
     ]},
    {'version': '0.122', 'date': '2026-03-14', 'title': 'Locandine AI Migliorate',
     'changes': [
         {'type': 'improvement', 'text': 'Le locandine AI ora includono automaticamente il titolo del film e il genere direttamente nell\'immagine generata'},
         {'type': 'fix', 'text': 'Ripristinato il sistema originale di poster con testo integrato (titolo grande + sottotitolo genere)'},
     ]},
    {'version': '0.121', 'date': '2026-03-14', 'title': 'Tutorial Aggiornato',
     'changes': [
         {'type': 'improvement', 'text': 'Tutorial completamente riscritto: 12 passi con CinePass, Login Giornaliero, Contest, Scuola di Recitazione e Sceneggiature Emergenti'},
         {'type': 'fix', 'text': 'Fix saldo CinePass non visibile nel profilo e nella barra superiore'},
     ]},
    {'version': '0.120', 'date': '2026-03-14', 'title': 'Sistema CinePass & Contest Giornalieri',
     'changes': [
         {'type': 'new', 'text': 'CinePass: nuova valuta premium! Ogni utente parte con 100 CinePass'},
         {'type': 'new', 'text': 'CinePass richiesti per: creare film (20), comprare infrastrutture (8-20), pre-ingaggiare attori (5), sceneggiature emergenti (10), reclutare alla scuola (3)'},
         {'type': 'new', 'text': 'Login giornaliero consecutivo: guadagna 3-35 CinePass al giorno + bonus ogni 15 giorni consecutivi'},
         {'type': 'new', 'text': 'Popup automatico bonus giornaliero al primo accesso con 7 giorni cliccabili'},
         {'type': 'new', 'text': 'Contest giornalieri: 3 sfide al giorno, fino a 50 CinePass. Si azzerano alle 11:00 italiane'},
         {'type': 'new', 'text': 'Indovina il Budget, Cast Perfetto, Box Office Prediction, Speed Producer - contest sempre diversi'},
         {'type': 'new', 'text': 'Badge CinePass nella barra superiore accanto ai fondi'},
         {'type': 'improvement', 'text': 'Sezione Contest sostituisce i Mini Giochi nella Dashboard'},
         {'type': 'improvement', 'text': 'Popup conferma CinePass prima di ogni acquisto importante'},
     ]},
    {'version': '0.115', 'date': '2026-03-14', 'title': 'Scuola di Recitazione Completa & Navigazione Mobile',
     'changes': [
         {'type': 'new', 'text': 'Scuola di Recitazione: forma i tuoi attori da zero! Acquista la scuola dalle Infrastrutture'},
         {'type': 'new', 'text': '6 reclute disponibili ogni giorno con skill iniziali, età e talento nascosto'},
         {'type': 'new', 'text': 'Sistema formazione 10-20 giorni con barre progresso e skill in tempo reale'},
         {'type': 'new', 'text': 'Opzioni post-formazione: Tieni nel Cast (costo 0, stipendio mensile) o Libera nel pool pubblico'},
         {'type': 'new', 'text': 'Cast Personale: i tuoi attori formati appaiono in cima alla lista nel Film Wizard'},
         {'type': 'new', 'text': 'Notifiche interattive: clicca sul nome dell\'attore per vedere tutte le skill con popup'},
         {'type': 'new', 'text': 'Attori rilasciati: bottone "Ingaggia" direttamente dalla notifica'},
         {'type': 'new', 'text': 'Notifiche broadcast: tutti i giocatori vedono le star formate dagli altri'},
         {'type': 'new', 'text': 'Upgrade Scuola: migliora il livello per sbloccare più slot di formazione'},
         {'type': 'new', 'text': 'Icona Infrastrutture nella barra di navigazione mobile'},
         {'type': 'improvement', 'text': 'Icone e testo ridimensionati nella bottom nav per ospitare 8 voci su mobile'},
         {'type': 'improvement', 'text': 'Tutte le 13 skill attore tradotte in italiano (Recitazione Fisica, Carisma, Metodo, etc.)'},
         {'type': 'fix', 'text': 'Fix acquisto infrastrutture: corretto import mancante che bloccava gli acquisti'},
         {'type': 'fix', 'text': 'Fix conteggi formazione: training e ready ora aggiornati correttamente'},
         {'type': 'fix', 'text': 'Fix sistema notifiche Scuola: notifiche ora create e salvate correttamente'},
     ]},
    {'version': '0.110', 'date': '2026-03-13', 'title': 'Sceneggiature Emergenti & Locandine Classiche',
     'changes': [
         {'type': 'new', 'text': 'Nuova sezione "Sceneggiature Emergenti": sceneggiature pronte da produrre con cast, rating e prezzo'},
         {'type': 'new', 'text': 'Due opzioni: "Solo Sceneggiatura" (scegli il tuo cast) o "Pacchetto Completo" (tutto incluso, scegli solo la locandina)'},
         {'type': 'new', 'text': 'Rating IMDb per trama e trama+cast - il valore finale dipende anche dalla produzione'},
         {'type': 'new', 'text': 'Sceneggiatori emergenti: 20% delle sceneggiature hanno un nuovo talento che entra nel pool permanente'},
         {'type': 'new', 'text': 'Locandina Classica: pulsante fallback per generare locandine tematiche con gradiente e testo overlay'},
         {'type': 'new', 'text': 'Pallino rosso notifica per nuove sceneggiature disponibili'},
         {'type': 'new', 'text': 'Sezione Sceneggiature aggiunta nel menu hamburger'},
         {'type': 'fix', 'text': 'Fix errore creazione film: gestione corretta errori validazione Pydantic'},
         {'type': 'fix', 'text': 'Fix overlay step bloccati: ora è un banner non invasivo che permette di vedere il contenuto'},
         {'type': 'fix', 'text': 'Fix titolo pagina nascosto dalla navbar su mobile'},
         {'type': 'fix', 'text': 'Fix regressione preview: route catch-all non intercetta più le API'},
     ]},
    {'version': '0.101', 'date': '2026-03-12', 'title': 'Animazioni Battaglia, Booster, Contro-Sfida & Fix Notifiche',
     'changes': [
         {'type': 'new', 'text': 'Animazioni battaglia: ogni skill si rivela una per volta con frasi epiche in italiano'},
         {'type': 'new', 'text': 'Animazione vittoria con confetti e sconfitta con effetto drammatico'},
         {'type': 'new', 'text': 'Sistema Booster per sfide 1v1: +20% skill su un film a scelta (costo inversamente proporzionale alla qualità)'},
         {'type': 'new', 'text': 'Tasto Contro-Sfida: lancia una rivincita immediata a fine match'},
         {'type': 'new', 'text': 'Popup sfida al login: gli utenti offline vedono le sfide ricevute appena entrano'},
         {'type': 'fix', 'text': 'Fix notifiche: ogni tipo di notifica ora reindirizza alla pagina corretta'},
         {'type': 'improvement', 'text': 'Ogni manche dura 20-30 secondi con animazioni fluide per ogni skill'},
     ]},
    {'version': '0.100', 'date': '2026-03-12', 'title': 'Ricalibrazione Economia, Colonna Sonora & Impatto Botteghino',
     'changes': [
         {'type': 'improvement', 'text': 'Costi del film ricalibrati: cast ora costa 3x in più (attori $150k base, registi $300k base)'},
         {'type': 'improvement', 'text': 'Incasso iniziale aumentato: da $5k a $50k base, con cap fino a $5M per i capolavori'},
         {'type': 'new', 'text': 'Rating Colonna Sonora visibile nel riepilogo film dopo il nome del compositore'},
         {'type': 'new', 'text': 'La colonna sonora ha un impatto del 25% sul rating totale del film'},
         {'type': 'new', 'text': 'Boost esponenziale colonna sonora nei primi 3 giorni: fino a +150% (G1), +80% (G2), +30% (G3) al botteghino'},
         {'type': 'improvement', 'text': 'Moltiplicatori tier film aumentati: capolavoro 3x, eccellente 2.2x, buono 1.5x'},
     ]},
    {'version': '0.099', 'date': '2026-03-12', 'title': 'Sfide 1v1: Scelta Offline/Online & Auto-Accept',
     'changes': [
         {'type': 'new', 'text': 'Nuovo flusso sfide: dopo la selezione film, scegli se sfida Offline o Online'},
         {'type': 'new', 'text': 'Sfide Offline: accettate automaticamente, battaglia immediata'},
         {'type': 'new', 'text': 'Sfide Online: lista giocatori online con notifica popup in tempo reale'},
         {'type': 'improvement', 'text': "L'avversario online riceve un popup per accettare/rifiutare la sfida"},
         {'type': 'improvement', 'text': 'Separazione chiara tra giocatori online (pallino verde) e offline'},
     ]},
    {'version': '0.098', 'date': '2026-03-12', 'title': 'Fix Cast: 8 Skill, Rating IMDb & Migrazione Dati',
     'changes': [
         {'type': 'fix', 'text': 'Corretto rating IMDb: ora calcolato realmente in base a skill, fama ed esperienza (0-100)'},
         {'type': 'fix', 'text': 'Tutti i cast hanno ora esattamente 8 skill (da un pool di 50 possibili)'},
         {'type': 'fix', 'text': 'Migrazione completa: 8000 membri del cast aggiornati con skill, IMDb, fama'},
         {'type': 'fix', 'text': 'Verificata generazione trama AI: funziona correttamente'},
         {'type': 'improvement', 'text': 'Spinner di caricamento aggiunto a tutte le pagine'},
     ]},
    {'version': '0.097', 'date': '2026-03-12', 'title': 'Sfide 1v1 Riabilitate, Filtro Età Cast & Info Film Fisso',
     'changes': [
         {'type': 'new', 'text': 'Sfide 1v1 riabilitate: sfida giocatori online e offline con costo partecipazione $50.000'},
         {'type': 'new', 'text': 'Premio vittoria $100.000: il vincitore si porta a casa tutto il montepremi'},
         {'type': 'new', 'text': 'Notifica popup per sfide in tempo reale ai giocatori online'},
         {'type': 'new', 'text': 'Filtro età cast: Giovani, 18-30, 31-50, 51+ nella selezione attori'},
         {'type': 'new', 'text': 'Barra info film fissa: nome film e genere sempre visibili durante la creazione'},
         {'type': 'improvement', 'text': 'Sfide semplificate: rimossi 2v2, 3v3, 4v4 e Tutti contro Tutti'},
         {'type': 'improvement', 'text': 'Menu Bozze separato da Pre-Ingaggi'},
         {'type': 'improvement', 'text': 'Mercato Infrastrutture in pausa temporanea'},
     ]},
    {'version': '0.096', 'date': '2026-03-12', 'title': 'Sistema Cast Rinnovato & Ricerca Avanzata',
     'changes': [
         {'type': 'new', 'text': '50 skill totali divise per ruolo (13 per tipo), ogni membro del cast ha esattamente 8 skill'},
         {'type': 'new', 'text': 'Valutazione IMDb: stella singola + punteggio globale 0-100 con decimale'},
         {'type': 'new', 'text': 'Sistema Star: stella dorata per attori famosi (+40% costo, +15% rifiuto se mai lavorato insieme)'},
         {'type': 'new', 'text': 'Badge fama per registi (corona), sceneggiatori (premio), compositori (nota musicale)'},
         {'type': 'new', 'text': 'Ricerca avanzata cast: filtra fino a 3 skill con valore minimo desiderato'},
         {'type': 'new', 'text': 'Sottogeneri Comici aggiunti: Film Comico e Commedia Italiana'},
         {'type': 'improvement', 'text': 'Skill intere 0-100 per tutti i tipi di cast con distribuzione realistica'},
         {'type': 'improvement', 'text': 'Cast completamente rigenerato con nuove regole (8000 membri)'},
     ]},
    {'version': '0.095', 'date': '2026-03-12', 'title': 'Ottimizzazione Velocità & Nuova Colonna Sonora',
     'changes': [
         {'type': 'fix', 'text': 'Fix crash Giornale del Cinema: la pagina ora si apre correttamente'},
         {'type': 'fix', 'text': 'Fix login: autenticazione più stabile e veloce'},
         {'type': 'new', 'text': 'Colonna Sonora automatica: punteggio stile IMDb basato su compositore e genere'},
         {'type': 'new', 'text': 'Riepilogo costi dettagliato prima della creazione del film'},
         {'type': 'new', 'text': 'Cast ampliato a 2000 per tipo (8000 totali) con 25+ nazionalità'},
         {'type': 'new', 'text': '50 cast visibili per genere con refresh casuale per massima varietà'},
         {'type': 'new', 'text': 'ErrorBoundary: le pagine non si bloccano più, mostrano un pulsante "Riprova"'},
         {'type': 'new', 'text': 'Spinner di caricamento su ogni sezione del gioco'},
         {'type': 'improvement', 'text': 'Infrastrutture e Sfide VS in pausa temporanea per ottimizzazione'},
         {'type': 'improvement', 'text': 'Generazione trailer temporaneamente in pausa'},
         {'type': 'improvement', 'text': 'Rimossa generazione AI colonna sonora (sostituita con sistema automatico)'},
         {'type': 'improvement', 'text': 'Timeout API ridotto da 2 minuti a 30 secondi per maggiore reattività'}
     ]},
    {'version': '0.089', 'date': '2026-03-11', 'title': 'Manche Singole, Notifiche Cliccabili & Film Uscito',
     'changes': [
         {'type': 'new', 'text': 'Report Manche Singole: ogni manche della sfida ha ora la sua pagina dedicata con navigazione Avanti/Indietro'},
         {'type': 'new', 'text': 'Notifiche Cliccabili: ogni notifica ti porta direttamente al contenuto (sfida, film, trailer, festival, social)'},
         {'type': 'new', 'text': 'Notifica Film Uscito: ricevi una notifica con qualità e incasso quando il tuo film esce'},
         {'type': 'new', 'text': 'Freccia indicatore su notifiche cliccabili per mostrare che portano a una pagina'},
         {'type': 'improvement', 'text': 'Sfide Offline attive di default per tutti i giocatori'},
         {'type': 'improvement', 'text': 'Navigazione intelligente notifiche con routing per tipo (sfide, film, festival, social)'}
     ]},
    {'version': '0.087', 'date': '2026-03-11', 'title': 'Battaglie 3 Manche, Fix Qualità Film & Rinegoziazione Cast',
     'changes': [
         {'type': 'new', 'text': 'Sistema Battaglie 3 Manche: ogni sfida ha 3 manche (film vs film) con 8 skill battles ciascuna'},
         {'type': 'new', 'text': 'Spareggio: se una manche finisce 4-4, il gradimento del pubblico decide il vincitore'},
         {'type': 'new', 'text': 'Rinegoziazione Cast: quando un attore rifiuta, puoi rilanciate fino a 3 volte con un\'offerta più alta'},
         {'type': 'fix', 'text': 'Fix qualità film: i film non escono più tutti scarsi/flop. Distribuzione bilanciata con più film buoni e ottimi'},
         {'type': 'improvement', 'text': 'Report battaglia dettagliato: ogni manche mostra titoli dei film, skill per skill, e spareggi'}
     ]},
    {'version': '0.085', 'date': '2026-03-11', 'title': 'Poster AI, Battaglie 8 Skill & Popup IMDb',
     'changes': [
         {'type': 'new', 'text': 'Locandine AI: generazione poster con GPT Image 1, coerenti con titolo e genere del film'},
         {'type': 'new', 'text': 'Sistema Battaglie 8 Skill: ogni sfida ha 8 mini-battaglie basate su Regia, Fotografia, Sceneggiatura, Recitazione, Colonna Sonora, Effetti, Montaggio e Carisma'},
         {'type': 'new', 'text': 'Meccanica Upset: i film con skill inferiori possono vincere come evento raro!'},
         {'type': 'new', 'text': 'Popup IMDb: cliccando sul punteggio IMDb si vedono i 6 fattori di valutazione dettagliati'},
         {'type': 'new', 'text': 'Bonus Online: +15% ricompense per chi gioca sfide in modalità online'},
         {'type': 'improvement', 'text': 'Dashboard: rimosse statistiche contest, ora solo nella board Mini Giochi'},
         {'type': 'improvement', 'text': 'Rimosso tasto Aggiorna dalla sezione sfide VS'}
     ]},
    {'version': '0.083', 'date': '2026-03-11', 'title': 'Mini-Giochi VS 1v1 & Fix Stabilità',
     'changes': [
         {'type': 'new', 'text': 'Mini-Giochi VS 1v1: sfida altri giocatori con le stesse domande!'},
         {'type': 'new', 'text': 'Crea sfida VS, rispondi alle domande e attendi un avversario'},
         {'type': 'new', 'text': 'Tab sfide aperte per accettare sfide di altri giocatori'},
         {'type': 'new', 'text': 'Storico sfide VS con vittorie, sconfitte e pareggi'},
         {'type': 'new', 'text': 'Ricompense VS: vincitore x1.5, perdente x0.3, pareggio x0.8'},
         {'type': 'fix', 'text': 'Fix pulsante "Continua" nella schermata report battaglia (non più bloccante)'},
         {'type': 'fix', 'text': 'Aggiunto pulsante Chiudi (X) e Salta Animazione nella battaglia'},
         {'type': 'fix', 'text': 'Fix errori di validazione Pydantic per film vecchi nel database'},
         {'type': 'improvement', 'text': 'Script di migrazione dati per allineare documenti vecchi'},
         {'type': 'improvement', 'text': 'Migliorata compatibilità mobile per tutti i dialog'}
     ]},
    {'version': '0.080', 'date': '2026-03-10', 'title': 'Locandina & Trailer Gratuiti',
     'changes': [
         {'type': 'fix', 'text': 'Generazione locandina ora usa immagini gratuite (loremflickr) basate sul genere del film'},
         {'type': 'fix', 'text': 'Generazione trailer ora usa FFmpeg (gratuito) con effetto Ken Burns, testo e transizioni'},
         {'type': 'improvement', 'text': 'Trailer generato in ~3 secondi invece dei 5+ minuti precedenti'},
         {'type': 'improvement', 'text': 'Trailer in formato H.264 1280x720, durate 4/8/12 secondi'},
         {'type': 'fix', 'text': 'Rimossi servizi a pagamento (gpt-image-1, Sora 2) che davano errori intermittenti'},
         {'type': 'fix', 'text': 'Card "Sfide" nella Dashboard ripristinata con nome corretto'}
     ]},
    {'version': '0.079', 'date': '2026-03-10', 'title': 'Contest, Revenue Infrastruttura & Mini-Giochi AI',
     'changes': [
         {'type': 'new', 'text': 'Sezione "Sfide" rinominata "Contest" in tutte le lingue (IT, EN, ES, FR, DE)'},
         {'type': 'new', 'text': 'Mini-giochi con domande generate da AI (GPT-4o-mini) ad ogni partita'},
         {'type': 'new', 'text': 'Tracciamento domande viste per evitare ripetizioni nei mini-giochi'},
         {'type': 'new', 'text': 'Fallback automatico alla pool statica se la generazione AI fallisce'},
         {'type': 'fix', 'text': 'Revenue infrastruttura: lo scheduler ora processa TUTTI i tipi (cinema, drive-in, multiplex, VIP, ecc.)'},
         {'type': 'fix', 'text': 'Frequenza aggiornamento revenue aumentata da 6h a 2h'},
         {'type': 'improvement', 'text': 'Reddito minimo garantito per ogni infrastruttura in base al livello'},
         {'type': 'improvement', 'text': 'Reddito passivo per Production Studio e Cinema School'}
     ]},
    {'version': '0.078', 'date': '2026-03-10', 'title': 'Profilo Giocatore Globale & Nickname Cliccabili',
     'changes': [
         {'type': 'new', 'text': 'Pop-up profilo giocatore globale cliccando su qualsiasi nickname'},
         {'type': 'new', 'text': 'Nickname cliccabili in: Classifiche, Chat, Festival, Amici, Contest'},
         {'type': 'new', 'text': 'Pulsanti rapidi nel pop-up: Aggiungi Amico, Sfida 1v1, Invia Messaggio'},
         {'type': 'new', 'text': 'Statistiche giocatore nel pop-up: Film, Incassi, Qualità, XP, Premi, Livello'},
         {'type': 'new', 'text': 'Film recenti del giocatore visibili nel pop-up con poster e dettagli'}
     ]},
    {'version': '0.077', 'date': '2026-03-10', 'title': 'Pannello Giocatori & Icona Amicizie',
     'changes': [
         {'type': 'new', 'text': 'Icona Giocatori nella barra di navigazione con contatore online'},
         {'type': 'new', 'text': 'Pannello con lista completa giocatori: sezioni Online e Offline'},
         {'type': 'new', 'text': 'Profilo giocatore nel pannello con statistiche e film'},
         {'type': 'new', 'text': 'Pulsanti azione rapida: Aggiungi Amico e Sfida 1v1 dal pannello'},
         {'type': 'improvement', 'text': 'Icona Amicizie sempre visibile nella barra di navigazione fissa'},
         {'type': 'improvement', 'text': 'Heartbeat aggiornato con campo livello per badge nella lista'}
     ]},
    {'version': '0.076', 'date': '2026-03-10', 'title': 'Giornale del Cinema & Sistema Critiche', 
     'changes': [
         {'type': 'new', 'text': 'Icona Giornale del Cinema nella barra di navigazione fissa'},
         {'type': 'new', 'text': 'Barra sticky con 4 categorie: News, Pubblico, Breaking News, Hall of Fame'},
         {'type': 'new', 'text': 'Hall of Fame con stelle scoperte e pre-ingaggio diretto'},
         {'type': 'new', 'text': 'Sistema Critiche Film: 2-4 recensioni da giornali e giornalisti al rilascio'},
         {'type': 'new', 'text': '15 testate giornalistiche (Variety, Cahiers du Cinéma, etc.) con bias e prestigio'},
         {'type': 'new', 'text': 'Popup animato al rilascio film con tier + recensioni della critica'},
         {'type': 'new', 'text': 'Bonus/malus della critica su spettatori, incassi e rating'},
         {'type': 'improvement', 'text': 'Pulsanti Giornale ottimizzati per mobile'},
         {'type': 'improvement', 'text': 'Sezione "Altre News" rinominata "Breaking News"'}
     ]},
    {'version': '0.075', 'date': '2026-03-10', 'title': 'Ribilanciamento Qualità Film', 
     'changes': [
         {'type': 'new', 'text': 'Nuova formula qualità film: distribuzione realistica con flop e film scarsi'},
         {'type': 'new', 'text': 'Fattore "giornata storta" (10%) e "magia" (5%) nella produzione'},
         {'type': 'improvement', 'text': 'Generazione trailer con retry automatico e fallback a durata ridotta'},
         {'type': 'fix', 'text': 'Risposte del Creator ora visibili nella chat generale'},
         {'type': 'fix', 'text': 'Like virtuali ora correttamente visibili in tutte le schermate'},
         {'type': 'fix', 'text': 'Campi mancanti nel modello Film (trailer_url, attendance, etc.)'}
     ]},
    {'version': '0.074', 'date': '2026-03-10', 'title': 'Like Pubblico Virtuale sui Poster', 
     'changes': [
         {'type': 'new', 'text': 'Badge like virtuali (cuore rosa) visibile su tutti i poster'},
         {'type': 'improvement', 'text': 'Like virtuali mostrati in Dashboard, CineBoard, Giornale e My Films'},
     ]},
    {'version': '0.073', 'date': '2026-03-10', 'title': 'Giornale del Cinema Ridisegnato', 
     'changes': [
         {'type': 'improvement', 'text': 'Giornale del Cinema ridisegnato con poster 4 per riga'},
         {'type': 'new', 'text': 'Sezioni news testuali: Pubblicazioni, Messaggi Pubblico, Altre News'},
         {'type': 'new', 'text': 'Modale interattivi per film dal Giornale'},
     ]},
    {'version': '0.072', 'date': '2026-03-10', 'title': 'Sistema Contatti Creator & CineBoard Nav', 
     'changes': [
         {'type': 'new', 'text': 'Form "Contattaci" nella pagina Crediti per messaggi al Creator'},
         {'type': 'new', 'text': 'Creator Board per gestione e risposta ai messaggi'},
         {'type': 'new', 'text': 'Badge "Creator" per NeoMorpheus'},
         {'type': 'new', 'text': 'Icona CineBoard nella barra di navigazione fissa'},
     ]},
    {'version': '0.071', 'date': '2026-03-10', 'title': 'Miglioramenti Contest & Navigazione', 
     'changes': [
         {'type': 'new', 'text': 'Icona Contest nella barra di navigazione fissa'},
         {'type': 'new', 'text': 'Tutorial interattivo nella pagina Contest'},
         {'type': 'new', 'text': 'Notifica di benvenuto "Contest sbloccati!" per nuovi utenti'},
         {'type': 'new', 'text': 'Storico contest passati, in sospeso e completati'},
         {'type': 'new', 'text': 'Pulsanti per riproporre o annullare contest'},
         {'type': 'improvement', 'text': 'Icona Chat nella barra di navigazione superiore'}
     ]},
    {'version': '0.070', 'date': '2026-03-10', 'title': 'Sistema Contest Multiplayer', 
     'changes': [
         {'type': 'new', 'text': 'Sistema Contest completo: 1v1, 2v2, 3v3, 4v4 e Tutti contro tutti'},
         {'type': 'new', 'text': '8 skill cinematografiche per film (Regia, Sceneggiatura, Cast, etc.)'},
         {'type': 'new', 'text': '3 manche per sfida con commenti automatici di combattimento'},
         {'type': 'new', 'text': 'Matchmaking: casuale, amici o membri della Major'},
         {'type': 'new', 'text': 'Classifica generale sfide e statistiche giocatore'},
         {'type': 'new', 'text': 'Bonus/malus sfide per vincitori e perdenti'},
         {'type': 'new', 'text': 'Tipi sfida: Rapida, Classica, Maratona, Torneo, Epica'}
     ]},
    {'version': '0.069', 'date': '2026-03-10', 'title': 'Video Cerimonia & Download Trailer', 
     'changes': [
         {'type': 'new', 'text': 'Pulsante download trailer direttamente dalla pagina film'},
         {'type': 'new', 'text': 'Pulsante download video cerimonie festival'},
         {'type': 'improvement', 'text': 'Trailer completamente gratuiti per tutti i giocatori'}
     ]},
    {'version': '0.068', 'date': '2026-03-10', 'title': 'Sistema Pubblico Virtuale & Recensioni', 
     'changes': [
         {'type': 'new', 'text': 'Like virtuali del pubblico con bonus monetari fino a +20%'},
         {'type': 'new', 'text': 'Recensioni automatiche stile IMDb generate dal pubblico virtuale'},
         {'type': 'new', 'text': 'Board recensioni pubbliche con valutazioni e sentiment'},
         {'type': 'new', 'text': 'Pubblico virtuale influenza vincitori festival (50%-100%)'},
         {'type': 'improvement', 'text': 'Film in evidenza Dashboard ora basati su affluenze'},
         {'type': 'improvement', 'text': 'Icone festival nella barra navigazione rapida'},
         {'type': 'improvement', 'text': 'Festival personalizzati visibili nella barra rapida'}
     ]},
    {'version': '0.067', 'date': '2026-03-10', 'title': 'Refactoring & Menu Mobile Migliorato', 
     'changes': [
         {'type': 'improvement', 'text': 'Menu mobile completamente ridisegnato con griglia icone'},
         {'type': 'improvement', 'text': 'Background menu scuro e non trasparente'},
         {'type': 'improvement', 'text': 'Pulsante hamburger sempre visibile su iPhone'},
         {'type': 'improvement', 'text': 'Cerimonia live ottimizzata per mobile'},
         {'type': 'fix', 'text': 'Indicatore Festival Live cliccabile per navigare alla live'},
         {'type': 'improvement', 'text': 'Struttura codice modulare per migliore manutenibilità'}
     ]},
    {'version': '0.066', 'date': '2026-03-10', 'title': 'Pulsante Festival Dashboard & UI Mobile', 
     'changes': [
         'Pulsante Festival del Cinema sulla Dashboard',
         'Barra navigazione rapida nella pagina Festival',
         'Modale cerimonia live responsivo per mobile',
         'Ottimizzazione generale interfaccia mobile'
     ]},
    {'version': '0.065', 'date': '2026-03-10', 'title': 'Bonus Visione Cerimonie & Notifiche Migliorate', 
     'changes': [
         'Bonus entrate fino a +10% guardando le cerimonie live',
         'Più tempo guardi, più guadagni!',
         'Notifiche con promemoria del bonus',
         'Indicatore bonus in tempo reale durante la visione'
     ]},
    {'version': '0.064', 'date': '2026-03-10', 'title': 'Cerimonie Live con Fusi Orari', 
     'changes': [
         'Premiazioni sempre alle 21:30 ora locale',
         'Supporto 50+ fusi orari mondiali',
         'Notifiche 6h, 3h, 1h prima e all\'inizio',
         'Indicatore LIVE/countdown nell\'header',
         'Effetti confetti e spotlight ai vincitori',
         'Audio TTS per annunci vincitori',
         'Sottotitoli sincronizzati multilingua',
         'Chat pubblica durante le cerimonie'
     ]},
    {'version': '0.063', 'date': '2026-03-10', 'title': 'Sistema Sottotitoli e Sequel', 
     'changes': [
         'Campo sottotitolo per film e pre-film',
         'Sistema sequel con bonus/malus basato su qualità originale',
         'Badge SEQUEL #X sui poster',
         'Fix generazione AI (trama, poster, soundtrack)'
     ]},
    {'version': '0.062', 'date': '2026-03-10', 'title': 'Selettore Lingua Login', 
     'changes': [
         'Selezione lingua IT/EN nelle pagine di autenticazione',
         'Traduzione automatica di tutti i testi'
     ]},
    {'version': '0.061', 'date': '2026-03-10', 'title': 'Sistema Pre-Ingaggio Completato', 
     'changes': [
         'Creazione bozze film (Pre-Film)',
         'Ingaggio anticipato del cast',
         'Sistema di negoziazione con offerte',
         'Penali per licenziamento cast',
         'Conversione pre-film in produzione'
     ]},
    {'version': '0.060', 'date': '2026-03-09', 'title': 'Recupero Credenziali', 
     'changes': [
         'Recupero password via email',
         'Recupero nickname via email',
         'Integrazione Resend per email transazionali'
     ]},
    {'version': '0.050', 'date': '2026-03-09', 'title': 'Release Notes Dinamiche', 
     'changes': ['Note di rilascio salvate nel database', 'Aggiornamento automatico', 'Endpoint POST /api/admin/release-notes']},
    {'version': '0.049', 'date': '2026-03-09', 'title': 'Sistema Autonomo 24/7', 
     'changes': ['APScheduler per task automatici', 'Aggiornamento ricavi ogni ora', 'Generazione cast giornaliera', 'Reset sfide automatico', 'Pulizia dati scaduti']},
    {'version': '0.048', 'date': '2026-03-09', 'title': 'Sistema Rifiuto Ingaggio Cast', 
     'changes': ['Cast può rifiutare offerte di lavoro', '23 motivazioni di rifiuto IT/EN', 'Modal popup con dettagli rifiuto', 'Card disabilitata dopo rifiuto', 'Persistenza rifiuto 24h']},
    {'version': '0.047', 'date': '2026-03-09', 'title': 'Sistema Ingaggio Star', 
     'changes': ['Sezione dedicata Stelle Scoperte', 'Ingaggio anticipato star per prossimo film', 'Visualizzazione skill dettagliate', 'Pagina Release Notes']},
    {'version': '0.046', 'date': '2026-03-09', 'title': 'Trailer in Chat & Giornale', 
     'changes': ['Annunci trailer automatici in chat via CineBot', 'Sezione "Nuovi Trailer" nel Cinema Journal', 'Click su trailer naviga al film']},
    {'version': '0.045', 'date': '2026-03-09', 'title': 'Boost Introiti & Sponsor', 
     'changes': ['+30% introiti primo giorno', '+10% introiti giorni successivi', '200 sponsor totali (40 a rotazione)', 'Budget sponsor aumentato +40%']},
    {'version': '0.044', 'date': '2026-03-09', 'title': 'Cast Pool Espanso', 
     'changes': ['200 cast members per tipo nel wizard', '2000+ membri totali nel database', 'Generazione automatica giornaliera 40-80 nuovi']},
    {'version': '0.043', 'date': '2026-03-09', 'title': 'Autosave Film', 
     'changes': ['Salvataggio automatico ogni 30 secondi', 'Salvataggio su chiusura browser', 'Indicatore visivo ultimo salvataggio']},
    {'version': '0.042', 'date': '2026-03-09', 'title': 'Film Incompleti', 
     'changes': ['Board Film Incompleti (Bozze)', 'Pausa/Riprendi creazione film', 'Badge stato: In Pausa, Auto-salvato, Recuperato']},
    {'version': '0.041', 'date': '2026-03-09', 'title': 'Fix Trailer Bloccati', 
     'changes': ['Timeout automatico 15 minuti', 'Reset manuale trailer stuck', 'Campo trailer_started_at per tracking']},
    {'version': '0.040', 'date': '2026-03-09', 'title': 'CineBoard & Classifiche', 
     'changes': ['CineBoard con Top 50 in Sala', 'Hall of Fame tutti i film', 'Punteggio multi-variabile (Qualità, Incassi, Popolarità, Premi, Longevità)']},
    {'version': '0.039', 'date': '2026-03-09', 'title': 'Sinossi AI & IMDb Rating', 
     'changes': ['Sinossi generata automaticamente via GPT-4o', 'Valutazione stile IMDb per ogni film', 'CineBoard Score nella pagina film']},
    {'version': '0.038', 'date': '2026-03-08', 'title': 'Attività Major', 
     'changes': ['Sfide Settimanali (6 tipi)', '5 Attività: Co-Produzione, Condivisione Risorse, Premiere, Scambio Talenti, Proiezione Collettiva', 'UI con bonus e cooldown']},
    {'version': '0.037', 'date': '2026-03-08', 'title': 'PWA Mobile', 
     'changes': ['App installabile su iOS e Android', 'Pagina download con istruzioni', 'Manifest.json e icone PWA']},
    {'version': '0.036', 'date': '2026-03-08', 'title': 'Re-Release Film', 
     'changes': ['Ripubblicazione film terminati', 'Costo basato sul successo precedente', 'Nuova programmazione in sala']},
    {'version': '0.035', 'date': '2026-03-08', 'title': 'Pulsanti Azione Profilo', 
     'changes': ['Aggiungi Amico dal profilo utente', 'Invita in Major dal profilo', 'Titoli film cliccabili ovunque']},
    {'version': '0.034', 'date': '2026-03-08', 'title': 'Inviti Major Offline', 
     'changes': ['Invita utenti anche se offline', 'Lista completa giocatori per inviti', 'Filtri per stato online/offline']},
    {'version': '0.033', 'date': '2026-03-08', 'title': 'Logo Major AI', 
     'changes': ['Generazione logo tramite Gemini Nano Banana', 'Prompt personalizzato dall\'utente', 'Logo visualizzato nella pagina Major']},
    {'version': '0.032', 'date': '2026-03-08', 'title': 'Sistema Catch-Up', 
     'changes': ['Calcolo incassi mentre server offline', 'Continuità del gioco garantita', 'Tracking last_activity utente']},
    {'version': '0.031', 'date': '2026-03-07', 'title': 'Sistema Social Completo', 
     'changes': ['Major (Alleanze) con livelli e bonus', 'Amici & Follower con 4 tab', 'Centro Notifiche con badge']},
    {'version': '0.030', 'date': '2026-03-07', 'title': 'Festival Personalizzati', 
     'changes': ['Creazione festival custom', 'Categorie personalizzabili', 'Sistema votazione e premi']},
    {'version': '0.029', 'date': '2026-03-06', 'title': 'Saghe & Serie TV', 
     'changes': ['Creazione saghe cinematografiche', 'Serie TV multi-stagione', 'Bonus per continuità narrativa']},
    {'version': '0.028', 'date': '2026-03-06', 'title': 'Sistema Affinità Cast', 
     'changes': ['+2% per ogni film insieme', 'Max +10% per coppia', 'Livelli: Conoscenti → Dream Team']},
    {'version': '0.027', 'date': '2026-03-05', 'title': 'Azioni One-Time Film', 
     'changes': ['Crea Star (promuovi attore)', 'Skill Boost cast', 'Genera Trailer (Sora 2)']},
    {'version': '0.026', 'date': '2026-03-05', 'title': 'Trailer AI Sora 2', 
     'changes': ['Generazione trailer video tramite Sora 2', 'Bonus qualità +5-15%', 'Anteprima nella pagina film']},
    {'version': '0.025', 'date': '2026-03-04', 'title': 'Poster AI', 
     'changes': ['Generazione poster tramite Gemini Nano Banana', 'Prompt personalizzato', 'Anteprima in tempo reale']},
    {'version': '0.024', 'date': '2026-03-04', 'title': 'Screenplay AI', 
     'changes': ['Generazione sceneggiatura tramite GPT-4o', 'Basata su genere, cast, trama', 'Editing manuale possibile']},
    {'version': '0.023', 'date': '2026-03-03', 'title': 'Soundtrack AI', 
     'changes': ['Descrizione colonna sonora AI', 'Integrazione con genere film', 'Bonus qualità per coerenza']},
    {'version': '0.022', 'date': '2026-03-03', 'title': 'Mini Games', 
     'changes': ['Trivia cinematografico', 'Box Office Prediction', 'Cast Match challenge']},
    {'version': '0.021', 'date': '2026-03-02', 'title': 'Leaderboard Globale', 
     'changes': ['Classifica giocatori per incassi', 'Leaderboard per paese', 'Badge per top producer']},
    {'version': '0.020', 'date': '2026-03-02', 'title': 'Festival Ufficiali', 
     'changes': ['Cannes, Venice, Berlin, Toronto, Sundance', 'Nomination automatiche', 'Premi e bonus']},
    {'version': '0.019', 'date': '2026-03-01', 'title': 'Cinema Journal', 
     'changes': ['Giornale del cinema stile newspaper', 'News su film in uscita', 'Scoperta nuove star']},
    {'version': '0.018', 'date': '2026-03-01', 'title': 'Sistema Chat', 
     'changes': ['Chat generale', 'Stanze private', 'Bot moderatore']},
    {'version': '0.017', 'date': '2026-02-28', 'title': 'Profile & Stats', 
     'changes': ['Pagina profilo dettagliata', 'Statistiche carriera', 'Cronologia film']},
    {'version': '0.016', 'date': '2026-02-28', 'title': 'Like & Commenti', 
     'changes': ['Like sui film', 'Sistema commenti', 'Notifiche interazioni']},
    {'version': '0.015', 'date': '2026-02-27', 'title': 'Advertising System', 
     'changes': ['Piattaforme pubblicitarie', 'Boost revenue temporaneo', 'ROI tracking']},
    {'version': '0.014', 'date': '2026-02-27', 'title': 'Box Office Dettagliato', 
     'changes': ['Revenue giornaliero', 'Grafici andamento', 'Previsioni AI']},
    {'version': '0.013', 'date': '2026-02-26', 'title': 'Cast Skills v2', 
     'changes': ['Skills multiple per attore', 'Specializzazioni per genere', 'Evoluzione skills']},
    {'version': '0.012', 'date': '2026-02-26', 'title': 'Hidden Gems', 
     'changes': ['Attori sconosciuti di talento', 'Scoperta star nascoste', 'Bonus per scoperta']},
    {'version': '0.011', 'date': '2026-02-25', 'title': 'Quality Score v2', 
     'changes': ['Formula qualità migliorata', 'Fattori multipli', 'Bonus sinergia cast']},
    {'version': '0.010', 'date': '2026-02-25', 'title': 'Sponsor System', 
     'changes': ['Sponsor per i film', 'Budget aggiuntivo', 'Revenue share']},
    {'version': '0.009', 'date': '2026-02-24', 'title': 'Location System', 
     'changes': ['Multiple location per film', 'Costi variabili per location', 'Bonus qualità']},
    {'version': '0.008', 'date': '2026-02-24', 'title': 'Equipment Packages', 
     'changes': ['Basic, Standard, Premium, IMAX', 'Effetti sulla qualità', 'Costi progressivi']},
    {'version': '0.007', 'date': '2026-02-23', 'title': 'Extras System', 
     'changes': ['Comparse per i film', 'Costi variabili', 'Impatto su qualità']},
    {'version': '0.006', 'date': '2026-02-23', 'title': 'Compositori', 
     'changes': ['Sistema compositori', 'Colonne sonore', 'Bonus qualità musica']},
    {'version': '0.005', 'date': '2026-02-22', 'title': 'Cast System', 
     'changes': ['Attori, Registi, Sceneggiatori', 'Skills e fama', 'Costi ingaggio']},
    {'version': '0.004', 'date': '2026-02-22', 'title': 'Genre System', 
     'changes': ['20+ generi cinematografici', 'Sub-generi', 'Bonus per combinazioni']},
    {'version': '0.003', 'date': '2026-02-21', 'title': 'Film Wizard', 
     'changes': ['Wizard creazione film 12 step', 'Preview costi', 'Validazione budget']},
    {'version': '0.002', 'date': '2026-02-21', 'title': 'Dashboard', 
     'changes': ['Dashboard principale', 'Overview finanze', 'Film in produzione']},
    {'version': '0.001', 'date': '2026-02-20', 'title': 'Auth & Base', 
     'changes': ['Sistema autenticazione', 'Registrazione utenti', 'Profilo base']},
    {'version': '0.000', 'date': '2026-02-20', 'title': 'Creazione Progetto', 
     'changes': ['Setup iniziale', 'Architettura FastAPI + React', 'Database MongoDB']},
]

DEFAULT_SYSTEM_NOTES = [
    {'title': 'Agenzia di Casting Personale', 'content': "Novita assoluta! Ora puoi avere la TUA agenzia di casting!\n\nCome funziona:\n1. Vai alla pagina Agenzia (pulsante nel menu Produci!)\n2. Ogni settimana trovi 8 nuove reclute da visionare\n3. Recluta quelle che ti piacciono: diventano attori permanenti della tua agenzia\n4. Livello 1: max 12 attori. Ogni livello dello Studio sblocca piu slot e reclute\n\nGeneri attore:\n- Ogni attore ha 2 generi in cui eccelle (badge verdi) e 1 genere adattabile (badge giallo)\n- Scegli attori con generi adatti ai tuoi film per massimizzare la qualita!\n\nBonus Film con attori propri:\n- 1 attore dalla tua agenzia: +25% XP e Fama\n- 2 attori: +35%\n- 3 attori: +50%\n- 4 o piu: +70%!\n\nCrescita attori:\n- Dopo ogni film, gli attori migliorano le skill in base alla qualita del film\n- Attenzione: ogni attore ha un 'talento nascosto' - alcune skill hanno un cap che non supereranno mai\n- Crescita graduale: nessuno diventa una star da un giorno all'altro!\n\nLicenziamento:\n- Puoi licenziare un attore per fare posto: tornera disponibile sul mercato globale\n\nStudenti della Scuola:\n- Gli studenti della scuola di recitazione sono disponibili per il casting\n- Continuano la formazione anche mentre girano un film, con bonus crescita!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Fix Incassi e Dashboard', 'content': "Risolti bug importanti!\n\n- Gli Incassi totali non diminuiscono piu dopo il ricalcolo automatico dello scheduler\n- Le locandine dei film nel Giornale del Cinema sono ora visibili\n- I punteggi Like, Social e Char nella Dashboard mostrano i valori reali\n\nLa formula revenue ora usa il massimo tra box office realistico e revenue totale, garantendo che i tuoi guadagni non calino mai.", 'category': 'bugfix', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'CineBoard: Classifiche Emittenti TV', 'content': "Nuove classifiche per le Emittenti TV!\n\n• Emittenti Più Viste di Sempre: chi ha raggiunto più spettatori in totale\n• Share Settimanale: top emittenti per share della settimana\n• Share Giornaliero: classifica live aggiornata ogni 5 minuti\n\nAccedi dal popup CineBoard nella navbar superiore. Chi ha lo share più alto domina la classifica!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Emittenti TV: Il Tuo Canale Netflix!', 'content': "Il sistema Emittenti TV è stato completamente rinnovato!\n\n• Puoi comprare più emittenti TV (costi crescono esponenzialmente)\n• Setup in 2 step: scegli un nome (permanente!) e la nazione, poi configura la pubblicità\n• Dashboard TV stile Netflix con sezioni Consigliati, Del Momento, I Più Visti\n• Slider pubblicità: più secondi = più incasso ma meno share\n• I film si possono inserire solo dopo la fine del cinema\n• Serie TV e Anime sempre inseribili\n• Revenue automatico ogni ora basato su qualità e share\n• Requisiti ridotti: Studio Serie TV e Anime -40%, Emittente TV -60%\n• Pagina pubblica per vedere tutte le emittenti dei giocatori\n• Nuovo tasto \"Le Mie TV!\" sulla Dashboard", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Dashboard Rinnovata', 'content': "La Dashboard è stata completamente rinnovata!\n\n• Ultimi Aggiornamenti: mostra le 5 produzioni più recenti di TUTTI i giocatori con locandina e produttore\n• I Miei Film: 5 locandine in fila unica ottimizzata per mobile con \"Vedi Tutti\"\n• Le Mie Serie TV: 5 locandine con link a \"Vedi Tutti\"\n• I Miei Anime: 5 locandine con link a \"Vedi Tutti\"\n• Layout più compatto e informativo", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Fix Sfide Online 1v1', 'content': "Risolto un bug importante nelle sfide online!\n\n• Il popup \"Sfida Ricevuta\" ora porta direttamente alla selezione film per accettare\n• Il pulsante \"Unisciti\" nelle sfide in attesa ora funziona correttamente\n• Cliccando la notifica sfida si apre il flusso di accettazione\n• Le notifiche sfida vengono controllate ogni 30 secondi anche senza refresh\n• Nuova UI: banner \"Sei stato sfidato!\" e pulsante \"ACCETTA SFIDA!\" differenziato", 'category': 'bugfix', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Emittente TV: Live Ratings & Storico Episodi', 'content': "La tua emittente televisiva è stata potenziata!\n\n• Live Ratings: audience in tempo reale con aggiornamento automatico ogni 5 secondi\n• Sparkline animata per ogni broadcast attivo\n• Share % e indicatore trend (crescita/calo/stabile)\n• Sistema Momentum: serie di qualità guadagnano pubblico episodio dopo episodio\n• Storico Episodi: clicca su un broadcast per vedere il grafico audience, dettaglio per episodio, analytics (picco, media, ricavi)\n• Banner LIVE con stats della rete completi", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Dashboard Semplificata', 'content': "La Dashboard è stata ripulita!\n\n• Rimossa la sezione 'Film in Attesa di Rilascio' dalla Dashboard\n• I film in attesa si gestiscono ora direttamente dalla Pipeline di Produzione (pulsante Produci!)\n• Layout più pulito e veloce da consultare", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Serie TV, Anime, Sequel e Emittente TV!', 'content': "Aggiornamento massiccio! Ora puoi produrre molto di più:\n\n• SERIE TV: 10 generi disponibili (Drama, Crime, Thriller...), pipeline completa con casting, sceneggiatura AI e produzione\n• ANIME: 8 generi unici (Shonen, Seinen, Shojo, Mecha, Isekai...), costi ridotti ma tempi più lunghi\n• SEQUEL: pipeline ridotta con cast ereditato (sconto 30%), bonus saga crescente fino a +15%\n• EMITTENTE TV: assegna le tue serie a 3 fasce orarie (Daytime, Prime Time, Late Night) e guadagna ricavi pubblicitari!\n\nSblocca lo Studio Serie TV e lo Studio Anime dalla sezione Infrastrutture. Il pulsante Produci! ora mostra 5 opzioni.\n\nNuove classifiche CineBoard per Serie TV e Anime (trend settimanale)!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Nuova Pipeline di Produzione Cinematografica!', 'content': 'Il sistema di creazione film e stato completamente rinnovato! Ora troverai il nuovo pulsante Produci! nella barra di navigazione. La produzione si divide in 6 fasi: Creazione, Proposte, Casting, Sceneggiatura, Pre-Produzione e Riprese. Ogni fase ha il suo tab dedicato con badge conteggio. I generi e sottogeneri si selezionano ora con pratici menu a tendina. La card CIAK! in dashboard ti porta direttamente alle riprese in corso. Buona produzione!', 'category': 'update', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Bug Fix - Studio di Produzione', 'content': 'Risolti diversi bug importanti:\n\n- Studio di Produzione: i 3 pannelli (Pre-Produzione, Post-Produzione, Agenzia Casting) ora si aprono correttamente\n- Agenzia Casting: corretti i nomi dei talenti che apparivano come "Unknown"\n- Aggiunto pulsante "Porta in Studio di Produzione" nel popup distribuzione', 'category': 'bugfix', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Cast Filtrato per Livello e Fama', 'content': 'Importante cambiamento nel bilanciamento del gioco!\n\nOra il cast disponibile durante la creazione film dipende dal tuo livello e dalla tua fama:\n\n- Livello 1-9: accesso ad attori 1 stella\n- Livello 10-19: fino a 2 stelle\n- Livello 20-29: fino a 3 stelle\n- Livello 30-39: fino a 4 stelle\n- Livello 40+: accesso completo a 5 stelle\n\nAnche la fama del tuo studio influenza quali talenti accettano di lavorare con te.\n\nQuesto rende la progressione piu significativa: salire di livello sblocca cast migliori e film di qualita superiore!', 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Agenzia Casting Potenziata', 'content': "L'Agenzia Casting dello Studio di Produzione e stata completamente rinnovata!\n\nNovita:\n- I talenti ora hanno nomi reali in base alla nazionalita\n- Cliccando su un talento si apre un popup con due scelte:\n  1. Usa Subito: il talento entra nel tuo Cast Personale ed e subito disponibile per i film\n  2. Invia alla Scuola di Recitazione: il talento parte con skill gia avanzate e migliora nel tempo\n\nStrategia: i talenti leggendari sono rari ma potentissimi. Ingaggiarli subito costa di piu ma hai un attore top immediato. Inviarli a scuola e un investimento a lungo termine!\n\nAttenzione: puoi ingaggiare ogni talento solo una volta a settimana.", 'category': 'feature', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Nuovo Sistema Riprese Film - Ciak, si Gira!', 'content': "Grande novita! Ora puoi girare i tuoi film prima di rilasciarli!\n\nCome funziona:\n1. Crea un film come sempre\n2. Nel popup di distribuzione, scegli:\n   - Rilascio Diretto: costo ridotto del 30%, ma qualita limitata a 5.8 IMDb e incassi ridotti\n   - Inizia le Riprese: scegli da 1 a 10 giorni di riprese\n\nBonus Riprese:\n- 1 giorno: +10% qualita\n- 3 giorni: +18%\n- 5 giorni: +25%\n- 7 giorni: +32%\n- 10 giorni: +40%\n\nDurante le riprese accadono eventi casuali ogni giorno:\n- Giornata Perfetta (+2%)\n- Improvvisazione Geniale (+3%)\n- Ispirazione Creativa (+2%)\n- Ritardo Meteo (-1%)\n- E altri...\n\nPuoi chiudere anticipatamente le riprese pagando CinePass (2 x giorni mancanti).\n\nTroverai il nuovo pulsante Ciak! nella Dashboard per monitorare i progressi!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Tutorial Aggiornato - 16 Step Completi', 'content': "Il tutorial e stato completamente aggiornato con tutti i nuovi contenuti!\n\nNovita nel tutorial:\n- Step 2 ora include tutti i 12 passaggi dettagliati della creazione film\n- Step 3 spiega il sistema di distribuzione con costi e zone\n- Nuovo Step 12 dedicato allo Studio di Produzione\n- Totale: 16 step completi per padroneggiare il gioco\n\nConsigliamo ai nuovi giocatori di leggerlo tutto per capire al meglio le meccaniche!", 'category': 'update', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Bozze Sceneggiatura - Crea Film Gratis!', 'content': "Novita nello Studio di Produzione! Ora puoi generare Bozze Sceneggiatura con intelligenza artificiale.\n\nCome funziona:\n1. Vai nel tuo Studio di Produzione > Pre-Produzione\n2. Scegli il genere e un titolo opzionale\n3. La AI generera titolo, sinossi e sottogeneri\n\nVantaggi delle bozze:\n- CinePass GRATIS quando crei il film con la bozza\n- Bonus qualita da +4% a +13% in base al livello dello studio\n- Titolo, genere e sceneggiatura pre-compilati nel Film Wizard\n\nPuoi tenere fino a 3 + livello bozze attive. Strategia: genera le bozze prima di creare i tuoi film per massimizzare la qualita e risparmiare CinePass!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Studio di Produzione - Ora Disponibile!', 'content': "Lo Studio di Produzione e finalmente operativo! Una volta acquistato (livello 15), avrai accesso a 3 potenti funzionalita:\n\n- Pre-Produzione: Applica bonus ai tuoi film in attesa di rilascio\n- Post-Produzione: Rimasterizza i film gia rilasciati per migliorare qualita e rating IMDb\n- Agenzia Casting: Ogni settimana troverai un pool esclusivo di talenti scontati fino al 40%!\n\nPiu sali di livello con lo studio, maggiori saranno i bonus!", 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
    {'title': 'Fix Sfide 1v1', 'content': 'Risolto il bug che non assegnava i +2 CinePass dopo una vittoria nelle sfide offline. Ridotte anche le probabilita di pareggio nelle skill battle.', 'category': 'bugfix', 'priority': 'normal', 'author': "Anacapito Studio's"},
    {'title': 'Sistema Distribuzione Film', 'content': 'Novita! Ora i film non escono piu automaticamente. Dopo la creazione, scegli dove distribuirli: Nazionale, Continentale o Mondiale. Ogni zona ha costi e ricavi diversi!', 'category': 'feature', 'priority': 'high', 'author': "Anacapito Studio's"},
]


# ==================== INIT FUNCTIONS (called at startup) ====================

async def initialize_release_notes():
    """Migrate static release notes to database on startup."""
    existing_count = await db.release_notes.count_documents({})
    if existing_count == 0:
        # First time: insert all release notes
        for note in RELEASE_NOTES:
            note['id'] = str(uuid.uuid4())
            note['created_at'] = datetime.now(timezone.utc).isoformat()
            await db.release_notes.insert_one(note)
        logging.info(f"Initialized {len(RELEASE_NOTES)} release notes in database")
    else:
        # Check for new versions not in database
        for note in RELEASE_NOTES:
            existing = await db.release_notes.find_one({'version': note['version']})
            if not existing:
                note['id'] = str(uuid.uuid4())
                note['created_at'] = datetime.now(timezone.utc).isoformat()
                await db.release_notes.insert_one(note)
                logging.info(f"Added new release note v{note['version']}")

async def add_release_note_to_db(version: str, title: str, changes: list):
    """
    Add a new release note to the database.
    Called automatically when a new feature is implemented.
    """
    # Check if version already exists
    existing = await db.release_notes.find_one({'version': version})
    if existing:
        # Update existing
        await db.release_notes.update_one(
            {'version': version},
            {'$set': {
                'title': title,
                'changes': changes,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        logging.info(f"Updated release note v{version}")
    else:
        # Create new
        note = {
            'id': str(uuid.uuid4()),
            'version': version,
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'title': title,
            'changes': changes,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.release_notes.insert_one(note)
        logging.info(f"Added release note v{version}: {title}")
    
    return True

async def initialize_system_notes():
    """Initialize default system notes if the collection is empty."""
    existing_count = await db.system_notes.count_documents({})
    if existing_count == 0:
        for note_data in DEFAULT_SYSTEM_NOTES:
            system_note = {
                'id': str(uuid.uuid4()),
                'title': note_data['title'],
                'content': note_data['content'],
                'category': note_data.get('category', 'update'),
                'priority': note_data.get('priority', 'normal'),
                'author': note_data.get('author', 'NeoMorpheus'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.system_notes.insert_one(system_note)
        logging.info(f"Initialized {len(DEFAULT_SYSTEM_NOTES)} default system notes")


# ==================== CINEBOARD / ATTENDANCE ====================

@router.get("/cineboard/attendance")
async def get_cineboard_attendance(
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """Get films ranked by attendance and screenings."""
    # Get films in theaters with attendance data
    attend_fields = {
        '_id': 0, 'id': 1, 'title': 1, 'user_id': 1,
        'current_cinemas': 1, 'current_attendance': 1, 'avg_attendance_per_cinema': 1,
        'cinema_distribution': 1, 'quality_score': 1, 'popularity_score': 1,
        'total_screenings': 1, 'cumulative_attendance': 1, 'status': 1, 'genre': 1
    }
    now_playing = await db.films.find(
        {'status': {'$in': ['in_theaters', 'released']}, 'current_cinemas': {'$gt': 0}},
        attend_fields
    ).sort('current_cinemas', -1).to_list(100)
    
    # Get all-time most screened films
    all_time = await db.films.find(
        {'total_screenings': {'$gt': 0}},
        attend_fields
    ).sort('total_screenings', -1).to_list(100)
    
    # Process now playing - bulk fetch owners (only essential fields)
    # Use .get() to avoid KeyError if user_id is missing
    np_owner_ids = list(set(f.get('user_id') for f in now_playing[:limit] if f.get('user_id')))
    at_owner_ids = list(set(f.get('user_id') for f in all_time[:limit] if f.get('user_id')))
    all_owner_ids = list(set(np_owner_ids + at_owner_ids))
    owners_cursor = db.users.find({'id': {'$in': all_owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1})
    owners_map = {o['id']: o async for o in owners_cursor}
    
    top_now_playing = []
    for i, film in enumerate(now_playing[:limit]):
        top_now_playing.append({
            'rank': i + 1,
            'id': film['id'],
            'title': film.get('title'),
            'genre': film.get('genre', ''),
            'current_cinemas': film.get('current_cinemas', 0),
            'current_attendance': film.get('current_attendance', 0),
            'avg_attendance_per_cinema': film.get('avg_attendance_per_cinema', 0),
            'cinema_distribution': film.get('cinema_distribution', [])[:5],
            'quality_score': film.get('quality_score', 0),
            'popularity_score': film.get('popularity_score', 0),
            'owner': owners_map.get(film.get('user_id'))
        })
    
    # Process all-time
    top_all_time = []
    for i, film in enumerate(all_time[:limit]):
        top_all_time.append({
            'rank': i + 1,
            'id': film['id'],
            'title': film.get('title'),
            'genre': film.get('genre', ''),
            'total_screenings': film.get('total_screenings', 0),
            'cumulative_attendance': film.get('cumulative_attendance', 0),
            'avg_attendance_per_screening': film.get('cumulative_attendance', 0) // max(1, film.get('total_screenings', 1)),
            'status': film.get('status'),
            'quality_score': film.get('quality_score', 0),
            'owner': owners_map.get(film.get('user_id'))
        })
    
    # Calculate global stats efficiently with aggregation
    pipeline = [
        {'$match': {'status': {'$in': ['in_theaters', 'released']}}},
        {'$group': {
            '_id': None,
            'total_films': {'$sum': 1},
            'total_cinemas': {'$sum': {'$ifNull': ['$current_cinemas', 0]}},
            'total_attendance': {'$sum': {'$ifNull': ['$current_attendance', 0]}}
        }}
    ]
    stats_result = await db.films.aggregate(pipeline).to_list(1)
    stats = stats_result[0] if stats_result else {'total_films': 0, 'total_cinemas': 0, 'total_attendance': 0}
    
    total_cinemas_showing = stats.get('total_cinemas', 0)
    total_current_attendance = stats.get('total_attendance', 0)
    avg_attendance = total_current_attendance // max(1, total_cinemas_showing)
    
    return {
        'top_now_playing': top_now_playing,
        'top_all_time': top_all_time,
        'global_stats': {
            'total_films_in_theaters': stats.get('total_films', 0),
            'total_cinemas_showing': total_cinemas_showing,
            'total_current_attendance': total_current_attendance,
            'avg_attendance_per_cinema': avg_attendance
        }
    }


# ==================== CINEMA NEWS / JOURNAL ====================

@router.get("/cinema-news")
async def get_cinema_news(
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get latest cinema news including star discoveries"""
    user_lang = user.get('language', 'en')
    
    news = await db.cinema_news.find(
        {},
        {'_id': 0, 'discoverer_avatar': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    
    # Localize titles and content
    for item in news:
        item['title_localized'] = item.get('title', {}).get(user_lang, item.get('title', {}).get('en', 'News'))
        item['content_localized'] = item.get('content', {}).get(user_lang, item.get('content', {}).get('en', ''))
    
    return {'news': news}

@router.get("/discovered-stars")
async def get_discovered_stars(user: dict = Depends(get_current_user), limit: int = 50):
    """Get list of discovered stars with full details"""
    stars = await db.people.find(
        {'is_discovered_star': True},
        {'_id': 0}
    ).sort('discovered_at', -1).limit(limit).to_list(limit)
    
    # Get discoverer details and check if hired by current user
    user_hired = await db.hired_stars.find({'user_id': user['id']}, {'star_id': 1}).to_list(100)
    hired_star_ids = {h['star_id'] for h in user_hired}
    
    for star in stars:
        if star.get('discovered_by'):
            discoverer = await db.users.find_one(
                {'id': star['discovered_by']}, 
                {'_id': 0, 'nickname': 1, 'avatar_url': 1, 'production_house_name': 1}
            )
            star['discoverer'] = discoverer
        
        # Calculate hire cost based on fame and skills
        base_cost = 100000  # $100k base
        fame_mult = 1 + (star.get('fame_score', 50) / 100)
        skill_avg = sum(star.get('skills', {}).values()) / max(len(star.get('skills', {})), 1)
        skill_mult = 1 + (skill_avg / 100)
        star['hire_cost'] = int(base_cost * fame_mult * skill_mult * star.get('stars', 3))
        star['is_hired_by_user'] = star['id'] in hired_star_ids
    
    return {'stars': stars, 'total': len(stars)}

@router.get("/journal/virtual-reviews")
async def get_journal_virtual_reviews(user: dict = Depends(get_current_user), limit: int = 50):
    """Get virtual audience reviews for display in the journal."""
    import random
    
    # Get reviews from the virtual_reviews collection
    all_reviews = await db.virtual_reviews.find(
        {},
        {'_id': 0}
    ).sort('created_at', -1).limit(100).to_list(100)
    
    reviews = []
    for review in all_reviews:
        # Get film info (exclude poster_url to keep response light)
        film = await db.films.find_one({'id': review.get('film_id')}, {'_id': 0, 'id': 1, 'title': 1})
        reviews.append({
            'film_id': review.get('film_id'),
            'film_title': film.get('title', 'Film sconosciuto') if film else 'Film sconosciuto',
            'reviewer_name': review.get('reviewer_name', 'Anonimo'),
            'reviewer_info': review.get('reviewer_info', ''),
            'rating': review.get('rating', 3),
            'comment': review.get('comment', review.get('text', ''))
        })
    
    random.shuffle(reviews)
    return {'reviews': reviews[:limit]}

@router.get("/journal/other-news")
async def get_journal_other_news(user: dict = Depends(get_current_user)):
    """Get various news items for the journal."""
    news = []
    now = datetime.now(timezone.utc)
    three_hours_ago = now - timedelta(hours=3)
    one_day_ago = now - timedelta(hours=24)
    
    # 1. Most liked film in last 3 hours
    films_3h = await db.films.find(
        {'updated_at': {'$gte': three_hours_ago.isoformat()}},
        {'_id': 0, 'id': 1, 'title': 1, 'likes_count': 1, 'virtual_likes': 1}
    ).sort('likes_count', -1).limit(1).to_list(1)
    
    if films_3h:
        film = films_3h[0]
        total_likes = film.get('likes_count', 0) + film.get('virtual_likes', 0)
        if total_likes > 0:
            news.append({
                'category': 'trending',
                'title': f"🔥 '{film['title']}' in tendenza!",
                'content': f"Il film ha ricevuto {total_likes} like nelle ultime 3 ore!",
                'link': f"/film/{film['id']}",
                'timestamp': 'Ultime 3 ore'
            })
    
    # 2. Most liked film in last 24 hours
    films_24h = await db.films.find(
        {'updated_at': {'$gte': one_day_ago.isoformat()}},
        {'_id': 0, 'id': 1, 'title': 1, 'likes_count': 1, 'virtual_likes': 1}
    ).sort('likes_count', -1).limit(1).to_list(1)
    
    if films_24h and (not films_3h or films_24h[0]['id'] != films_3h[0]['id']):
        film = films_24h[0]
        total_likes = film.get('likes_count', 0) + film.get('virtual_likes', 0)
        if total_likes > 0:
            news.append({
                'category': 'trending',
                'title': f"⭐ '{film['title']}' domina le ultime 24 ore!",
                'content': f"Con {total_likes} like totali è il film più amato della giornata.",
                'link': f"/film/{film['id']}",
                'timestamp': 'Ultime 24 ore'
            })
    
    # 3. Recently discovered stars
    new_stars = await db.people.find(
        {'is_discovered_star': True, 'discovered_at': {'$gte': one_day_ago.isoformat()}},
        {'_id': 0, 'id': 1, 'name': 1, 'discovered_by': 1, 'stars': 1}
    ).sort('discovered_at', -1).limit(3).to_list(3)
    
    for star in new_stars:
        discoverer = await db.users.find_one({'id': star.get('discovered_by')}, {'_id': 0, 'nickname': 1})
        news.append({
            'category': 'star',
            'title': f"⭐ Nuova stella scoperta: {star['name']}!",
            'content': f"Scoperta da {discoverer.get('nickname', 'Unknown') if discoverer else 'Unknown'}. {star.get('stars', 3)} stelle di talento!",
            'link': None,
            'timestamp': 'Nuova scoperta'
        })
    
    # 4. Films that broke attendance records
    record_films = await db.films.find(
        {'cumulative_attendance': {'$gt': 100000}},
        {'_id': 0, 'id': 1, 'title': 1, 'cumulative_attendance': 1}
    ).sort('cumulative_attendance', -1).limit(2).to_list(2)
    
    for film in record_films:
        attendance = film.get('cumulative_attendance', 0)
        if attendance > 500000:
            news.append({
                'category': 'record',
                'title': f"🏆 RECORD! '{film['title']}' supera {attendance:,} spettatori!",
                'content': "Un traguardo storico per il cinema!",
                'link': f"/film/{film['id']}",
                'timestamp': 'Record'
            })
        elif attendance > 100000:
            news.append({
                'category': 'record',
                'title': f"📈 '{film['title']}' raggiunge {attendance:,} spettatori",
                'content': "Il pubblico continua ad affluire nei cinema!",
                'link': f"/film/{film['id']}",
                'timestamp': 'Milestone'
            })
    
    # 5. Top rated films of the week
    top_rated = await db.films.find(
        {'imdb_rating': {'$gt': 8.0}},
        {'_id': 0, 'id': 1, 'title': 1, 'imdb_rating': 1}
    ).sort('imdb_rating', -1).limit(2).to_list(2)
    
    for film in top_rated:
        news.append({
            'category': 'record',
            'title': f"🎬 '{film['title']}' con rating {film.get('imdb_rating', 0):.1f}/10!",
            'content': "Un capolavoro apprezzato dalla critica.",
            'link': f"/film/{film['id']}",
            'timestamp': 'Top Rated'
        })
    
    # 6. New majors or major news
    new_majors = await db.majors.find(
        {},
        {'_id': 0, 'id': 1, 'name': 1, 'created_at': 1}
    ).sort('created_at', -1).limit(2).to_list(2)
    
    for major in new_majors:
        news.append({
            'category': 'news',
            'title': f"🏢 Nuova Major: {major['name']}",
            'content': "Una nuova casa di produzione entra nel mercato cinematografico!",
            'link': f"/major/{major['id']}",
            'timestamp': 'Major'
        })
    
    # 7. Films with most awards
    awarded_films = await db.films.find(
        {'awards': {'$exists': True, '$ne': []}},
        {'_id': 0, 'id': 1, 'title': 1, 'awards': 1}
    ).to_list(100)
    
    awarded_films.sort(key=lambda x: len(x.get('awards', [])), reverse=True)
    
    for film in awarded_films[:2]:
        award_count = len(film.get('awards', []))
        if award_count > 0:
            news.append({
                'category': 'record',
                'title': f"🏆 '{film['title']}' vince {award_count} premi!",
                'content': "Un film pluripremiato che sta facendo storia.",
                'link': f"/film/{film['id']}",
                'timestamp': 'Premi'
            })
    
    return {'news': news}


# ==================== RELEASE NOTES ====================

@router.get("/release-notes")
async def get_release_notes():
    """Get all release notes from database, sorted by newest first."""
    # Try to get from database first
    db_notes = await db.release_notes.find({}, {'_id': 0}).sort('version', -1).to_list(1000)
    
    if db_notes:
        current_version = db_notes[0]['version'] if db_notes else '0.000'
        return {
            'current_version': current_version,
            'releases': db_notes,
            'total_releases': len(db_notes),
            'source': 'database'
        }
    else:
        # Fallback to static list
        current_version = RELEASE_NOTES[0]['version'] if RELEASE_NOTES else '0.000'
        return {
            'current_version': current_version,
            'releases': RELEASE_NOTES,
            'total_releases': len(RELEASE_NOTES),
            'source': 'static'
        }

@router.post("/release-notes")
async def add_release_note_endpoint(data: dict, user: dict = Depends(get_current_user)):
    """Add a new release note (Creator only). Auto-increments version."""
    if user.get('nickname') != CREATOR_NICKNAME:
        raise HTTPException(status_code=403, detail="Solo il Creator può aggiungere note di rilascio")
    
    title = data.get('title', '')
    changes = data.get('changes', [])
    
    if not title or not changes:
        raise HTTPException(status_code=400, detail="Titolo e modifiche sono obbligatori")
    
    # Auto-calculate next version from DB
    latest = await db.release_notes.find_one({}, {'_id': 0, 'version': 1}, sort=[('version', -1)])
    if latest:
        parts = latest['version'].split('.')
        next_version = f"{parts[0]}.{str(int(parts[1]) + 1).zfill(3)}"
    else:
        next_version = '0.077'
    
    # Allow manual version override
    if data.get('version'):
        next_version = data['version']
    
    note = {
        'id': str(uuid.uuid4()),
        'version': next_version,
        'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'title': title,
        'changes': [{'type': c.get('type', 'new'), 'text': c['text']} for c in changes],
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.release_notes.insert_one(note)
    del note['_id']
    
    return {'message': f'Release note v{next_version} aggiunta', 'release_note': note}

@router.get("/release-notes/unread-count")
async def get_unread_release_notes_count(user: dict = Depends(get_current_user)):
    """Get count of release notes the user hasn't seen yet."""
    last_seen = user.get('last_seen_release_version', '0.000')
    
    # Get releases newer than what user has seen
    db_notes = await db.release_notes.find({}, {'_id': 0, 'version': 1}).sort('version', -1).to_list(1000)
    
    if not db_notes:
        db_notes = [{'version': r['version']} for r in RELEASE_NOTES]
    
    # Count versions newer than last_seen
    unread_count = 0
    for note in db_notes:
        if note['version'] > last_seen:
            unread_count += 1
        else:
            break  # Notes are sorted desc, so we can stop
    
    latest_version = db_notes[0]['version'] if db_notes else '0.000'
    
    return {
        'unread_count': unread_count,
        'last_seen_version': last_seen,
        'latest_version': latest_version
    }

@router.post("/release-notes/mark-read")
async def mark_release_notes_read(user: dict = Depends(get_current_user)):
    """Mark all release notes as read for the user."""
    # Get latest version
    db_notes = await db.release_notes.find({}, {'_id': 0, 'version': 1}).sort('version', -1).limit(1).to_list(1)
    
    if db_notes:
        latest_version = db_notes[0]['version']
    else:
        latest_version = RELEASE_NOTES[0]['version'] if RELEASE_NOTES else '0.000'
    
    # Update user's last seen version
    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'last_seen_release_version': latest_version}}
    )
    
    return {
        'success': True,
        'marked_version': latest_version
    }

@router.post("/admin/release-notes")
async def create_release_note(note: NewReleaseNote):
    """
    Create a new release note. 
    This endpoint is called by the system when new features are implemented.
    """
    # Calculate version if not provided
    version = note.version
    if not version:
        # Get highest version from database
        latest = await db.release_notes.find_one({}, sort=[('version', -1)])
        if latest:
            parts = latest['version'].split('.')
            major = int(parts[0])
            minor = int(parts[1])
            version = f"{major}.{str(minor + 1).zfill(3)}"
        else:
            version = '0.050'  # Start from 0.050 if database is empty
    
    # Add the release note
    await add_release_note_to_db(version, note.title, note.changes)
    
    return {
        'success': True,
        'version': version,
        'title': note.title,
        'message': f'Release note v{version} aggiunta con successo!'
    }


# ==================== LEADERBOARD ====================

@router.get("/leaderboard/local/{country}")
async def get_local_leaderboard(country: str, limit: int = 50):
    """Get local leaderboard by country."""
    # Get users with infrastructure in this country
    infra_owners = await db.infrastructure.distinct('owner_id', {'country': country})
    
    users = await db.users.find(
        {'id': {'$in': infra_owners}},
        {'_id': 0, 'password': 0}
    ).to_list(1000)
    
    for user in users:
        user['leaderboard_score'] = calculate_leaderboard_score(user)
        user['level_info'] = get_level_from_xp(user.get('total_xp', 0))
        user['fame_tier'] = get_fame_tier(user.get('fame', 50))
    
    sorted_users = sorted(users, key=lambda x: x['leaderboard_score'], reverse=True)[:limit]
    
    for i, user in enumerate(sorted_users):
        user['rank'] = i + 1
    
    return {'leaderboard': sorted_users, 'country': country}


# ==================== CINEBOARD RANKINGS ====================

@router.get("/cineboard/now-playing")
async def get_cineboard_now_playing(user: dict = Depends(get_current_user)):
    """Get top 50 films currently in theaters, ranked by CineBoard score."""
    cached = _cache.get('cineboard_now_playing', ttl=30)
    if cached:
        user_liked_ids = _cache.get(f'np_likes_{user["id"]}', ttl=30)
        if user_liked_ids is None:
            user_liked_films = await db.films.find(
                {'status': 'in_theaters', 'liked_by': user['id']},
                {'_id': 0, 'id': 1}
            ).to_list(500)
            user_liked_ids = set(f['id'] for f in user_liked_films)
            _cache.set(f'np_likes_{user["id"]}', user_liked_ids)
        for f in cached:
            f['user_liked'] = f.get('id') in user_liked_ids
        return {'films': cached}
    
    import asyncio as _asyncio
    FILM_PROJECTION = {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'genre': 1, 'subgenre': 1,
        'poster_url': 1, 'imdb_rating': 1, 'quality_score': 1, 'quality': 1, 'likes_count': 1,
        'total_revenue': 1, 'opening_day_revenue': 1,
        'released_at': 1, 'release_date': 1, 'created_at': 1, 'status': 1,
        'realistic_box_office': 1, 'total_attendance': 1, 'cineboard_score': 1,
        'estimated_final_revenue': 1,
        'awards': 1, 'actual_weeks_in_theater': 1, 'weeks_in_theater': 1}
    
    films_future = db.films.find(
        {'status': 'in_theaters'},
        FILM_PROJECTION
    ).to_list(500)
    liked_future = db.films.find(
        {'status': 'in_theaters', 'liked_by': user['id']},
        {'_id': 0, 'id': 1}
    ).to_list(500)
    
    films, user_liked_films = await _asyncio.gather(films_future, liked_future)
    user_liked_ids = set(f['id'] for f in user_liked_films)
    _cache.set(f'np_likes_{user["id"]}', user_liked_ids)
    
    # Bulk fetch owners
    owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
    owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
    owners_map = {o['id']: o for o in owners_list}
    
    for film in films:
        film['cineboard_score'] = calculate_cineboard_score(film)
        film['owner'] = owners_map.get(film.get('user_id'))
        film['user_liked'] = film.get('id') in user_liked_ids
    
    sorted_films = sorted(films, key=lambda x: x['cineboard_score'], reverse=True)[:50]
    for i, film in enumerate(sorted_films):
        film['rank'] = i + 1
    
    _cache.set('cineboard_now_playing', sorted_films)
    return {'films': sorted_films}

@router.get("/cineboard/hall-of-fame")
async def get_cineboard_hall_of_fame(user: dict = Depends(get_current_user)):
    """Get all-time top films (Hall of Fame), ranked by CineBoard score."""
    cached = _cache.get('cineboard_hall_of_fame', ttl=60)
    if cached:
        user_liked_ids = _cache.get(f'hof_likes_{user["id"]}', ttl=60)
        if user_liked_ids is None:
            user_liked_films = await db.films.find(
                {'status': {'$in': ['completed', 'in_theaters']}, 'liked_by': user['id']},
                {'_id': 0, 'id': 1}
            ).to_list(1000)
            user_liked_ids = set(f['id'] for f in user_liked_films)
            _cache.set(f'hof_likes_{user["id"]}', user_liked_ids)
        for f in cached:
            f['user_liked'] = f.get('id') in user_liked_ids
        return {'films': cached}
    
    import asyncio as _asyncio
    HOF_PROJECTION = {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'genre': 1, 'subgenre': 1,
        'poster_url': 1, 'imdb_rating': 1, 'quality_score': 1, 'quality': 1, 'likes_count': 1,
        'total_revenue': 1, 'opening_day_revenue': 1,
        'released_at': 1, 'release_date': 1, 'created_at': 1, 'status': 1,
        'realistic_box_office': 1, 'total_attendance': 1, 'cineboard_score': 1,
        'estimated_final_revenue': 1,
        'awards': 1, 'actual_weeks_in_theater': 1, 'weeks_in_theater': 1}
    
    films_future = db.films.find(
        {'status': {'$in': ['completed', 'in_theaters']}},
        HOF_PROJECTION
    ).to_list(1000)
    liked_future = db.films.find(
        {'status': {'$in': ['completed', 'in_theaters']}, 'liked_by': user['id']},
        {'_id': 0, 'id': 1}
    ).to_list(1000)
    
    films, user_liked_films = await _asyncio.gather(films_future, liked_future)
    user_liked_ids = set(f['id'] for f in user_liked_films)
    _cache.set(f'hof_likes_{user["id"]}', user_liked_ids)
    
    owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
    owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
    owners_map = {o['id']: o for o in owners_list}
    
    for film in films:
        film['cineboard_score'] = calculate_cineboard_score(film)
        film['owner'] = owners_map.get(film.get('user_id'))
        film['user_liked'] = film.get('id') in user_liked_ids
        film['hall_of_fame'] = film['cineboard_score'] >= 60
    
    sorted_films = sorted(films, key=lambda x: x['cineboard_score'], reverse=True)[:100]
    for i, film in enumerate(sorted_films):
        film['rank'] = i + 1
    
    _cache.set('cineboard_hall_of_fame', sorted_films)
    return {'films': sorted_films}

@router.get("/cineboard/daily")
async def get_cineboard_daily(user: dict = Depends(get_current_user)):
    """Get today's top films ranked by daily revenue with hourly trend."""
    cached = _cache.get('cineboard_daily', ttl=30)
    if cached:
        for f in cached:
            f['user_liked'] = user['id'] in f.get('liked_by', [])
        return {'films': cached}
    
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    FILM_PROJECTION = {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'genre': 1, 'subgenre': 1,
        'poster_url': 1, 'imdb_rating': 1, 'quality_score': 1, 'quality': 1, 'likes_count': 1,
        'liked_by': 1, 'daily_revenues': 1, 'total_revenue': 1, 'opening_day_revenue': 1,
        'released_at': 1, 'release_date': 1, 'created_at': 1, 'status': 1,
        'realistic_box_office': 1, 'total_attendance': 1, 'cineboard_score': 1,
        'weekly_revenues': 1, 'estimated_final_revenue': 1}
    films = await db.films.find(
        {'status': 'in_theaters'},
        FILM_PROJECTION
    ).to_list(500)

    # Bulk fetch owners
    owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
    owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
    owners_map = {o['id']: o for o in owners_list}

    for film in films:
        daily_rev = 0
        for dr in film.get('daily_revenues', []):
            dr_date = dr.get('date', '')
            if dr_date:
                try:
                    d = datetime.fromisoformat(dr_date.replace('Z', '+00:00'))
                    if d >= today_start:
                        daily_rev += dr.get('amount', 0)
                except Exception:
                    pass
        
        # Calculate days since release for decay
        quality = film.get('quality_score', film.get('quality', 50))
        released_at = film.get('released_at', film.get('release_date', film.get('created_at', now.isoformat())))
        try:
            rd = datetime.fromisoformat(str(released_at).replace('Z', '+00:00'))
            days_old = max(0, (now - rd).total_seconds() / 86400)
        except Exception:
            rd = now - timedelta(days=30)
            days_old = 30
        
        if daily_rev <= 0:
            total_rev = film.get('total_revenue', 0)
            if quality >= 90:
                decay = 0.92 ** days_old
            elif quality >= 80:
                decay = 0.85 ** days_old
            elif quality >= 65:
                decay = 0.78 ** days_old
            else:
                decay = 0.70 ** days_old
            daily_rev = total_rev * 0.05 * decay
        
        # Generate 6 bars: 4-hour blocks since release (showing decay pattern)
        opening_rev = film.get('opening_day_revenue', film.get('total_revenue', 100000) * 0.05)
        if quality >= 90:
            block_decay = 0.92
        elif quality >= 80:
            block_decay = 0.85
        elif quality >= 65:
            block_decay = 0.78
        else:
            block_decay = 0.70
        
        hourly_blocks = []
        for i in range(6):
            block_day = days_old - 1 + (i * 4 / 24)  # Spread across today
            block_rev = opening_rev * (block_decay ** max(0, block_day)) * (1.0 - i * 0.08)
            label = f'{i*4}-{(i+1)*4}h'
            hourly_blocks.append({'hour': label, 'revenue': round(max(0, block_rev))})
        
        film['daily_revenue'] = round(daily_rev)
        film['hourly_trend'] = hourly_blocks
        film['cineboard_score'] = calculate_cineboard_score(film)
        film['owner'] = owners_map.get(film.get('user_id'))
        film['user_liked'] = user['id'] in film.get('liked_by', [])

    sorted_films = sorted(films, key=lambda x: x['daily_revenue'], reverse=True)[:50]
    for i, film in enumerate(sorted_films):
        film['rank'] = i + 1

    _cache.set('cineboard_daily', sorted_films)
    return {'films': sorted_films}

@router.get("/cineboard/weekly")
async def get_cineboard_weekly(user: dict = Depends(get_current_user)):
    """Get this week's top films ranked by weekly revenue with daily trend."""
    cached = _cache.get('cineboard_weekly', ttl=30)
    if cached:
        for f in cached:
            f['user_liked'] = user['id'] in f.get('liked_by', [])
        return {'films': cached}
    
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    FILM_PROJECTION = {'_id': 0, 'id': 1, 'title': 1, 'user_id': 1, 'genre': 1, 'subgenre': 1,
        'poster_url': 1, 'imdb_rating': 1, 'quality_score': 1, 'quality': 1, 'likes_count': 1,
        'liked_by': 1, 'daily_revenues': 1, 'total_revenue': 1, 'opening_day_revenue': 1,
        'released_at': 1, 'release_date': 1, 'created_at': 1, 'status': 1,
        'realistic_box_office': 1, 'total_attendance': 1, 'cineboard_score': 1,
        'weekly_revenues': 1, 'estimated_final_revenue': 1}
    films = await db.films.find(
        {'status': 'in_theaters'},
        FILM_PROJECTION
    ).to_list(500)

    # Bulk fetch owners
    owner_ids = list(set(f.get('user_id') for f in films if f.get('user_id')))
    owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1, 'badge': 1, 'badge_expiry': 1, 'badges': 1}).to_list(len(owner_ids))
    owners_map = {o['id']: o for o in owners_list}

    for film in films:
        weekly_rev = 0
        daily_trend = {}
        for dr in film.get('daily_revenues', []):
            dr_date = dr.get('date', '')
            if dr_date:
                try:
                    d = datetime.fromisoformat(dr_date.replace('Z', '+00:00'))
                    if d >= week_start:
                        amt = dr.get('amount', 0)
                        weekly_rev += amt
                        daily_trend[d.strftime('%Y-%m-%d')] = daily_trend.get(d.strftime('%Y-%m-%d'), 0) + amt
                except Exception:
                    pass
        if weekly_rev <= 0:
            # Fallback: estimate weekly revenue with decay
            total_rev = film.get('total_revenue', 0)
            quality = film.get('quality_score', film.get('quality', 50))
            released_at = film.get('released_at', film.get('release_date', film.get('created_at', now.isoformat())))
            try:
                rd = datetime.fromisoformat(str(released_at).replace('Z', '+00:00'))
                days_old = max(0, (now - rd).total_seconds() / 86400)
            except Exception:
                days_old = 30
            
            if quality >= 90:
                decay = 0.92 ** max(0, days_old - 7)
            elif quality >= 80:
                decay = 0.85 ** max(0, days_old - 7)
            elif quality >= 65:
                decay = 0.78 ** max(0, days_old - 7)
            else:
                decay = 0.70 ** max(0, days_old - 7)
            
            weekly_rev = total_rev * 0.25 * decay
            for i in range(7):
                day = (now - timedelta(days=6-i)).strftime('%Y-%m-%d')
                daily_trend[day] = round(weekly_rev / 7 * (1 + (i - 3) * 0.05))
        
        # Generate 7 bars: one for each day since release (release-relative trend)
        released_at = film.get('released_at', film.get('release_date', film.get('created_at', now.isoformat())))
        try:
            rd = datetime.fromisoformat(str(released_at).replace('Z', '+00:00'))
        except Exception:
            rd = now - timedelta(days=30)
        
        quality = film.get('quality_score', film.get('quality', 50))
        opening_rev = film.get('opening_day_revenue', film.get('total_revenue', 100000) * 0.05)
        
        if quality >= 90:
            day_decay = 0.92
        elif quality >= 80:
            day_decay = 0.85
        elif quality >= 65:
            day_decay = 0.78
        else:
            day_decay = 0.70
        
        daily_trend_since_release = []
        for i in range(7):
            day_rev = opening_rev * (day_decay ** i)
            daily_trend_since_release.append({'day': f'G{i+1}', 'revenue': round(max(0, day_rev))})
        
        film['weekly_revenue'] = round(weekly_rev)
        film['daily_trend'] = daily_trend_since_release
        film['cineboard_score'] = calculate_cineboard_score(film)
        film['owner'] = owners_map.get(film.get('user_id'))
        film['user_liked'] = user['id'] in film.get('liked_by', [])

    sorted_films = sorted(films, key=lambda x: x['weekly_revenue'], reverse=True)[:50]
    for i, film in enumerate(sorted_films):
        film['rank'] = i + 1

    _cache.set('cineboard_weekly', sorted_films)
    return {'films': sorted_films}

@router.get("/cineboard/series-weekly")
async def get_cineboard_series_weekly(user: dict = Depends(get_current_user)):
    """Get this week's top TV series ranked by quality."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).isoformat()
    
    series = await db.tv_series.find(
        {'type': 'tv_series', 'status': 'completed', 'completed_at': {'$gte': week_start}},
        {'_id': 0}
    ).sort('quality_score', -1).to_list(20)
    
    if len(series) < 5:
        extra = await db.tv_series.find(
            {'type': 'tv_series', 'status': 'completed', 'id': {'$nin': [s['id'] for s in series]}},
            {'_id': 0}
        ).sort('quality_score', -1).to_list(20 - len(series))
        series.extend(extra)
    
    owner_ids = list(set(s.get('user_id') for s in series if s.get('user_id')))
    owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1}).to_list(len(owner_ids) + 1)
    owners_map = {o['id']: o for o in owners_list}
    
    for i, s in enumerate(series):
        s['rank'] = i + 1
        s['owner'] = owners_map.get(s.get('user_id'))
        completed = s.get('completed_at', '')
        try:
            d = datetime.fromisoformat(completed)
            s['is_new'] = d >= (now - timedelta(days=7))
        except Exception:
            s['is_new'] = False
    
    return {'series': series}

@router.get("/cineboard/anime-weekly")
async def get_cineboard_anime_weekly(user: dict = Depends(get_current_user)):
    """Get this week's top anime ranked by quality."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).isoformat()
    
    series = await db.tv_series.find(
        {'type': 'anime', 'status': 'completed', 'completed_at': {'$gte': week_start}},
        {'_id': 0}
    ).sort('quality_score', -1).to_list(20)
    
    if len(series) < 5:
        extra = await db.tv_series.find(
            {'type': 'anime', 'status': 'completed', 'id': {'$nin': [s['id'] for s in series]}},
            {'_id': 0}
        ).sort('quality_score', -1).to_list(20 - len(series))
        series.extend(extra)
    
    owner_ids = list(set(s.get('user_id') for s in series if s.get('user_id')))
    owners_list = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1, 'production_house_name': 1}).to_list(len(owner_ids) + 1)
    owners_map = {o['id']: o for o in owners_list}
    
    for i, s in enumerate(series):
        s['rank'] = i + 1
        s['owner'] = owners_map.get(s.get('user_id'))
        completed = s.get('completed_at', '')
        try:
            d = datetime.fromisoformat(completed)
            s['is_new'] = d >= (now - timedelta(days=7))
        except Exception:
            s['is_new'] = False
    
    return {'series': series}

@router.get("/cineboard/tv-stations-alltime")
async def get_cineboard_tv_stations_alltime(user: dict = Depends(get_current_user)):
    """Top TV stations by total viewers of all time."""
    stations = await db.tv_stations.find(
        {'setup_complete': True},
        {'_id': 0, 'id': 1, 'station_name': 1, 'nation': 1, 'user_id': 1, 'owner_nickname': 1,
         'total_viewers': 1, 'total_revenue': 1, 'current_share': 1, 'contents': 1}
    ).sort('total_viewers', -1).to_list(20)
    
    for i, s in enumerate(stations):
        s['rank'] = i + 1
        contents = s.get('contents', {})
        s['content_count'] = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
        del s['contents']
    
    return {'stations': stations}

@router.get("/cineboard/tv-stations-weekly")
async def get_cineboard_tv_stations_weekly(user: dict = Depends(get_current_user)):
    """Top TV stations by weekly share (updated from last 7 days revenue)."""
    stations = await db.tv_stations.find(
        {'setup_complete': True},
        {'_id': 0, 'id': 1, 'station_name': 1, 'nation': 1, 'user_id': 1, 'owner_nickname': 1,
         'total_viewers': 1, 'total_revenue': 1, 'current_share': 1, 'contents': 1}
    ).sort('current_share', -1).to_list(20)
    
    for i, s in enumerate(stations):
        s['rank'] = i + 1
        contents = s.get('contents', {})
        s['content_count'] = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
        del s['contents']
    
    return {'stations': stations}

@router.get("/cineboard/tv-stations-daily")
async def get_cineboard_tv_stations_daily(user: dict = Depends(get_current_user)):
    """Top TV stations by daily share (live snapshot, updates every 5 min)."""
    from routes.tv_stations import _calc_share_and_revenue, BASE_HOURLY_VIEWERS, AD_REVENUE_PER_1K, SHARE_PENALTY_PER_AD_SECOND
    import random
    
    stations = await db.tv_stations.find(
        {'setup_complete': True},
        {'_id': 0}
    ).to_list(50)
    
    results = []
    for s in stations:
        contents = s.get('contents', {})
        total_content = len(contents.get('films', [])) + len(contents.get('tv_series', [])) + len(contents.get('anime', []))
        
        # Fetch quality scores for live calculation
        film_ids = [c['content_id'] for c in contents.get('films', [])]
        series_ids = [c['content_id'] for c in contents.get('tv_series', []) + contents.get('anime', [])]
        qualities = []
        if film_ids:
            films = await db.films.find({'id': {'$in': film_ids}}, {'_id': 0, 'quality_score': 1}).to_list(100)
            qualities.extend([f.get('quality_score', 50) for f in films])
        if series_ids:
            series_docs = await db.tv_series.find({'id': {'$in': series_ids}}, {'_id': 0, 'quality_score': 1}).to_list(100)
            qualities.extend([sd.get('quality_score', 50) for sd in series_docs])
        
        avg_quality = sum(qualities) / max(1, len(qualities)) if qualities else 50
        ad_seconds = s.get('ad_seconds', 30)
        
        share_base = (avg_quality / 100) * 20
        ad_penalty = ad_seconds * SHARE_PENALTY_PER_AD_SECOND * 0.1
        volume_bonus = min(5, total_content * 0.5)
        variation = random.uniform(-1.0, 1.0)
        live_share = max(0.5, min(30, share_base - ad_penalty + volume_bonus + variation))
        
        results.append({
            'id': s['id'],
            'station_name': s['station_name'],
            'nation': s['nation'],
            'user_id': s['user_id'],
            'owner_nickname': s.get('owner_nickname', '?'),
            'live_share': round(live_share, 1),
            'total_revenue': s.get('total_revenue', 0),
            'total_viewers': s.get('total_viewers', 0),
            'content_count': total_content,
        })
    
    results.sort(key=lambda x: x['live_share'], reverse=True)
    for i, r in enumerate(results):
        r['rank'] = i + 1
    
    return {'stations': results}
