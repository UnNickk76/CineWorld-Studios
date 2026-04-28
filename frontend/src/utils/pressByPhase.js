// CineWorld Studio's — Press Quotes per fase pipeline
// =====================================================
// Frasi STAMPA coerenti con la fase reale del progetto.
// I giornali "parlano" ma in modo realistico:
//  - In fase concept/cast: indiscrezioni, trapelati, rumor, casting buzz
//  - In fase riprese: leak dal set, foto rubate, behind-the-scenes
//  - In fase post-prod: anteprime stampa, test screening
//  - In fase marketing/la_prima: hype trailer, prevendite, premiere
//  - Solo dopo l'uscita: vere recensioni post-visione

// Mappa ESTESA per stato pipeline → categoria narrativa
//   'concept'    → idea, hype, cast (rumor + casting buzz)
//   'riprese'    → prep, ciak (leak dal set)
//   'postprod'   → finalcut (montaggio, test screening)
//   'promo'      → marketing (trailer, materiali)
//   'imminente'  → la_prima, distribution, release_pending (prevendite, hype)
//
// Per ognuna, frasi differenziate per livello hype (high/mid/low).

export const PIPELINE_TO_CATEGORY = {
  // Pre-release
  idea: 'concept',
  hype: 'concept',
  cast: 'concept',
  prep: 'riprese',
  ciak: 'riprese',
  finalcut: 'postprod',
  marketing: 'promo',
  la_prima: 'imminente',
  distribution: 'imminente',
  release_pending: 'imminente',
  // Status (per LAMPO scheduled & co)
  lampo_ready: 'imminente',
  lampo_scheduled: 'imminente',
};

