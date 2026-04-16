import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useSearchParams } from 'react-router-dom';
import {
  Youtube, Key, Clock, Shield, AlertTriangle, CheckCircle, ExternalLink, Eye, EyeOff, Github
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Slider } from '../components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Separator } from '../components/ui/separator';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Skeleton } from '../components/ui/skeleton';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function PasswordInput({ value, onChange, placeholder, testId }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <Input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="bg-secondary border-border pr-10"
        data-testid={testId}
      />
      <button
        type="button"
        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        onClick={() => setShow(!show)}
      >
        {show ? <EyeOff size={14} /> : <Eye size={14} />}
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [ytStatus, setYtStatus] = useState(null);
  const [checkingYt, setCheckingYt] = useState(false);
  const [authUrl, setAuthUrl] = useState(null);
  const [searchParams] = useSearchParams();

  const fetchSettings = async () => {
    try {
      const res = await axios.get(`${API}/settings`);
      setSettings(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const checkYouTubeStatus = async () => {
    setCheckingYt(true);
    try {
      const res = await axios.get(`${API}/settings/youtube/status`);
      setYtStatus(res.data);
    } catch (e) {
      setYtStatus({ connected: false, error: e.message });
    } finally {
      setCheckingYt(false);
    }
  };

  useEffect(() => {
    fetchSettings();
    // Check for OAuth callback params
    if (searchParams.get('oauth_success')) {
      toast.success('YouTube conectado exitosamente!');
      checkYouTubeStatus();
    } else if (searchParams.get('oauth_error')) {
      toast.error('Error de OAuth: ' + searchParams.get('oauth_error'));
    }
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings`, settings);
      toast.success('Ajustes guardados');
    } catch (e) {
      toast.error('Error al guardar: ' + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
    }
  };

  const handleGetAuthUrl = async () => {
    // First save credentials
    await handleSave();
    try {
      const res = await axios.get(`${API}/settings/youtube/auth-url`);
      setAuthUrl(res.data.auth_url);
      toast.info('Abre el enlace para autorizar YouTube');
    } catch (e) {
      toast.error('Error: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleRevoke = async () => {
    try {
      await axios.post(`${API}/settings/youtube/revoke`);
      setYtStatus({ connected: false });
      toast.success('YouTube desconectado');
    } catch (e) {
      toast.error('Error al desconectar');
    }
  };

  if (loading) return (
    <div className="p-6 space-y-4">{[1,2,3].map(i => <Skeleton key={i} className="h-32 w-full" />)}</div>
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{background: 'radial-gradient(600px circle at 50% -5%, rgba(255,0,0,0.1), transparent 50%)'}} />
        <div className="relative px-6 py-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold" style={{fontFamily: 'Space Grotesk'}}>Ajustes</h1>
            <p className="text-muted-foreground mt-1 text-sm">Configuración de credenciales y automatización</p>
          </div>
          <Button
            className="bg-primary hover:bg-red-600"
            onClick={handleSave}
            disabled={saving}
            data-testid="settings-save-button"
          >
            {saving ? 'Guardando...' : 'Guardar Ajustes'}
          </Button>
        </div>
      </div>

      <div className="px-6 pb-8 space-y-6">

        {/* YouTube OAuth */}
        <Card className="bg-card border-border">
          <CardHeader className="px-5 py-4">
            <div className="flex items-center gap-2">
              <Youtube size={18} className="text-primary" />
              <CardTitle className="text-sm font-semibold">YouTube OAuth 2.0</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="px-5 pb-5 space-y-4">
            {/* Connection Status */}
            {ytStatus && (
              <div className={`flex items-center gap-3 p-3 rounded-lg ${
                ytStatus.connected ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-red-500/10 border border-red-500/30'
              }`}>
                {ytStatus.connected ? (
                  <><CheckCircle size={16} className="text-emerald-300" />
                  <p className="text-sm text-emerald-300">Conectado: {ytStatus.channel?.title}</p></>
                ) : (
                  <><AlertTriangle size={16} className="text-red-300" />
                  <p className="text-sm text-red-300">No conectado</p></>
                )}
              </div>
            )}

            {/* Setup Guide */}
            <Alert className="border-sky-500/30 bg-sky-500/10">
              <AlertDescription className="text-xs text-sky-200">
                <p className="font-semibold mb-1">Guía de configuración:</p>
                <ol className="list-decimal list-inside space-y-0.5">
                  <li>Ve a <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">console.cloud.google.com</a></li>
                  <li>Crea un proyecto y activa YouTube Data API v3</li>
                  <li>Crea credenciales OAuth 2.0 (tipo: Aplicación web)</li>
                  <li>Añade como URI de redirección: <code className="bg-black/30 px-1 rounded">https://tube-optimizer-ai.preview.emergentagent.com/api/youtube/oauth/callback</code></li>
                  <li>Pega Client ID y Secret abajo, guarda, y haz clic en &quot;Conectar YouTube&quot;</li>
                </ol>
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-1 gap-3">
              <div>
                <Label className="text-xs text-muted-foreground">YouTube Client ID</Label>
                <Input
                  placeholder="tu-client-id.apps.googleusercontent.com"
                  value={settings?.youtube_client_id || ''}
                  onChange={e => setSettings({...settings, youtube_client_id: e.target.value})}
                  className="bg-secondary border-border mt-1"
                  data-testid="settings-youtube-client-id-input"
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">YouTube Client Secret</Label>
                <PasswordInput
                  value={settings?.youtube_client_secret || ''}
                  onChange={e => setSettings({...settings, youtube_client_secret: e.target.value})}
                  placeholder="GOCSPX-..."
                  testId="settings-youtube-client-secret-input"
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Refresh Token (se llena automáticamente)</Label>
                <PasswordInput
                  value={settings?.youtube_refresh_token || ''}
                  onChange={e => setSettings({...settings, youtube_refresh_token: e.target.value})}
                  placeholder="Se obtiene al conectar YouTube..."
                  testId="settings-youtube-refresh-token-input"
                />
              </div>
            </div>

            <div className="flex gap-2 flex-wrap">
              <Button
                className="bg-primary hover:bg-red-600"
                onClick={handleGetAuthUrl}
                data-testid="settings-youtube-oauth-connect-button"
              >
                <Youtube size={16} className="mr-2" /> Conectar YouTube
              </Button>
              <Button
                variant="outline"
                className="border-border"
                onClick={checkYouTubeStatus}
                disabled={checkingYt}
                data-testid="settings-youtube-check-status-button"
              >
                {checkingYt ? 'Verificando...' : 'Verificar conexión'}
              </Button>
              {ytStatus?.connected && (
                <Button variant="destructive" size="sm" onClick={handleRevoke}>
                  Desconectar
                </Button>
              )}
            </div>

            {/* Auth URL */}
            {authUrl && (
              <div className="p-3 rounded-lg bg-amber-400/10 border border-amber-400/30">
                <p className="text-xs text-amber-200 font-semibold mb-2">
                  Paso 2: Abre este enlace en tu navegador para autorizar:
                </p>
                <a
                  href={authUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline break-all flex items-center gap-1"
                >
                  <ExternalLink size={12} /> Abrir enlace de autorización YouTube
                </a>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Posting Schedule */}
        <Card className="bg-card border-border">
          <CardHeader className="px-5 py-4">
            <div className="flex items-center gap-2">
              <Clock size={18} className="text-sky-400" />
              <CardTitle className="text-sm font-semibold">Programación de Publicación</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="px-5 pb-5 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs text-muted-foreground">Hora inicio de ventana</Label>
                <Input
                  type="time"
                  value={settings?.posting_window_start || '15:00'}
                  onChange={e => setSettings({...settings, posting_window_start: e.target.value})}
                  className="bg-secondary border-border mt-1"
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Hora fin de ventana</Label>
                <Input
                  type="time"
                  value={settings?.posting_window_end || '20:00'}
                  onChange={e => setSettings({...settings, posting_window_end: e.target.value})}
                  className="bg-secondary border-border mt-1"
                />
              </div>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Máximo de subidas por día</Label>
              <Select
                value={String(settings?.max_daily_uploads || 1)}
                onValueChange={v => setSettings({...settings, max_daily_uploads: parseInt(v)})}
              >
                <SelectTrigger className="bg-secondary border-border mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  <SelectItem value="1">1 video/día (recomendado inicio)</SelectItem>
                  <SelectItem value="2">2 videos/día</SelectItem>
                  <SelectItem value="3">3 videos/día</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-2 block">
                Retraso aleatorio: {settings?.random_delay_minutes || 30} minutos
              </Label>
              <Slider
                min={0}
                max={120}
                step={5}
                value={[settings?.random_delay_minutes || 30]}
                onValueChange={v => setSettings({...settings, random_delay_minutes: v[0]})}
                className="mt-2"
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Privacidad de subida</Label>
              <Select
                value={settings?.upload_privacy || 'public'}
                onValueChange={v => setSettings({...settings, upload_privacy: v})}
              >
                <SelectTrigger className="bg-secondary border-border mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  <SelectItem value="public">Público</SelectItem>
                  <SelectItem value="unlisted">No listado</SelectItem>
                  <SelectItem value="private">Privado</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Anti-Detection */}
        <Card className="bg-card border-border">
          <CardHeader className="px-5 py-4">
            <div className="flex items-center gap-2">
              <Shield size={18} className="text-amber-400" />
              <CardTitle className="text-sm font-semibold">Anti-Detección</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="px-5 pb-5 space-y-4">
            <Alert className="border-amber-400/30 bg-amber-400/10">
              <AlertTriangle size={14} className="text-amber-300" />
              <AlertDescription className="text-xs text-amber-200 ml-2">
                Estas opciones ayudan a que el canal parezca más natural ante YouTube.
                Siempre publica contenido de calidad y cumple con las políticas de YouTube.
              </AlertDescription>
            </Alert>
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/3 border border-border">
              <div>
                <p className="text-sm font-medium">Anti-detección activado</p>
                <p className="text-xs text-muted-foreground">Aplica retrasos aleatorios y variaciones en metadatos</p>
              </div>
              <Switch
                checked={settings?.anti_detection_enabled ?? true}
                onCheckedChange={v => setSettings({...settings, anti_detection_enabled: v})}
                data-testid="settings-anti-detection-switch"
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/3 border border-border">
              <div>
                <p className="text-sm font-medium">COPPA por defecto</p>
                <p className="text-xs text-muted-foreground">Marcar todos los videos como &quot;Hecho para niños&quot;</p>
              </div>
              <Switch
                checked={settings?.made_for_kids_default ?? true}
                onCheckedChange={v => setSettings({...settings, made_for_kids_default: v})}
                data-testid="settings-coppa-switch"
              />
            </div>
          </CardContent>
        </Card>

        {/* GitHub Actions */}
        <Card className="bg-card border-border">
          <CardHeader className="px-5 py-4">
            <div className="flex items-center gap-2">
              <Github size={18} className="text-foreground" />
              <CardTitle className="text-sm font-semibold">GitHub Actions</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="px-5 pb-5 space-y-4">
            <Alert className="border-sky-500/30 bg-sky-500/10">
              <AlertDescription className="text-xs text-sky-200">
                <p className="font-semibold mb-1">Configuración de automatización gratuita:</p>
                <ol className="list-decimal list-inside space-y-0.5">
                  <li>Crea un repositorio en GitHub</li>
                  <li>Añade los secrets: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN</li>
                  <li>Añade el secret EMERGENT_LLM_KEY</li>
                  <li>Descarga el workflow YAML de abajo y súbelo a .github/workflows/</li>
                </ol>
              </AlertDescription>
            </Alert>
            <div className="flex items-center justify-between p-3 rounded-lg bg-white/3 border border-border">
              <div>
                <p className="text-sm font-medium">GitHub Actions habilitado</p>
                <p className="text-xs text-muted-foreground">Publicación automática vía GitHub Actions</p>
              </div>
              <Switch
                checked={settings?.github_actions_enabled ?? false}
                onCheckedChange={v => setSettings({...settings, github_actions_enabled: v})}
                data-testid="settings-github-switch"
              />
            </div>
            <Button
              variant="outline"
              className="border-border w-full"
              onClick={() => {
                const yaml = generateGitHubActionsYaml();
                const blob = new Blob([yaml], { type: 'text/yaml' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'youtube_automation.yml';
                a.click();
                URL.revokeObjectURL(url);
                toast.success('Workflow YAML descargado');
              }}
              data-testid="settings-download-workflow-button"
            >
              <Github size={14} className="mr-2" /> Descargar Workflow YAML
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function generateGitHubActionsYaml() {
  return `name: YouTube Automation Daily\n\non:\n  schedule:\n    - cron: '0 17 * * *'  # Runs daily at 5pm UTC\n  workflow_dispatch: # Allow manual trigger\n\njobs:\n  generate-and-upload:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      \n      - name: Setup Python\n        uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n          cache: 'pip'\n      \n      - name: Install dependencies\n        run: pip install emergentintegrations gtts moviepy pillow yt-dlp google-api-python-client google-auth-oauthlib\n      \n      - name: Run automation pipeline\n        env:\n          EMERGENT_LLM_KEY: \${{ secrets.EMERGENT_LLM_KEY }}\n          YT_CLIENT_ID: \${{ secrets.YT_CLIENT_ID }}\n          YT_CLIENT_SECRET: \${{ secrets.YT_CLIENT_SECRET }}\n          YT_REFRESH_TOKEN: \${{ secrets.YT_REFRESH_TOKEN }}\n        run: |\n          python automation/run_daily.py\n`;
}
