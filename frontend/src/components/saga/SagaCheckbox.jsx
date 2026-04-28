// CineWorld Studio's — SagaCheckbox
// Checkbox per attivare la modalità "Film a Capitoli" all'ULTIMO step prima del rilascio.
// Mostrato in Pipeline V3 / LAMPO solo per Film e Animazione (no Serie/Anime).
// Permette di scegliere il numero potenziale di capitoli (2-15) e marcare cliffhanger.

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Sparkles, AlertCircle } from 'lucide-react';
import { Checkbox } from '../ui/checkbox';
import { Slider } from '../ui/slider';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';

const MIN_CH = 2;
const MAX_CH = 15;

export const SagaCheckbox = ({
  enabled = false,
  onToggle,
  totalChapters = 3,
  onTotalChange,
  cliffhanger = false,
  onCliffhangerChange,
  contentKind = 'film',
  disabled = false,
}) => {
  const [open, setOpen] = useState(enabled);

  const allowed = contentKind === 'film' || contentKind === 'animation';

  if (!allowed) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-700 bg-zinc-900/40 p-3 text-xs text-zinc-500" data-testid="saga-not-available">
        <AlertCircle className="inline w-4 h-4 mr-1 -mt-0.5" />
        Le saghe sono disponibili solo per Film e Animazione (no Serie/Anime).
      </div>
    );
  }

  const handleToggle = (val) => {
    setOpen(!!val);
    onToggle?.(!!val);
    if (val && (!totalChapters || totalChapters < MIN_CH)) onTotalChange?.(3);
  };

  return (
    <div className="rounded-xl border border-amber-700/40 bg-gradient-to-br from-amber-950/40 via-zinc-900/60 to-zinc-900/30 p-4 shadow-inner">
      <div className="flex items-start gap-3">
        <Checkbox
          id="saga-checkbox"
          checked={enabled}
          onCheckedChange={handleToggle}
          disabled={disabled}
          data-testid="saga-checkbox"
          className="mt-0.5"
        />
        <div className="flex-1">
          <Label htmlFor="saga-checkbox" className="cursor-pointer flex items-center gap-2 text-sm font-bold text-amber-300">
            <BookOpen className="w-4 h-4" />
            Film a Capitoli (Saga pianificata)
          </Label>
          <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
            Trasforma questo film nel <span className="text-amber-300 font-semibold">Capitolo 1</span> di una saga.
            I capitoli successivi avranno costo ridotto del <span className="text-emerald-400">30%</span>,
            beneficeranno del <span className="text-amber-300">bonus fan-base</span> e occuperanno{' '}
            <span className="text-cyan-300">un solo slot quota</span>.
          </p>
        </div>
      </div>

      <AnimatePresence>
        {enabled && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden mt-4"
          >
            <div className="grid gap-4 pl-7">
              <div>
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-xs text-zinc-300">Numero capitoli pianificati</span>
                  <span className="text-base font-bold text-amber-300" data-testid="saga-chapters-count">
                    {totalChapters} capitoli
                  </span>
                </div>
                <Slider
                  value={[totalChapters]}
                  min={MIN_CH}
                  max={MAX_CH}
                  step={1}
                  onValueChange={(v) => onTotalChange?.(v[0])}
                  className="w-full"
                  data-testid="saga-chapters-slider"
                />
                <div className="flex justify-between text-[10px] text-zinc-500 mt-1">
                  <span>{MIN_CH}</span>
                  <span>5</span>
                  <span>10</span>
                  <span>{MAX_CH}</span>
                </div>
              </div>

              <div className="flex items-center justify-between rounded-lg bg-zinc-900/60 p-2.5 border border-zinc-800">
                <div>
                  <Label htmlFor="saga-cliffhanger" className="cursor-pointer text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    Finale Cliffhanger (+5% hype al prossimo capitolo)
                  </Label>
                  <p className="text-[10px] text-zinc-500 mt-0.5">
                    Lascia il pubblico col fiato sospeso.
                  </p>
                </div>
                <Switch
                  id="saga-cliffhanger"
                  checked={cliffhanger}
                  onCheckedChange={onCliffhangerChange}
                  data-testid="saga-cliffhanger-toggle"
                />
              </div>

              <div className="rounded-lg bg-amber-950/30 border border-amber-700/30 p-2.5 text-[11px] text-amber-200/90">
                <span className="font-semibold">📚 Dopo il rilascio</span> di questo capitolo, troverai la saga
                nella sezione <span className="text-amber-300 font-bold">«Saghe» → Capitoli</span> per creare
                i successivi (max 3 attivi contemporaneamente).
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SagaCheckbox;
