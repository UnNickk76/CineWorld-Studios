// Pre-release / hype phrases generator
// Le frasi vengono selezionate deterministicamente in base a (film_id + ora corrente)
// così tutti i giocatori vedono le stesse frasi per la stessa ora — coerente con il sistema hype.
//
// AGGIORNATO (Apr 28, 2026): le press quotes ora sono SUDDIVISE PER FASE PIPELINE
// (concept/riprese/postprod/promo/imminente) per coerenza realistica.
// Vedi `pressByPhase.js` per i nuovi pool.

import {
  PRESS_BY_PHASE,
  OUTLETS_BY_PHASE,
  getProjectPhaseCategory,
  isProjectNotYetReleased,
  PHASE_LABELS,
} from './pressByPhase';

// ─── Hype levels (basati su quality + budget + cast + virtual_likes) ───
// 'high'   → grande attesa, spettatori entusiasti
// 'mid'    → curiosità moderata
// 'low'    → scetticismo, attesa modesta

// ── PRESS QUOTES per progetti NON ANCORA usciti (analogo "Cosa ne pensano i giornali") ──
const PRESS_PRE_RELEASE = {
  high: [
    'Il film più atteso del mese',
    'Promette di essere il blockbuster dell\'anno',
    'Il cast fa già parlare di sé',
    'Le prime immagini lasciano senza fiato',
    'Aspettative altissime dopo le anticipazioni',
    'Si preannuncia un evento cinematografico',
    'I primi screening sono entusiastici',
    'Già si parla di candidature ai premi',
    'Il progetto cinematografico più chiacchierato del momento',
    'Da non perdere assolutamente',
    'Tutti i riflettori puntati su questo titolo',
    'L\'hype cresce di ora in ora',
    'I fan contano i giorni',
    'Il preview ha letteralmente folgorato',
    'L\'attesa è febbrile',
    'Si delinea come l\'evento dell\'anno',
    'La produzione promette grandi cose',
    'Aspettative critiche oltre il limite',
    'Le immagini trapelate sono spettacolari',
    'Il pubblico è in fermento',
    'Successo annunciato',
    'Tutti ne parlano già',
    'Si profila un trionfo',
    'Tra i film più discussi della stagione',
    'Materiale promozionale di qualità rara',
  ],
  mid: [
    'Promettente ma con qualche dubbio',
    'Aspettative miste',
    'Da seguire con attenzione',
    'Potrebbe sorprendere o deludere',
    'Il pubblico aspetta di vedere',
    'Curioso ma non convincente al 100%',
    'Resta da verificare l\'esito finale',
    'Il cast c\'è, ma il resto?',
    'Da dimostrare nel concreto',
    'La curiosità è alta ma cautela d\'obbligo',
    'Concept solido, esecuzione tutta da verificare',
    'Aspettative oneste, niente di più',
    'Il trailer divide la critica',
    'Materiale promozionale altalenante',
    'Si vedrà in sala',
    'Mancano elementi convincenti',
    'Curiosità sì, certezza no',
    'Tema interessante, regia da scoprire',
    'Premesse buone, dubbi sull\'esito',
    'Punti di forza e di debolezza già visibili',
    'Resta nel limbo delle aspettative',
    'Solido sulla carta, da provare in sala',
  ],
  low: [
    'Aspettative molto basse',
    'Il pubblico è scettico',
    'Pochi sembrano interessati',
    'Probabilmente non farà gli incassi sperati',
    'I trailer non hanno entusiasmato',
    'Materiale promozionale poco efficace',
    'Concept debole sulla carta',
    'Il cast non basta a salvare le anticipazioni',
    'Buco programmatico più che evento',
    'Difficile crederci con queste premesse',
    'Promesse vuote',
    'Si profila un flop annunciato',
    'I dati sull\'attesa sono preoccupanti',
    'Mancano gli ingredienti del successo',
    'Materiale insufficiente',
    'Trailer dimenticabili',
    'Il pubblico ha già archiviato',
    'Manca chiaramente lo "wow factor"',
    'Aspettative al di sotto della media',
    'Difficile trovare entusiasmo',
    'Le case di produzione paiono scettiche',
    'Niente di entusiasmante nelle anticipazioni',
    'Probabilmente sarà un flop di sala',
    'Mancano spunti concreti',
    'Pubblico tiepido',
  ],
};

const OUTLETS = ['Variety', 'Empire', 'Hollywood R.', 'IndieWire', 'CineNews', 'Cahiers', 'Total Film', 'Vulture', 'Screen Daily'];