export const PRESS_BY_PHASE = {
  // ─── CONCEPT (idea/hype/cast): rumors e casting buzz ───────────────
  concept: {
    high: [
      'Annunciato il progetto: già si parla di evento dell\'anno',
      'Indiscrezioni dal pitch fanno scattare la curiosità',
      'Il cast in formazione promette grandi nomi',
      'Trattative in corso per attori di prima fascia',
      'Trapelato il concept: i fan sono in fermento',
      'Il progetto fa già rumore prima ancora di partire',
      'Le case di produzione si contendono i diritti',
      'Concept ambizioso, aspettative altissime',
      'Indiscrezioni dalla scrivania degli sceneggiatori',
      'Il primo trattamento avrebbe sorpreso tutti',
      'Si delinea un progetto da blockbuster',
      'Voci insistenti su un cast d\'eccezione',
      'Anche solo l\'annuncio fa tendenza',
      'Il pitch sarebbe stato accolto con entusiasmo',
      'I primi materiali concept lasciano a bocca aperta',
    ],
    mid: [
      'Annunciato un nuovo progetto, dettagli ancora scarsi',
      'Concept interessante, sviluppo da seguire',
      'Trattative casting in fase iniziale',
      'I primi rumor parlano di un progetto promettente',
      'Indiscrezioni misurate, attesa moderata',
      'Voci sul cast non ancora confermate',
      'Il concept divide gli addetti ai lavori',
      'Progetto in fase embrionale: si vedrà',
      'Sviluppo lento ma costante',
      'I primi feedback dal team sono cauti',
      'Dettagli centellinati: strategia o incertezza?',
      'Premesse buone, esecuzione tutta da scrivere',
      'Il pitch avrebbe convinto solo in parte',
      'Aspettative oneste per ora',
      'Ne sapremo di più quando partirà la pre-produzione',
    ],
    low: [
      'Annuncio sottotono: pochi se ne sono accorti',
      'Il concept fatica a generare attenzione',
      'Trattative casting al palo',
      'Indiscrezioni scarse, interesse minimo',
      'Il pitch non avrebbe convinto i piani alti',
      'Progetto in stallo? Le voci preoccupano',
      'Concept poco originale secondo gli osservatori',
      'Pochi nomi si stanno avvicinando al progetto',
      'Materiale concept sotto le aspettative',
      'L\'attenzione mediatica è quasi assente',
      'Sviluppo accidentato già nelle prime fasi',
      'I segnali iniziali sono deboli',
      'Il progetto rischia di passare inosservato',
      'Mancano elementi di richiamo',
      'Difficile costruire hype con queste premesse',
    ],
  },

  // ─── RIPRESE (prep/ciak): leak dal set ──────────────────────────
  riprese: {
    high: [
      'Avvistati sul set i protagonisti: foto già virali',
      'Le prime immagini trapelate dalle riprese sono spettacolari',
      'Locations da sogno: il film promette spettacolo',
      'Indiscrezioni dal set parlano di scene mozzafiato',
      'Il ciak iniziale sarebbe stato accolto con applausi',
      'I costumi avvistati lasciano senza fiato',
      'Effetti speciali da kolossal: voci insistenti',
      'Il cast affiatato sul set: stampa entusiasta',
      'Le foto rubate lasciano intuire un visual potente',
      'Le riprese procedono a ritmo serrato',
      'Il regista parla di "sequenze indimenticabili"',
      'I tecnici raccontano un set da grande produzione',
      'Le scenografie lasciano stupiti i visitatori',
      'I curiosi affollano le location per sbirciare',
      'Il behind-the-scenes lascia presagire qualità',
    ],
    mid: [
      'Riprese iniziate: prime foto dal set',
      'Il set procede regolarmente, niente di eclatante',
      'Qualche scatto trapelato, reazioni miste',
      'Le location scelte fanno discutere',
      'Indiscrezioni dal set ancora vaghe',
      'Le riprese hanno avuto qualche intoppo, dicono',
      'Il regista sembra concentrato ma riservato',
      'Il cast lavora in silenzio, niente leak rumorosi',
      'Costumi e scenografie nella media',
      'Le prime immagini non hanno entusiasmato',
      'Set chiuso, poche informazioni in uscita',
      'Riprese standard, dicono dagli addetti',
      'Il behind-the-scenes resta misterioso',
      'I tempi di produzione sono nella norma',
      'Aspettative bilanciate dopo i primi giorni di set',
    ],
    low: [
      'Riprese partite tra le polemiche',
      'Indiscrezioni dal set parlano di tensioni',
      'Le foto trapelate non convincono',
      'Le location scelte sembrano poco curate',
      'Si vocifera di rallentamenti sul set',
      'Cambi di sceneggiatura in corsa preoccupano',
      'Il cast sembrerebbe poco affiatato',
      'Materiale dal set sotto le aspettative',
      'Le riprese procedono a fatica',
      'Voci di problemi tecnici sul set',
      'Effetti speciali artigianali, dicono i curiosi',
      'Behind-the-scenes deludente trapelato online',
      'I costumi avvistati lasciano perplessi',
      'Il regista in difficoltà secondo le voci',
      'Set caotico, secondo testimoni anonimi',
    ],
  },

  // ─── POST-PRODUZIONE (finalcut): montaggio + test screening ────
  postprod: {
    high: [
      'Post-produzione in corso: anteprime stampa entusiastiche',
      'I test screening sarebbero stati un trionfo',
      'Il montaggio promette un ritmo travolgente',
      'Effetti speciali al top: dicono i tecnici',
      'I primi spettatori in test sono usciti commossi',
      'La colonna sonora sarebbe da brividi',
      'L\'editing sta levigando un capolavoro',
      'Reazioni eccellenti ai test privati',
      'Il sound design sarebbe rivoluzionario',
      'Si parla già di candidature tecniche',
      'I primi riscontri parlano di "esperienza unica"',
      'Il direttore della fotografia ha fatto miracoli',
      'I tempi di post-produzione si allungano per perfezionare',
      'Anteprime ai distributori finite con applausi',
      'Il film starebbe prendendo forma di evento',
    ],
    mid: [
      'Post-produzione regolare, niente eclatante',
      'Test screening con reazioni miste',
      'Il montaggio richiede più tempo del previsto',
      'Effetti speciali nella media, dicono gli addetti',
      'I primi spettatori in test si dividono',
      'Colonna sonora ancora in lavorazione',
      'L\'editing procede con tagli importanti',
      'Reazioni tiepide alle prime proiezioni private',
      'Sound design standard per il genere',
      'I test screening lasciano dubbi',
      'Si attende il taglio definitivo per giudicare',
      'Fotografia e luce nella media',
      'Tempi di post nella norma',
      'Anteprime ai distributori senza scosse',
      'Il film sta trovando la sua forma',
    ],
    low: [
      'Post-produzione travagliata: voci di rifacimenti',
      'Test screening deludenti, dicono fonti vicine',
      'Il montaggio fatica a trovare la chiave giusta',
      'Effetti speciali sotto le aspettative',
      'I test privati avrebbero generato perplessità',
      'Cambi alla colonna sonora in corsa',
      'L\'editing richiede tagli pesanti',
      'Reazioni fredde nei test screening',
      'Sound design povero, secondo le voci',
      'Si parla di reshoot necessari',
      'I primi spettatori test non sono entusiasti',
      'Fotografia poco curata, dicono i tecnici',
      'Tempi di post che si allungano per rimediare',
      'Anteprime ai distributori in salita',
      'Il film fatica a trovare la sua identità',
    ],
  },

  // ─── MARKETING (marketing): trailer + campagna ─────────────────
  promo: {
    high: [
      'Il trailer è virale: milioni di visualizzazioni in poche ore',
      'Il poster lascia il pubblico a bocca aperta',
      'Materiali promo da manuale di marketing',
      'La campagna virale fa già parlare',
      'Il trailer divide e infiamma i social',
      'Le clip diffuse hanno un impatto enorme',
      'Marketing aggressivo: tutti ne parlano',
      'Il merchandising è già esaurito',
      'Le interviste al cast generano hype massimo',
      'Trailer travolgente: aspettative oltre le stelle',
      'I poster diventano oggetti da collezione',
      'Campagna social al top: trending mondiale',
      'Tutti aspettano l\'uscita con il fiato sospeso',
      'Materiali promozionali di qualità rara',
      'Hype incontenibile dopo il trailer',
    ],
    mid: [
      'Trailer pubblicato: reazioni tiepide ma costanti',
      'Il poster non sorprende ma fa il suo',
      'Materiali promo nella media',
      'La campagna marketing va avanti senza scossoni',
      'Il trailer divide la critica',
      'Le clip diffuse passano inosservate ai più',
      'Marketing standard per il genere',
      'Il merchandising vende lentamente',
      'Le interviste al cast non emozionano',
      'Trailer ok, niente di travolgente',
      'I poster sono ben fatti ma non virali',
      'Campagna social discreta',
      'Aspettative bilanciate dopo i materiali',
      'Materiale promo sufficiente',
      'Hype costante ma non esplosivo',
    ],
    low: [
      'Trailer ignorato dai social',
      'Il poster non lascia il segno',
      'Materiali promo sotto le aspettative',
      'La campagna marketing fatica a decollare',
      'Il trailer non ha convinto',
      'Le clip diffuse non generano conversazione',
      'Marketing fallimentare secondo gli analisti',
      'Il merchandising langue sugli scaffali',
      'Le interviste al cast passano inosservate',
      'Trailer dimenticabile in poche ore',
      'I poster generano scetticismo',
      'Campagna social piatta',
      'Hype assente dopo i materiali',
      'Materiale promo deludente',
      'Difficile crederci con questa campagna',
    ],
  },

  // ─── IMMINENTE (la_prima/distribution/release_pending): hype finale ─
  imminente: {
    high: [
      'Code virtuali per i biglietti in prevendita',
      'I cinema sono già pieni per la prima settimana',
      'La premiere è un evento cinematografico globale',
      'Il pubblico conta i giorni all\'uscita',
      'Prevendite oltre ogni record',
      'Tutti i riflettori puntati sull\'uscita',
      'Si delinea un trionfo al botteghino',
      'Le sale si preparano a un\'invasione',
      'Hype al massimo storico',
      'La distribuzione è blindata su slot premium',
      'Marketing finale incendiario',
      'Il film è il più atteso del periodo',
      'Eventi speciali in tutto il mondo',
      'Streaming social del primo giorno già pianificati',
      'I distributori parlano di evento storico',
    ],
    mid: [
      'Prevendite nella media',
      'I cinema riservano slot standard',
      'La premiere passerà senza grande clamore',
      'Il pubblico si prepara con misura',
      'Prevendite oneste, niente record',
      'Riflettori accesi ma non puntati',
      'Aspettative al botteghino bilanciate',
      'Le sale aspettano di vedere',
      'Hype costante ma non esplosivo',
      'Distribuzione equilibrata',
      'Marketing finale efficace',
      'Il film è atteso dai cinefili',
      'Qualche evento speciale nelle grandi città',
      'Discussione misurata sui social',
      'I distributori sono cauti',
    ],
    low: [
      'Prevendite al lumicino',
      'Pochi cinema riservano slot generosi',
      'La premiere passerà sotto silenzio',
      'Il pubblico sembra disinteressato',
      'Prevendite preoccupanti',
      'Marketing finale debole',
      'Le sale temono buchi nel weekend di apertura',
      'Hype assente a ridosso dell\'uscita',
      'Distribuzione limitata',
      'I distributori sono pessimisti',
      'Il film esce in sordina',
      'Pochi eventi speciali pianificati',
      'Discussione marginale sui social',
      'Aspettative al botteghino bassissime',
      'Difficile vedere code ai cinema',
    ],
  },
};

