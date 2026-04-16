import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Plus, Trash2, Edit3, Gamepad2, BookOpen, Wand2, Globe, Mic } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Skeleton } from '../components/ui/skeleton';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CONTENT_TYPE_ICONS = {
  roblox: Gamepad2,
  curiosity: BookOpen,
  story: BookOpen,
  animated: Wand2,
};

const CONTENT_TYPE_COLORS = {
  roblox: 'bg-red-500/20 text-red-300',
  curiosity: 'bg-sky-500/20 text-sky-300',
  story: 'bg-purple-500/20 text-purple-300',
  animated: 'bg-emerald-500/20 text-emerald-300',
};

const CONTENT_TYPE_LABELS = {
  roblox: 'Roblox',
  curiosity: 'Curiosidades',
  story: 'Historia',
  animated: 'Animado',
};

const DEFAULT_FORM = {
  name: '',
  content_type: 'roblox',
  hook_style: 'surprise',
  language: 'bilingual',
  tts_voice: 'standard',
  tags: '',
  custom_prompt: '',
  description: ''
};

export default function Templates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(DEFAULT_FORM);

  const fetchTemplates = async () => {
    try {
      const res = await axios.get(`${API}/templates`);
      setTemplates(res.data.templates || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTemplates(); }, []);

  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error('El nombre es obligatorio');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : []
      };
      if (editingId) {
        await axios.put(`${API}/templates/${editingId}`, payload);
        toast.success('Template actualizado');
      } else {
        await axios.post(`${API}/templates`, payload);
        toast.success('Template creado');
      }
      setDialogOpen(false);
      setEditingId(null);
      setForm(DEFAULT_FORM);
      fetchTemplates();
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (template) => {
    setForm({
      name: template.name || '',
      content_type: template.content_type || 'roblox',
      hook_style: template.hook_style || 'surprise',
      language: template.language || 'bilingual',
      tts_voice: template.tts_voice || 'standard',
      tags: (template.tags || []).join(', '),
      custom_prompt: template.custom_prompt || '',
      description: template.description || ''
    });
    setEditingId(template.id);
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/templates/${id}`);
      toast.success('Template eliminado');
      fetchTemplates();
    } catch (e) {
      toast.error('Error al eliminar');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{background: 'radial-gradient(600px circle at 20% -5%, rgba(46,168,255,0.12), transparent 50%)'}} />
        <div className="relative px-6 py-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold" style={{fontFamily: 'Space Grotesk'}}>Plantillas</h1>
            <p className="text-muted-foreground mt-1 text-sm">Estilos reutilizables para la generación de contenido</p>
          </div>
          <Button
            className="bg-primary hover:bg-red-600"
            onClick={() => { setForm(DEFAULT_FORM); setEditingId(null); setDialogOpen(true); }}
            data-testid="templates-create-template-button"
          >
            <Plus size={16} className="mr-2" /> Nueva Plantilla
          </Button>
        </div>
      </div>

      <div className="px-6 pb-8">
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {[1,2,3].map(i => <Skeleton key={i} className="h-48 w-full" />)}
          </div>
        ) : templates.length === 0 ? (
          <Card className="bg-card border-border">
            <CardContent className="text-center py-16">
              <Wand2 size={48} className="mx-auto mb-3 opacity-20 text-muted-foreground" />
              <p className="text-sm text-muted-foreground font-medium">No hay plantillas aún</p>
              <p className="text-xs text-muted-foreground mt-1">Crea plantillas para personalizar la IA</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {templates.map(template => {
              const Icon = CONTENT_TYPE_ICONS[template.content_type] || Wand2;
              const colorCls = CONTENT_TYPE_COLORS[template.content_type] || 'bg-white/10 text-muted-foreground';
              return (
                <Card key={template.id} className="bg-card border-border hover:border-white/20" data-testid="template-card">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between mb-3">
                      <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${colorCls}`}>
                        <Icon size={20} />
                      </div>
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost" className="h-7 w-7 p-0 hover:bg-white/5" onClick={() => handleEdit(template)} data-testid="template-edit-button">
                          <Edit3 size={13} />
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-red-400 hover:bg-red-500/10" onClick={() => handleDelete(template.id)} data-testid="template-delete-button">
                          <Trash2 size={13} />
                        </Button>
                      </div>
                    </div>
                    <h3 className="text-sm font-semibold">{template.name}</h3>
                    <p className="text-xs text-muted-foreground mt-1">{template.description || 'Sin descripción'}</p>
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorCls}`}>
                        {CONTENT_TYPE_LABELS[template.content_type] || template.content_type}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs bg-white/5 text-muted-foreground">
                        {template.language === 'bilingual' ? 'ES+EN' : template.language?.toUpperCase()}
                      </span>
                    </div>
                    {template.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {template.tags.slice(0, 4).map(tag => (
                          <span key={tag} className="text-xs text-muted-foreground">#{tag}</span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="bg-card border-border text-foreground max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{fontFamily: 'Space Grotesk'}}>
              {editingId ? 'Editar Plantilla' : 'Nueva Plantilla'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <Label className="text-xs text-muted-foreground">Nombre *</Label>
              <Input placeholder="Ej: Roblox Viral ES" value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="bg-secondary border-border mt-1" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs text-muted-foreground">Tipo de contenido</Label>
                <Select value={form.content_type} onValueChange={v => setForm({...form, content_type: v})}>
                  <SelectTrigger className="bg-secondary border-border mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    <SelectItem value="roblox">Roblox</SelectItem>
                    <SelectItem value="curiosity">Curiosidades</SelectItem>
                    <SelectItem value="story">Historia</SelectItem>
                    <SelectItem value="animated">Animado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Idioma</Label>
                <Select value={form.language} onValueChange={v => setForm({...form, language: v})}>
                  <SelectTrigger className="bg-secondary border-border mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    <SelectItem value="bilingual">Bilingüe (ES+EN)</SelectItem>
                    <SelectItem value="es">Español</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Estilo de hook</Label>
              <Select value={form.hook_style} onValueChange={v => setForm({...form, hook_style: v})}>
                <SelectTrigger className="bg-secondary border-border mt-1"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-card border-border">
                  <SelectItem value="surprise">😮 Sorpresa / Impacto</SelectItem>
                  <SelectItem value="question">❓ Pregunta intrigante</SelectItem>
                  <SelectItem value="bold">🔥 Afirmación audaz</SelectItem>
                  <SelectItem value="story">📚 Inicio de historia</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Tags (separados por coma)</Label>
              <Input placeholder="roblox, niños, viral, gaming" value={form.tags} onChange={e => setForm({...form, tags: e.target.value})} className="bg-secondary border-border mt-1" />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Descripción</Label>
              <Input placeholder="Descripción breve de la plantilla" value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="bg-secondary border-border mt-1" />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Prompt personalizado para la IA</Label>
              <Textarea
                placeholder="Instrucciones adicionales para el modelo de IA..."
                value={form.custom_prompt}
                onChange={e => setForm({...form, custom_prompt: e.target.value})}
                className="bg-secondary border-border mt-1 resize-none h-28"
              />
            </div>
            <Button className="w-full bg-primary hover:bg-red-600" onClick={handleSave} disabled={saving}>
              {saving ? 'Guardando...' : editingId ? 'Guardar cambios' : 'Crear plantilla'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
