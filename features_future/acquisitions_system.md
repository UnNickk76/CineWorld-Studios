# Sistema Acquisizioni - Game Design Document

## Panoramica
Le Major possono acquisire studi indipendenti, IP di altri giocatori o intere Major rivali attraverso un sistema di offerte e negoziazioni.

## Funzionalita Previste
- Offerta di acquisizione a studi indipendenti (giocatori senza Major)
- Acquisizione hostile di Major rivali (richiede superiorita economica)
- Fusione consensuale tra Major alleate
- Acquisizione IP specifiche (franchise, personaggi)
- Difesa anti-acquisizione (poison pill, white knight)

## Economia
- Le acquisizioni costano una percentuale del valore totale del target
- Lo studio acquisito genera revenue passiva per la Major
- Le acquisizioni ostili hanno un costo premium (2-3x)
- Limite massimo di acquisizioni per evitare monopoli

## Fasi di Implementazione
1. Schema DB acquisitions, acquisition_offers
2. Calcolo valore studio/Major
3. Endpoint offerta, accettazione, rifiuto
4. Timer per offerte (scadenza 48h)
5. UI notifiche e gestione offerte
6. Integrazione con sistema Major per merger

## Note
- Documento preparatorio. Implementazione futura.
