import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TalentMarketModal from '../components/TalentMarketModal';

/**
 * Pagina dedicata Mercato Talenti — wrapper standalone.
 * L'esperienza vive nel TalentMarketModal; chiudendolo si torna alla pagina precedente.
 */
export default function TalentMarketPage() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(true);

  const close = () => {
    setOpen(false);
    setTimeout(() => navigate(-1), 50);
  };

  return (
    <div className="min-h-screen pt-14 pb-20 px-2" data-testid="talent-market-page">
      <TalentMarketModal open={open} onClose={close} />
    </div>
  );
}
