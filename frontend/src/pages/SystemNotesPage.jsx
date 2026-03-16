import React, { useContext, useState, useEffect } from 'react';
import { Megaphone, Plus, Trash2, Bug, Sparkles, Wrench, Calendar, AlertTriangle, Loader2 } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '../components/ui/select';
import { AuthContext, useTranslations } from '../contexts';
import { toast } from 'sonner';

const CATEGORY_CONFIG = {
  update: { label: 'Aggiornamento', icon: Wrench, color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  feature: { label: 'Nuova Funzione', icon: Sparkles, color: 'bg-green-500/20 text-green-400 border-green-500/30' },
  bugfix: { label: 'Bug Fix', icon: Bug, color: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
  event: { label: 'Evento', icon: Calendar, color: 'bg-purple-500/20 text-purple-400 border-purple-500/30' },
  maintenance: { label: 'Manutenzione', icon: AlertTriangle, color: 'bg-red-500/20 text-red-400 border-red-500/30' }
};

const SystemNotesPage = () => {
  const { user, api } = useContext(AuthContext);
  const { language } = useTranslations();
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newNote, setNewNote] = useState({ title: '', content: '', category: 'update', priority: 'normal' });
  const [creating, setCreating] = useState(false);
  const isAdmin = user?.nickname === 'NeoMorpheus';

  useEffect(() => {
    const load = async () => {
      try {
        const [notesRes] = await Promise.all([
          api.get('/system-notes'),
          api.post('/system-notes/mark-read').catch(() => {})
        ]);
        setNotes(notesRes.data);
      } catch {} finally { setLoading(false); }
    };
    load();
  }, [api]);

  const handleCreate = async () => {
    if (!newNote.title || !newNote.content) return toast.error('Compila tutti i campi');
    setCreating(true);
    try {
      const res = await api.post('/admin/system-notes', newNote);
      setNotes(prev => [res.data, ...prev]);
      setShowCreate(false);
      setNewNote({ title: '', content: '', category: 'update', priority: 'normal' });
      toast.success('Nota creata!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally { setCreating(false); }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/admin/system-notes/${id}`);
      setNotes(prev => prev.filter(n => n.id !== id));
      toast.success('Nota eliminata');
    } catch { toast.error('Errore'); }
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  if (loading) return <div className="pt-20 text-center"><Loader2 className="w-6 h-6 animate-spin mx-auto text-yellow-500" /></div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-3xl mx-auto" data-testid="system-notes-page">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
          <Megaphone className="w-7 h-7 text-yellow-500" />
          {language === 'it' ? 'Note di Sistema' : 'System Notes'}
        </h1>
        {isAdmin && (
          <Button size="sm" onClick={() => setShowCreate(true)} className="bg-yellow-500 hover:bg-yellow-600 text-black" data-testid="create-note-btn">
            <Plus className="w-4 h-4 mr-1" /> Nuova Nota
          </Button>
        )}
      </div>

      {notes.length === 0 ? (
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardContent className="p-8 text-center text-gray-400">
            <Megaphone className="w-10 h-10 mx-auto mb-2 opacity-30" />
            <p>{language === 'it' ? 'Nessuna nota di sistema ancora.' : 'No system notes yet.'}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {notes.map(note => {
            const cat = CATEGORY_CONFIG[note.category] || CATEGORY_CONFIG.update;
            const Icon = cat.icon;
            return (
              <Card key={note.id} className={`bg-[#1A1A1A] border-white/10 ${note.priority === 'high' ? 'ring-1 ring-yellow-500/30' : ''}`} data-testid={`note-${note.id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border ${cat.color}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold text-sm">{note.title}</h3>
                          <Badge variant="outline" className={`text-[10px] h-4 border ${cat.color}`}>{cat.label}</Badge>
                          {note.priority === 'high' && <Badge className="bg-yellow-500/20 text-yellow-400 text-[10px] h-4">Importante</Badge>}
                        </div>
                        <p className="text-gray-400 text-xs mt-1 whitespace-pre-line">{note.content}</p>
                        <p className="text-gray-600 text-[10px] mt-2">{formatDate(note.created_at)} — {note.author}</p>
                      </div>
                    </div>
                    {isAdmin && (
                      <Button size="sm" variant="ghost" onClick={() => handleDelete(note.id)} className="text-red-400 hover:text-red-300 h-7 w-7 p-0 shrink-0">
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Note Dialog (Admin) */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="bg-[#1A1A1A] border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Bebas_Neue']">Nuova Nota di Sistema</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Input placeholder="Titolo" value={newNote.title} onChange={e => setNewNote(p => ({ ...p, title: e.target.value }))} className="bg-black/30 border-white/10" data-testid="note-title-input" />
            <Textarea placeholder="Contenuto della nota..." value={newNote.content} onChange={e => setNewNote(p => ({ ...p, content: e.target.value }))} className="bg-black/30 border-white/10 min-h-[100px]" data-testid="note-content-input" />
            <div className="grid grid-cols-2 gap-2">
              <Select value={newNote.category} onValueChange={v => setNewNote(p => ({ ...p, category: v }))}>
                <SelectTrigger className="bg-black/30 border-white/10 h-8 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  {Object.entries(CATEGORY_CONFIG).map(([k, v]) => (
                    <SelectItem key={k} value={k} className="text-xs">{v.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={newNote.priority} onValueChange={v => setNewNote(p => ({ ...p, priority: v }))}>
                <SelectTrigger className="bg-black/30 border-white/10 h-8 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-[#1A1A1A] border-white/10">
                  <SelectItem value="low" className="text-xs">Bassa</SelectItem>
                  <SelectItem value="normal" className="text-xs">Normale</SelectItem>
                  <SelectItem value="high" className="text-xs">Alta</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setShowCreate(false)} className="border-white/10">Annulla</Button>
            <Button size="sm" onClick={handleCreate} disabled={creating} className="bg-yellow-500 hover:bg-yellow-600 text-black" data-testid="confirm-create-note">
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Pubblica'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SystemNotesPage;
