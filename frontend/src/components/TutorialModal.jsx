import React, { useState } from "react";
import { tutorialSteps } from "../data/tutorialSteps";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

export default function TutorialModal({ onClose }) {
  const [step, setStep] = useState(0);
  const current = tutorialSteps[step];

  const next = () => {
    if (step < tutorialSteps.length - 1) setStep(step + 1);
    else onClose();
  };

  const prev = () => {
    if (step > 0) setStep(step - 1);
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[200]" onClick={onClose} data-testid="tutorial-modal-overlay">
      <div className="bg-[#111] text-white p-5 rounded-2xl w-[90%] max-w-md border border-white/10 shadow-2xl" onClick={e => e.stopPropagation()} data-testid="tutorial-modal">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] text-gray-500 font-mono">{step + 1}/{tutorialSteps.length}</span>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors" data-testid="tutorial-close-btn">
            <X className="w-4 h-4" />
          </button>
        </div>

        <h2 className="text-lg font-bold mb-2" data-testid="tutorial-step-title">{current.title}</h2>
        <p className="text-sm text-gray-300 leading-relaxed mb-5">{current.text}</p>

        <div className="flex items-center justify-between">
          <button
            onClick={prev}
            disabled={step === 0}
            className={`flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg transition-colors ${step === 0 ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:bg-white/10'}`}
            data-testid="tutorial-prev-btn"
          >
            <ChevronLeft className="w-4 h-4" /> Indietro
          </button>

          <button
            onClick={next}
            className="flex items-center gap-1 text-sm px-4 py-1.5 rounded-lg bg-yellow-500 text-black font-semibold hover:bg-yellow-400 transition-colors"
            data-testid="tutorial-next-btn"
          >
            {step === tutorialSteps.length - 1 ? "Fine" : "Avanti"} {step < tutorialSteps.length - 1 && <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}
