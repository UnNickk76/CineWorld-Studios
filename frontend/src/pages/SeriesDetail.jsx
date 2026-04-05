// CineWorld Studio's - SeriesDetail
// Uses ContentTemplate for fullscreen cinematic view

import React from 'react';
import { useParams } from 'react-router-dom';
import { ContentTemplate } from '../components/ContentTemplate';

export default function SeriesDetail() {
  const { id } = useParams();
  
  return (
    <div className="pt-14 pb-16 px-3 flex items-center justify-center min-h-screen" data-testid="series-detail-page">
      <ContentTemplate filmId={id} contentType="series" />
    </div>
  );
}