// Outlets specifici per fase (per varietà narrativa)
export const OUTLETS_BY_PHASE = {
  concept: ['Variety', 'Hollywood R.', 'Deadline', 'Indie Insider', 'Screen Daily'],
  riprese: ['Set Stalker', 'Variety', 'Empire', 'CineLeaks', 'Total Film'],
  postprod: ['Variety', 'IndieWire', 'CineNews', 'Screen Daily', 'Hollywood R.'],
  promo: ['Empire', 'Total Film', 'Variety', 'Vulture', 'CineNews'],
  imminente: ['Variety', 'Empire', 'Hollywood R.', 'IndieWire', 'CineNews', 'Screen Daily'],
};

// Stati pipeline che indicano "non ancora rilasciato"
export const PRE_RELEASE_PIPELINE_STATES = new Set([
  'idea', 'hype', 'cast', 'prep', 'ciak', 'finalcut',
  'marketing', 'la_prima', 'distribution', 'release_pending',
]);

// Stati FILM/SERIE TV che indicano "non ancora rilasciato"
export const PRE_RELEASE_STATUSES = new Set([
  'lampo_ready', 'lampo_scheduled', 'proposed', 'in_production',
  'pre_production', 'pre_release', 'coming_soon',
]);

/**
 * Determina se un film/serie è "non ancora rilasciato"
 * basandosi sia sul pipeline_state sia sul status sia su scheduled_release_at.
 */
