/**
 * Utility per matching età personaggio↔attore.
 * Deve rimanere in sync con backend/utils/characters_ai.py.
 */

export function ageTolerance(charAge) {
  const a = Number.isFinite(charAge) ? charAge : 30;
  if (a <= 12) return 3;
  if (a <= 17) return 3;
  if (a <= 35) return 8;
  if (a <= 60) return 10;
  return 12;
}

export function isActorCompatible(charAge, actorAge) {
  if (actorAge == null || !Number.isFinite(actorAge)) return true; // attori senza età → OK
  return Math.abs(Number(actorAge) - Number(charAge)) <= ageTolerance(charAge);
}

const ROLE_LABEL = {
  protagonist: 'Protagonista',
  antagonist: 'Antagonista',
  coprotagonist: 'Co-protagonista',
  supporting: 'Supporto',
  minor: 'Minore',
};

const ROLE_COLOR = {
  protagonist:   { bar: 'bg-yellow-400',  chip: 'bg-yellow-500/20 text-yellow-300' },
  antagonist:    { bar: 'bg-red-500',     chip: 'bg-red-500/20 text-red-300' },
  coprotagonist: { bar: 'bg-cyan-400',    chip: 'bg-cyan-500/20 text-cyan-300' },
  supporting:    { bar: 'bg-purple-400',  chip: 'bg-purple-500/20 text-purple-300' },
  minor:         { bar: 'bg-gray-500',    chip: 'bg-gray-500/20 text-gray-300' },
};

export function roleLabel(rt) {
  return ROLE_LABEL[rt] || 'Personaggio';
}

export function roleColor(rt) {
  return ROLE_COLOR[rt] || ROLE_COLOR.supporting;
}
