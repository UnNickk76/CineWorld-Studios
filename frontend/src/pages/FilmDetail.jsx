// CineWorld Studio's - FilmDetail
// Uses ContentTemplate for fullscreen cinematic view

import React from 'react';
import { useParams } from 'react-router-dom';
import { ContentTemplate } from '../components/ContentTemplate';

const FilmDetail = () => {
  const { id } = useParams();
  
  return (
    <div className="pt-16 pb-20 px-3 flex items-center justify-center min-h-screen" data-testid="film-detail-page">
      <ContentTemplate filmId={id} contentType="film" />
    </div>
  );
};

export default FilmDetail;
