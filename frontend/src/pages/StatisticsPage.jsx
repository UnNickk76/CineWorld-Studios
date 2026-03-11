import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, useTranslations } from '../contexts';
import { Card, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Film, DollarSign, Heart, Star, Users } from 'lucide-react';

const StatisticsPage = () => {
  const { api } = useContext(AuthContext);
  const { t } = useTranslations();
  const [globalStats, setGlobalStats] = useState(null);
  const [myStats, setMyStats] = useState(null);

  useEffect(() => { Promise.all([api.get('/statistics/global'), api.get('/statistics/my')]).then(([g, m]) => { setGlobalStats(g.data); setMyStats(m.data); }); }, [api]);

  return (
    <div className="pt-16 pb-20 px-3 max-w-7xl mx-auto" data-testid="statistics-page">
      <h1 className="font-['Bebas_Neue'] text-3xl mb-4">{t('statistics')}</h1>
      <Tabs defaultValue="my">
        <TabsList className="mb-3"><TabsTrigger value="my">My Stats</TabsTrigger><TabsTrigger value="global">Global</TabsTrigger></TabsList>
        <TabsContent value="my"><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {[{l:'Films',v:myStats?.total_films||0,i:Film},{l:'Revenue',v:`$${(myStats?.total_revenue||0).toLocaleString()}`,i:DollarSign},{l:'Likes',v:myStats?.total_likes||0,i:Heart},{l:'Quality',v:`${(myStats?.average_quality||0).toFixed(0)}%`,i:Star}].map(s=>(
            <Card key={s.l} className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><s.i className="w-5 h-5 mb-1 text-yellow-500" /><p className="text-xl font-bold">{s.v}</p><p className="text-xs text-gray-400">{s.l}</p></CardContent></Card>
          ))}
        </div></TabsContent>
        <TabsContent value="global"><div className="grid sm:grid-cols-3 gap-3">
          <Card className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><Film className="w-5 h-5 mb-1 text-yellow-500" /><p className="text-xl font-bold">{globalStats?.total_films||0}</p><p className="text-xs text-gray-400">Total Films</p></CardContent></Card>
          <Card className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><Users className="w-5 h-5 mb-1 text-blue-500" /><p className="text-xl font-bold">{globalStats?.total_users||0}</p><p className="text-xs text-gray-400">Producers</p></CardContent></Card>
          <Card className="bg-[#1A1A1A] border-white/5"><CardContent className="p-3"><DollarSign className="w-5 h-5 mb-1 text-green-500" /><p className="text-xl font-bold">${(globalStats?.total_box_office||0).toLocaleString()}</p><p className="text-xs text-gray-400">Box Office</p></CardContent></Card>
        </div></TabsContent>
      </Tabs>
    </div>
  );
};

export default StatisticsPage;
