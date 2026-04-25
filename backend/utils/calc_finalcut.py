"""
calc_finalcut.py — Calcolo durata Final Cut (3-48 ore reali)

Fattori:
- Formato film (corto = veloce, kolossal = lento)
- Giorni di riprese effettuati
- CGI/VFX (post-produzione piu lunga)
- Genere (animazione/sci-fi richiedono piu post)
"""

FORMAT_BASE_HOURS = {
    "cortometraggio": 3,
    "medio": 6,
    "standard": 12,
    "epico": 24,
    "kolossal": 36,
}

GENRE_POSTPROD_MULT = {
    "animation": 1.8,
    "sci_fi": 1.4,
    "fantasy": 1.3,
    "action": 1.2,
    "war": 1.2,
    "horror": 1.1,
    "adventure": 1.15,
    "thriller": 1.0,
    "drama": 0.9,
    "comedy": 0.85,
    "romance": 0.8,
    "documentary": 0.7,
    "biographical": 0.85,
    "mystery": 0.95,
    "musical": 1.1,
    "western": 0.95,
    "crime": 1.0,
    "noir": 0.9,
    "historical": 1.1,
}

CGI_HOURS = {
    "basic_cgi": 2,
    "advanced_cgi": 5,
    "full_cgi": 10,
}

VFX_HOURS = {
    "explosions": 2,
    "creatures": 4,
    "environments": 3,
    "de_aging": 3,
}


def calculate_finalcut_hours(project: dict) -> int:
    """Calcola le ore di post-produzione. Range: 3-48."""
    film_format = project.get("film_format", "standard")
    genre = project.get("genre", "drama")
    shooting_days = project.get("shooting_days", 14)
    cgi = project.get("prep_cgi", [])
    vfx = project.get("prep_vfx", [])

    base = FORMAT_BASE_HOURS.get(film_format, 12)
    mult = GENRE_POSTPROD_MULT.get(genre, 1.0)

    # Shooting days factor: more shooting = slightly more editing
    shoot_bonus = max(0, (shooting_days - 10) * 0.3)

    cgi_extra = sum(CGI_HOURS.get(c, 0) for c in cgi)
    vfx_extra = sum(VFX_HOURS.get(v, 0) for v in vfx)

    total = (base * mult) + shoot_bonus + cgi_extra + vfx_extra

    return max(3, min(48, round(total)))


# ~100 messaggi rotanti durante il Final Cut (in italiano)
FINALCUT_MESSAGES = [
    "Sincronizzazione audio e video in corso...",
    "Il montatore sta analizzando le scene migliori...",
    "Correzione colore della scena d'apertura...",
    "Taglio delle scene superflue...",
    "Aggiunta delle transizioni tra le sequenze...",
    "Mixaggio della colonna sonora...",
    "Bilanciamento dei livelli audio...",
    "Revisione del ritmo narrativo...",
    "Inserimento degli effetti sonori ambientali...",
    "Ottimizzazione della fotografia...",
    "Il regista sta rivedendo il primo montaggio...",
    "Rifinitura dei dialoghi in post-produzione...",
    "Stabilizzazione delle riprese in movimento...",
    "Aggiunta dei titoli di testa...",
    "Rendering delle scene in CGI...",
    "Compositing degli effetti visivi...",
    "Correzione delle imperfezioni visive...",
    "Il colorist sta lavorando alla palette cromatica...",
    "Inserimento della musica di sottofondo...",
    "Taglio e cucitura delle scene d'azione...",
    "Revisione della continuita tra le scene...",
    "Aggiunta degli effetti di transizione...",
    "Sincronizzazione del labiale...",
    "Ottimizzazione della scena climax...",
    "Rifinitura del finale del film...",
    "Mixaggio finale in Dolby Surround...",
    "Il sound designer crea atmosfere uniche...",
    "Inserimento dei sottotitoli...",
    "Revisione del montaggio alternato...",
    "Correzione della grana dell'immagine...",
    "Aggiunta del logo della casa di produzione...",
    "Il regista approva la scena del confronto...",
    "Rifinitura delle scene romantiche...",
    "Ottimizzazione dei tempi comici...",
    "Bilanciamento delle scene di tensione...",
    "Aggiunta della dissolvenza in chiusura...",
    "Rendering finale delle scene notturne...",
    "Revisione del flashback centrale...",
    "Aggiunta degli effetti di pioggia digitale...",
    "Il montatore taglia 15 minuti superflui...",
    "Inserimento del tema musicale principale...",
    "Correzione dell'esposizione nelle scene esterne...",
    "Aggiunta dei crediti finali...",
    "Revisione dell'arco narrativo del protagonista...",
    "Ottimizzazione della scena d'inseguimento...",
    "Il colorist aggiunge toni caldi al tramonto...",
    "Sincronizzazione dei movimenti di camera...",
    "Rifinitura della scena del colpo di scena...",
    "Aggiunta del sonoro ambientale della citta...",
    "Rendering degli effetti particellari...",
    "Revisione del montaggio parallelo...",
    "Il regista vuole rifare il finale...",
    "Aggiunta delle scritte in sovrimpressione...",
    "Correzione del bilanciamento del bianco...",
    "Ottimizzazione della scena onirica...",
    "Mixaggio della voce narrante...",
    "Inserimento degli effetti di slow-motion...",
    "Il montatore riordina le sequenze temporali...",
    "Aggiunta della colonna sonora orchestrale...",
    "Rifinitura delle scene di massa...",
    "Correzione delle ombre nelle scene interne...",
    "Rendering delle esplosioni in CGI...",
    "Revisione del pacing del secondo atto...",
    "Il sound designer aggiunge il battito cardiaco...",
    "Aggiunta del filtro vintage alle scene retro...",
    "Ottimizzazione della scena subacquea...",
    "Inserimento dei rumori di fondo realistici...",
    "Correzione del contrasto nelle scene buie...",
    "Il regista e soddisfatto della scena madre...",
    "Aggiunta delle particelle di polvere atmosferica...",
    "Rifinitura della scena di apertura...",
    "Rendering delle creature digitali...",
    "Mixaggio dei livelli di dialogo e musica...",
    "Revisione dell'epilogo...",
    "Aggiunta degli easter egg nascosti...",
    "Il colorist crea il look definitivo del film...",
    "Ottimizzazione delle scene di volo...",
    "Inserimento del tema dell'antagonista...",
    "Correzione dei riflessi nelle scene con vetro...",
    "Aggiunta delle dissolvenze incrociate...",
    "Rifinitura della colonna sonora emotiva...",
    "Il montatore lavora alla versione Director's Cut...",
    "Rendering finale a risoluzione 4K...",
    "Revisione complessiva del montaggio...",
    "Aggiunta dei suoni foley personalizzati...",
    "Ottimizzazione della compressione dinamica...",
    "Il regista firma l'approvazione del montaggio...",
    "Inserimento del teaser per i titoli di coda...",
    "Correzione finale della timeline...",
    "Esportazione del master in formato DCP...",
    "Controllo qualita dell'output finale...",
    "Verifica della sincronizzazione su tutti i canali...",
    "Il film sta prendendo la sua forma definitiva...",
    "Preparazione del pacchetto per la distribuzione...",
    "Ultimi ritocchi al mix audio 7.1...",
    "Generazione della versione per il cinema...",
    "Il montaggio e quasi pronto...",
    "Revisione finale prima dell'approvazione...",
    "Il team di post-produzione da gli ultimi tocchi...",
    "Encoding del master file definitivo...",
]