// ── PUBBLICO & EVENTI per progetti NON ANCORA usciti ──
const AUDIENCE_PRE_RELEASE = {
  high: [
    'L\'attesa cresce di giorno in giorno',
    'Code virtuali per i biglietti in prevendita',
    'I social sono inondati di hype',
    'Influencer entusiasti dei preview',
    'Il fandom è in fibrillazione',
    'Trending su tutti i social per giorni',
    'Migliaia di prenotazioni anticipate',
    'I fan hanno organizzato watch party',
    'Il merchandise pre-release è esaurito',
    'Aumenta l\'attesa: il pubblico vuole vedere',
    'Discussioni accese sui forum di cinema',
    'Aspettative alle stelle',
    'Le proiezioni stampa hanno acceso il pubblico',
    'TikTok e Instagram in fermento',
    'Pre-vendita oltre ogni previsione',
    'Comunità di fan organizzano marathon',
    'Il poster è virale',
    'Hype incontenibile',
    'Marketing virale da manuale',
    'Momento culturale in arrivo',
  ],
  mid: [
    'Curiosità moderata tra il pubblico',
    'Alcuni interessati, altri scettici',
    'Aspettative bilanciate',
    'L\'attesa è equilibrata',
    'Il pubblico aspetta di vedere',
    'Discussione contenuta sui social',
    'Niente fenomeno virale, ma interesse c\'è',
    'Il pubblico riserva il giudizio',
    'Reazioni miste alle anticipazioni',
    'Curiosità sì, fervore no',
    'Pochi commenti virali ma costanti',
    'Pre-vendita nella media',
    'Interesse selettivo',
    'I cinefili attendono, i casual no',
    'Marketing efficace ma non virale',
    'Il pubblico non si sbilancia',
    'Reazioni tiepide ma positive',
    'Aspettativa moderata',
    'Discussione ridotta ma costruttiva',
    'Né hype né flop annunciato',
  ],
  low: [
    'Pubblico scettico',
    'Pochi interessati al pre-release',
    'L\'attesa è quasi nulla',
    'I social ignorano il film',
    'Pre-vendita al lumicino',
    'Trailer dimenticati in poche ore',
    'Discussione marginale',
    'Probabilmente non farà gli incassi sperati',
    'Marketing fallimentare',
    'Il pubblico è glaciale',
    'Nessun hype rilevabile',
    'Le sale faranno fatica a riempirsi',
    'Aspettative azzerate',
    'Il film passa quasi inosservato',
    'Influencer disinteressati',
    'Pre-release sotto le aspettative',
    'Buco mediatico',
    'Il pubblico ha altri interessi',
    'Materiale promozionale inefficace',
    'Si annuncia tristemente sottotono',
  ],
};

// ── THEATER DURATION explanations (perché il film resta X giorni in sala) ──
const THEATER_DURATION_REASONS = {
  short: [
    'Pochi giorni al cinema: il film non ha generato grandi aspettative',
    'Distribuzione limitata viste le premesse modeste',
    'I cinema non hanno scommesso troppo su questo titolo',
    'Permanenza ridotta per via del marketing contenuto',
    'Programmazione breve: i trailer non hanno convinto',
    'Le sale hanno preferito investire su titoli più sicuri',
    'Permanenza minima per testare la reazione del pubblico',
    'Il film passerà brevemente in sala',
    'Pochi giorni per evitare buchi di programmazione',
    'Distribuzione veloce per arrivare presto in TV',
  ],
  medium: [
    'Permanenza nella media: aspettative oneste',
    'Distribuzione equilibrata',
    'Le sale danno fiducia con tempi standard',
    'Programmazione di durata media',
    'Il film resta in sala per i tempi canonici',
    'Permanenza sufficiente per testare il pubblico',
    'Il marketing giustifica una durata moderata',
    'Programmazione equilibrata in base al cast',
    'Tempi medi di permanenza per progetti di questo livello',
    'Distribuzione adeguata alla qualità prevista',
  ],
  long: [
    'Molti giorni al cinema: dai brevi trailer visti il pubblico non vede l\'ora che il film esca',
    'Programmazione estesa per il forte hype generato',
    'Le sale credono fortemente nel titolo',
    'Permanenza prolungata viste le aspettative altissime',
    'Distribuzione lunga: i numeri lo meritano',
    'I cinema hanno blindato slot prolungati',
    'Programmazione VIP per il successo annunciato',
    'Permanenza estesa per cavalcare l\'hype',
    'Le sale vogliono massimizzare gli incassi',
    'Distribuzione ampia per un evento atteso',
  ],
  blockbuster: [
    'Programmazione record: il film promette di essere un evento storico',
    'Distribuzione ai massimi livelli per un titolo evento',
    'Permanenza da blockbuster: tutte le sale ai massimi turni',
    'Il film resterà in sala il più a lungo possibile',
    'Programmazione massima riservata a pochi titoli',
    'Le sale puntano tutto su questo film',
    'Distribuzione monstre per uno dei film più attesi',
    'Programmazione speciale, il pubblico è impaziente',
    'Massima esposizione possibile: hype incontenibile',
    'Il calendario è blindato per settimane',
  ],
};

// ── HASH semplice per selezione deterministica per (filmId + ora) ──
function djb2(str) {
  let h = 5381;
  for (let i = 0; i < str.length; i++) h = ((h << 5) + h) + str.charCodeAt(i);
  return Math.abs(h);
}

