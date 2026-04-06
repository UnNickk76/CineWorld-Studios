# Sistema Franchise - Game Design Document

## Panoramica
Sistema per creare e gestire franchise cinematografici (sequel, prequel, spin-off, universi condivisi).

## Funzionalita Previste
- Creazione franchise da un film esistente di successo
- Sequel automatici con bonus qualita dal predecessore
- Spin-off con personaggi secondari che diventano protagonisti
- Universo condiviso tra franchise della stessa Major
- Crossover tra franchise di Major alleate

## Economia
- Costo creazione franchise: basato su revenue del film originale
- Revenue bonus crescente per ogni capitolo successivo (fedelta del pubblico)
- Rischio "franchise fatigue" se qualita scende troppo

## Fasi di Implementazione
1. Schema DB franchise (parent_film, sequels[], universe_id)
2. Logica backend per sequel/spin-off
3. UI albero franchise nel profilo
4. Bonus e malus nel sistema auto-tick

## Note
- Documento preparatorio. Implementazione futura.
