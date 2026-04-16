import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Plus, Trash2, Play, RotateCcw, Globe, Gamepad2, BookOpen, Wand2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { Skeleton } from '../components/ui/skeleton';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const StatusBadge = ({ status }) => {
  const map = {
    completed: { label: 'Completado', cls: 'badge-success' },
    running: { label: 'Ejecutando', cls: 'badge-running animate-pulse-ring' },
    failed: { label: 'Fallido', cls: 'badge-failed' },
    pending: { label: 'Pendiente', cls: 'badge-pending' },
    cancelled: { label: 'Cancelado', cls: 'badge-idle' },
  };
  const s = map[status] || { label: status, cls: 'badge-idle' };
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>{s.label}</span>;
};

const CONTENT_TYPES = [
  { value: 'roblox', label: 'Roblox', icon: Gamepad2 },
  { value: 'curiosity', label: 'Curiosidades', icon: BookOpen },
  { value: 'story', label: 'Historia', icon: BookOpen },
  { value: 'animated', label: 'Animado', icon: Wand2 },
];

const LANGUAGES = [
  { value: 'bilingual', label: 'Bilingüe (ES+EN)' },
  { value: 'es', label: 'Español' },
  { value: 'en', label: 'English' },
];

const FORMATS = [
  { value: 'short', label: 'YouTube Shorts (9:16)' },
  { value: 'long', label: 'Standard (16:9)' },
];

const PRIORITIES = [
  { value: '1', label: '1 — Máxima' },
  { value: '5', label: '5 — Normal' },
  { value: '10', label: '10 — Baja' },
];

