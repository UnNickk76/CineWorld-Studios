# Piattaforma Streaming - Game Design Document

## Panoramica
Ogni giocatore o Major puo lanciare la propria piattaforma di streaming in-game per distribuire contenuti e generare ricavi ricorrenti.

## Funzionalita Previste
- Creazione piattaforma streaming (nome, logo, catalogo)
- Acquisizione diritti di film/serie da altri giocatori
- Abbonati virtuali basati su qualita del catalogo
- Revenue ricorrente mensile (nel tick automatico)
- Esclusive: contenuti disponibili solo sulla propria piattaforma
- Competizione tra piattaforme per il numero di abbonati

## Economia
- Costo lancio piattaforma elevato
- Revenue mensile passiva
- Costo acquisizione diritti basato su popolarita del contenuto
- Abbonati fluttuano in base alla qualita media del catalogo

## Fasi di Implementazione
1. Schema DB streaming_platforms, content_rights, subscribers
2. Endpoint gestione piattaforma e acquisizione diritti
3. Marketplace diritti streaming
4. Dashboard piattaforma con metriche abbonati
5. Integrazione auto-tick per revenue ricorrente

## Note
- Documento preparatorio. Implementazione futura.