export function isProjectNotYetReleased(film) {
  if (!film) return false;
  const ps = String(film.pipeline_state || '').toLowerCase();
  if (PRE_RELEASE_PIPELINE_STATES.has(ps)) return true;
  const st = String(film.status || '').toLowerCase();
  if (PRE_RELEASE_STATUSES.has(st)) return true;
  // LAMPO scheduled / future scheduled_release_at
  if (st === 'lampo_ready' || st === 'lampo_scheduled') return true;
  const sch = film.scheduled_release_at;
  if (sch) {
    try {
      if (new Date(sch).getTime() > Date.now()) return true;
    } catch { /* noop */ }
  }
  // Se ha released_at futuro
  const ra = film.released_at;
  if (ra && (st === 'lampo_scheduled' || st === 'coming_soon')) {
    try {
      if (new Date(ra).getTime() > Date.now()) return true;
    } catch { /* noop */ }
  }
  return false;
}

/**
 * Ritorna la categoria narrativa ('concept'|'riprese'|'postprod'|'promo'|'imminente')
 * coerente con la fase pipeline reale del progetto.
 */
export function getProjectPhaseCategory(film) {
  if (!film) return 'concept';
  const ps = String(film.pipeline_state || '').toLowerCase();
  if (PIPELINE_TO_CATEGORY[ps]) return PIPELINE_TO_CATEGORY[ps];
  const st = String(film.status || '').toLowerCase();
  if (st === 'lampo_ready' || st === 'lampo_scheduled') return 'imminente';
  if (st === 'pre_production') return 'concept';
  if (st === 'in_production') return 'riprese';
  if (st === 'coming_soon' || st === 'pre_release') return 'imminente';
  if (st === 'proposed') return 'concept';
  return 'imminente';
}

// Etichette UI per ogni categoria
export const PHASE_LABELS = {
  concept: 'Le voci dalla pre-produzione',
  riprese: 'Indiscrezioni dal set',
  postprod: 'Anteprime e voci dalla post-produzione',
  promo: 'I giornali parlano della campagna',
  imminente: 'Le aspettative della stampa',
};