export default function Queue() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [creating, setCreating] = useState(false);
  const [runningJobId, setRunningJobId] = useState(null);

  const [form, setForm] = useState({
    title: '',
    topic: '',
    source_url: '',
    content_type: 'roblox',
    language: 'bilingual',
    format: 'short',
    made_for_kids: true,
    priority: 5,
    custom_prompt: ''
  });

  const fetchJobs = async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const res = await axios.get(`${API}/jobs`, { params });
      setJobs(res.data.jobs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchJobs(); }, [statusFilter]);

  const handleCreate = async () => {
    if (!form.title.trim() || !form.topic.trim()) {
      toast.error('El título y tema son obligatorios');
      return;
    }
    setCreating(true);
    try {
      await axios.post(`${API}/jobs`, form);
      toast.success('Job creado exitosamente');
      setCreateOpen(false);
      setForm({ title: '', topic: '', source_url: '', content_type: 'roblox', language: 'bilingual', format: 'short', made_for_kids: true, priority: 5, custom_prompt: '' });
      fetchJobs();
    } catch (e) {
      toast.error('Error al crear el job: ' + (e.response?.data?.detail || e.message));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (jobId) => {
    try {
      await axios.delete(`${API}/jobs/${jobId}`);
      toast.success('Job eliminado');
      fetchJobs();
    } catch (e) {
      toast.error('Error al eliminar');
    }
  };

  const handleRun = async (jobId) => {
    setRunningJobId(jobId);
    try {
      const res = await axios.post(`${API}/jobs/${jobId}/run`);
      toast.success(`Pipeline iniciado! Run ID: ${res.data.run_id?.slice(0, 8)}`);
      fetchJobs();
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail || e.message));
    } finally {
      setRunningJobId(null);
    }
  };

  const handleRetry = async (jobId) => {
    setRunningJobId(jobId);
    try {
      await axios.post(`${API}/jobs/${jobId}/retry`);
      toast.success('Reintentando...');
      fetchJobs();
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail || e.message));
    } finally {
      setRunningJobId(null);
    }
  };

  const contentTypeLabel = (type) => CONTENT_TYPES.find(c => c.value === type)?.label || type;
  const languageLabel = (lang) => LANGUAGES.find(l => l.value === lang)?.label || lang;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{background: 'radial-gradient(600px circle at 10% -5%, rgba(255,0,0,0.12), transparent 50%)'}} />
        <div className="relative px-6 py-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold" style={{fontFamily: 'Space Grotesk'}}>Cola de Videos</h1>
            <p className="text-muted-foreground mt-1 text-sm">{jobs.length} job{jobs.length !== 1 ? 's' : ''} en cola</p>
          </div>
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button className="bg-primary hover:bg-red-600" data-testid="queue-add-job-button">
                <Plus size={16} className="mr-2" /> Nuevo Video
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-border text-foreground max-w-lg max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle style={{fontFamily: 'Space Grotesk'}}>Crear Nuevo Job de Video</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-2">
                <div>
                  <Label className="text-xs text-muted-foreground">Título del job *</Label>
                  <Input
                    placeholder="Ej: Mejor momento Roblox semana 1"
                    value={form.title}
                    onChange={e => setForm({...form, title: e.target.value})}
                    className="bg-secondary border-border mt-1"
                    data-testid="job-create-title-input"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Tema/Topic del video *</Label>
                  <Input
                    placeholder="Ej: El modo oculto de Roblox que nadie conoce"
                    value={form.topic}
                    onChange={e => setForm({...form, topic: e.target.value})}
                    className="bg-secondary border-border mt-1"
                    data-testid="job-create-topic-input"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">URL del clip (opcional)</Label>
                  <Input
                    placeholder="https://youtube.com/watch?v=..."
                    value={form.source_url}
                    onChange={e => setForm({...form, source_url: e.target.value})}
                    className="bg-secondary border-border mt-1"
                    data-testid="job-create-url-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-muted-foreground">Tipo de contenido</Label>
                    <Select value={form.content_type} onValueChange={v => setForm({...form, content_type: v})}>
                      <SelectTrigger className="bg-secondary border-border mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        {CONTENT_TYPES.map(c => (
                          <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Idioma</Label>
                    <Select value={form.language} onValueChange={v => setForm({...form, language: v})}>
                      <SelectTrigger className="bg-secondary border-border mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        {LANGUAGES.map(l => (
                          <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-muted-foreground">Formato</Label>
                    <Select value={form.format} onValueChange={v => setForm({...form, format: v})}>
                      <SelectTrigger className="bg-secondary border-border mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        {FORMATS.map(f => (
                          <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Prioridad</Label>
                    <Select value={String(form.priority)} onValueChange={v => setForm({...form, priority: parseInt(v)})}>
                      <SelectTrigger className="bg-secondary border-border mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-card border-border">
                        {PRIORITIES.map(p => (
                          <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-fuchsia-500/10 border border-fuchsia-500/25">
                  <Switch
                    checked={form.made_for_kids}
                    onCheckedChange={v => setForm({...form, made_for_kids: v})}
                    data-testid="job-create-coppa-switch"
                  />
                  <div>
                    <p className="text-sm font-medium">Marcado para niños (COPPA)</p>
                    <p className="text-xs text-muted-foreground">Recomendado para contenido infantil</p>
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Prompt personalizado (opcional)</Label>
                  <Textarea
                    placeholder="Instrucciones adicionales para la IA..."
                    value={form.custom_prompt}
                    onChange={e => setForm({...form, custom_prompt: e.target.value})}
                    className="bg-secondary border-border mt-1 resize-none h-20"
                    data-testid="job-create-prompt-input"
                  />
                </div>
                <Button
                  className="w-full bg-primary hover:bg-red-600"
                  onClick={handleCreate}
                  disabled={creating}
                  data-testid="job-create-submit-button"
                >
                  {creating ? 'Creando...' : 'Crear Job'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="px-6 pb-8">
        {/* Filters */}
        <div className="flex gap-2 mb-4">
          {['', 'pending', 'running', 'completed', 'failed'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              data-testid={`queue-filter-${s || 'all'}`}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${
                statusFilter === s
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white/5 text-muted-foreground border-border hover:bg-white/10'
              }`}
            >
              {s === '' ? 'Todos' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>

        {/* Jobs Table */}
        <Card className="bg-card border-border">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-5 space-y-3">
                {[1,2,3].map(i => <Skeleton key={i} className="h-16 w-full" />)}
              </div>
            ) : jobs.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground">
                <Gamepad2 size={48} className="mx-auto mb-3 opacity-20" />
                <p className="text-sm font-medium">No hay jobs en la cola</p>
                <p className="text-xs mt-1">Crea tu primer video para empezar la automatización</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {jobs.map(job => (
                  <div
                    key={job.id}
                    className="flex items-center gap-4 px-5 py-4 hover:bg-white/2"
                    data-testid="queue-job-row"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-medium truncate">{job.title}</p>
                        <StatusBadge status={job.status} />
                        {job.made_for_kids && (
                          <span className="badge-coppa inline-flex items-center px-2 py-0.5 rounded text-xs font-medium">COPPA</span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 truncate">
                        {contentTypeLabel(job.content_type)} · {languageLabel(job.language)} · {job.format === 'short' ? 'Shorts' : 'Estándar'}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">{job.topic}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {job.status === 'failed' && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-amber-500/30 text-amber-300 hover:bg-amber-500/10 h-8"
                          onClick={() => handleRetry(job.id)}
                          disabled={runningJobId === job.id}
                          data-testid="queue-retry-button"
                        >
                          <RotateCcw size={14} className="mr-1" /> Reintentar
                        </Button>
                      )}
                      {(job.status === 'pending' || job.status === 'completed') && (
                        <Button
                          size="sm"
                          className="bg-primary hover:bg-red-600 h-8"
                          onClick={() => handleRun(job.id)}
                          disabled={runningJobId === job.id}
                          data-testid="queue-run-button"
                        >
                          <Play size={14} className="mr-1" />
                          {runningJobId === job.id ? 'Iniciando...' : 'Ejecutar'}
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-8 w-8 p-0"
                        onClick={() => handleDelete(job.id)}
                        data-testid="queue-delete-button"
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