function pickN(arr, n, seed) {
  // Selezione deterministica di n elementi distinti dall'array, basata su seed
  const out = [];
  const used = new Set();
  let s = seed;
  while (out.length < n && used.size < arr.length) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const idx = s % arr.length;
    if (!used.has(idx)) {
      used.add(idx);
      out.push(arr[idx]);
    }
  }
  return out;
}

/**
 * Calcola il "livello hype" di un progetto pre-release in base ai segnali disponibili.
 * Ritorna 'high' | 'mid' | 'low'.
 */
export function computeHypeLevel(film) {
  if (!film) return 'mid';
  // Pesi: quality_score (0-100) 40%, virtual_likes 25%, budget_tier 20%, cast quality 15%
  const q = Math.min(100, Math.max(0, film.quality_score || (film.cwsv ? film.cwsv * 10 : 50)));
  const likes = film.virtual_likes || 0;
  const budgetMap = { high: 100, mid: 60, low: 30 };
  const budget = budgetMap[film.budget_tier] ?? 60;
  const castStars = (film.cast?.actors || []).reduce((s, a) => s + (a.stars || a.popularity || 0), 0);
  const castScore = Math.min(100, castStars * 10);
  // Hype bonus se schedulato (anticipazione mediatica)
  const hypeBonus = film.lampo_hype_bonus ? (film.lampo_hype_bonus - 1) * 100 : 0;
  const score = q * 0.40 + Math.min(100, likes / 5) * 0.25 + budget * 0.20 + castScore * 0.15 + hypeBonus * 5;
  if (score >= 70) return 'high';
  if (score >= 45) return 'mid';
  return 'low';
}

/**
 * Restituisce 3 frasi di "press pre-release" per un film non ancora uscito.
 * Si aggiornano ogni ora basandosi su (film_id + currentHour).
 *
 * AGGIORNATO: il pool di frasi è ora COERENTE con la fase pipeline reale del progetto.
 * - idea/hype/cast → "concept" (rumor, casting buzz)
 * - prep/ciak (riprese) → "riprese" (leak dal set)
 * - finalcut → "postprod" (montaggio, test screening)
 * - marketing → "promo" (trailer, materiali)
 * - la_prima/distribution/release_pending → "imminente" (prevendite, hype finale)
 */
export function getPreReleasePressReviews(film) {
  const level = computeHypeLevel(film);
  const phase = getProjectPhaseCategory(film);
  // Prefer phase-specific pool; fallback to legacy mid pool
  const phasePool = PRESS_BY_PHASE[phase]?.[level] || PRESS_BY_PHASE.imminente[level];
  const pool = phasePool || PRESS_PRE_RELEASE[level] || PRESS_PRE_RELEASE.mid;
  const outletsPool = OUTLETS_BY_PHASE[phase] || OUTLETS;
  const hour = Math.floor(Date.now() / 3600000);
  const seed = djb2((film?.id || 'x') + ':' + phase + ':' + hour);
  const phrases = pickN(pool, 3, seed);
  const outlets = pickN(outletsPool, 3, seed + 999);
  return phrases.map((quote, i) => ({ outlet: outlets[i], quote }));
}

/**
 * Ritorna l'etichetta UI ("Le aspettative della stampa", "Indiscrezioni dal set", ecc.)
 * coerente con la fase pipeline del progetto.
 */
export function getPreReleasePressLabel(film) {
  const phase = getProjectPhaseCategory(film);
  return PHASE_LABELS[phase] || 'Le aspettative della stampa';
}

/**
 * Restituisce 2-3 frasi di "pubblico & eventi" per un film non ancora uscito.
 */
export function getPreReleaseAudience(film) {
  const level = computeHypeLevel(film);
  const pool = AUDIENCE_PRE_RELEASE[level] || AUDIENCE_PRE_RELEASE.mid;
  const hour = Math.floor(Date.now() / 3600000);
  const seed = djb2('aud:' + (film?.id || 'x') + ':' + hour);
  return pickN(pool, 3, seed);
}

/**
 * Restituisce una frase che spiega la durata in sala di un film LAMPO.
 * `theaterDays`: 5-45.
 */
export function getTheaterDurationReason(theaterDays, film) {
  let bucket = 'medium';
  if (theaterDays <= 10) bucket = 'short';
  else if (theaterDays <= 22) bucket = 'medium';
  else if (theaterDays <= 35) bucket = 'long';
  else bucket = 'blockbuster';
  const pool = THEATER_DURATION_REASONS[bucket];
  const hour = Math.floor(Date.now() / 3600000);
  const seed = djb2('dur:' + (film?.id || 'x') + ':' + hour);
  return pickN(pool, 1, seed)[0];
}

export default {
  computeHypeLevel,
  getPreReleasePressReviews,
  getPreReleasePressLabel,
  getPreReleaseAudience,
  getTheaterDurationReason,
};

// Re-export per uso esterno
export { isProjectNotYetReleased };
