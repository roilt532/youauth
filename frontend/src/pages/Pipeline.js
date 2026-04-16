import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Zap, CheckCircle, AlertCircle, Clock, Download, RefreshCw, FileText, Volume2, Video, Image, Upload } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Skeleton } from '../components/ui/skeleton';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STEP_ICONS = {
  script: FileText,
  tts: Volume2,
  video_source: Download,
  video_compile: Video,
  thumbnail: Image,
  upload: Upload,
};

const STEP_LABELS = {
  script: 'Generación de Script',
  tts: 'Narración TTS',
  video_source: 'Video Fuente',
  video_compile: 'Compilación',
  thumbnail: 'Miniatura',
  upload: 'Subida YouTube',
};

const StepNode = ({ step, index, total }) => {
  const Icon = STEP_ICONS[step.name] || Zap;
  const stateStyle = {
    idle: 'opacity-60',
    pending: 'opacity-60',
    running: 'ring-1 ring-sky-500/40 shadow-[0_0_0_1px_rgba(46,168,255,0.25)] animate-pulse-ring',
    completed: 'ring-1 ring-emerald-500/35',
    failed: 'ring-1 ring-red-500/35',
    skipped: 'opacity-50',
  };

  const iconColor = {
    idle: 'text-muted-foreground',
    pending: 'text-muted-foreground',
    running: 'text-sky-300',
    completed: 'text-emerald-300',
    failed: 'text-red-300',
    skipped: 'text-muted-foreground',
  };

  const bgColor = {
    idle: 'bg-white/3',
    pending: 'bg-white/3',
    running: 'bg-sky-500/10',
    completed: 'bg-emerald-500/10',
    failed: 'bg-red-500/10',
    skipped: 'bg-white/3',
  };

  const status = step.status || 'pending';

  return (
    <div className="flex flex-col items-center" data-testid={`pipeline-step-${step.name}-status`}>
      <div className={`relative flex items-center gap-3 p-3 rounded-xl border border-border w-full ${stateStyle[status]} ${bgColor[status]}`}>
        <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${bgColor[status]}`}>
          <Icon size={16} className={iconColor[status]} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-foreground">{STEP_LABELS[step.name] || step.name}</p>
          <p className={`text-xs capitalize ${iconColor[status]}`}>{status}</p>
        </div>
        {status === 'completed' && <CheckCircle size={14} className="text-emerald-300 shrink-0" />}
        {status === 'failed' && <AlertCircle size={14} className="text-red-300 shrink-0" />}
        {status === 'running' && (
          <div className="h-3 w-3 rounded-full bg-sky-400 animate-ping shrink-0" />
        )}
      </div>
      {index < total - 1 && (
        <div className={`pipeline-connector w-0.5 h-4 my-0.5 ${status === 'completed' ? 'completed' : ''}`} />
      )}
    </div>
  );
};

export default function Pipeline() {
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [recentRuns, setRecentRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const logsEndRef = useRef(null);

  const fetchPipelineStatus = async () => {
    try {
      const [statusRes, runsRes] = await Promise.all([
        axios.get(`${API}/pipeline/status`),
        axios.get(`${API}/runs`, { params: { limit: 10 } })
      ]);
      setPipelineStatus(statusRes.data);
      setRecentRuns(runsRes.data.runs || []);

      // Auto-select active run
      if (statusRes.data?.active && statusRes.data?.run) {
        setSelectedRun(statusRes.data.run);
      } else if (!selectedRun && runsRes.data.runs?.length > 0) {
        setSelectedRun(runsRes.data.runs[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchSelectedRunDetails = async () => {
    if (!selectedRun?.id) return;
    try {
      const res = await axios.get(`${API}/runs/${selectedRun.id}`);
      setSelectedRun(res.data);
    } catch (e) {}
  };

  useEffect(() => {
    fetchPipelineStatus();
    const interval = setInterval(() => {
      fetchPipelineStatus();
      if (selectedRun?.status === 'running') {
        fetchSelectedRunDetails();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedRun?.id]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [selectedRun?.logs]);

  const isActive = pipelineStatus?.active;
  const activeRun = pipelineStatus?.run;
  const displayRun = selectedRun || activeRun;

  const completedSteps = displayRun?.steps?.filter(s => s.status === 'completed').length || 0;
  const totalSteps = displayRun?.steps?.length || 6;
  const progressPercent = Math.round((completedSteps / totalSteps) * 100);

  const logLevelColor = (level) => ({
    info: 'text-muted-foreground',
    warning: 'text-amber-300',
    error: 'text-red-300',
    success: 'text-emerald-300',
  }[level] || 'text-muted-foreground');

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{background: 'radial-gradient(600px circle at 30% -5%, rgba(46,168,255,0.12), transparent 50%)'}} />
        <div className="relative px-6 py-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold" style={{fontFamily: 'Space Grotesk'}}>Pipeline</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              {isActive ? (
                <span className="text-sky-300">Pipeline ejecutándose...</span>
              ) : 'Monitor de ejecución en tiempo real'}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-border text-muted-foreground hover:text-foreground"
            onClick={fetchPipelineStatus}
            data-testid="pipeline-refresh-button"
          >
            <RefreshCw size={14} className="mr-1" /> Actualizar
          </Button>
        </div>
      </div>

      <div className="px-6 pb-8">
        {loading ? (
          <div className="space-y-4">
            {[1,2,3].map(i => <Skeleton key={i} className="h-32 w-full" />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
            {/* Left: Steps + Progress */}
            <div className="xl:col-span-4 space-y-4">
              {/* Progress overview */}
              <Card className="bg-card border-border">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-medium">
                      {isActive ? 'En Progreso' : displayRun ? 'Última Ejecución' : 'Sin ejecución'}
                    </p>
                    {displayRun && (
                      <span className={`text-xs font-medium ${
                        displayRun.status === 'completed' ? 'text-emerald-300' :
                        displayRun.status === 'failed' ? 'text-red-300' :
                        displayRun.status === 'running' ? 'text-sky-300' : 'text-muted-foreground'
                      }`}>{displayRun.status}</span>
                    )}
                  </div>
                  {displayRun && (
                    <>
                      <Progress value={progressPercent} className="h-2 mb-2" />
                      <p className="text-xs text-muted-foreground">{completedSteps}/{totalSteps} pasos completados</p>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Pipeline steps */}
              <Card className="bg-card border-border">
                <CardHeader className="px-4 py-3">
                  <CardTitle className="text-sm font-semibold">Pasos del Pipeline</CardTitle>
                </CardHeader>
                <CardContent className="px-4 pb-4">
                  {displayRun?.steps ? (
                    <div className="flex flex-col">
                      {displayRun.steps.map((step, i) => (
                        <StepNode key={step.name} step={step} index={i} total={displayRun.steps.length} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Zap size={32} className="mx-auto mb-2 opacity-20" />
                      <p className="text-xs">Inicia un job desde la Cola para ver el pipeline</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Recent runs selector */}
              {recentRuns.length > 0 && (
                <Card className="bg-card border-border">
                  <CardHeader className="px-4 py-3">
                    <CardTitle className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Ejecuciones Recientes</CardTitle>
                  </CardHeader>
                  <CardContent className="px-4 pb-4 space-y-1">
                    {recentRuns.slice(0, 5).map(run => (
                      <button
                        key={run.id}
                        onClick={() => setSelectedRun(run)}
                        className={`w-full text-left p-2 rounded-lg border text-xs ${
                          selectedRun?.id === run.id ? 'bg-white/5 border-white/10' : 'border-transparent hover:bg-white/3'
                        }`}
                      >
                        <p className="font-medium truncate">{run.job_title || 'Run'}</p>
                        <p className={`mt-0.5 ${
                          run.status === 'completed' ? 'text-emerald-400' :
                          run.status === 'failed' ? 'text-red-400' :
                          run.status === 'running' ? 'text-sky-400' : 'text-muted-foreground'
                        }`}>{run.status}</p>
                      </button>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Right: Logs + Artifacts */}
            <div className="xl:col-span-8">
              <Card className="bg-card border-border h-full">
                <Tabs defaultValue="logs" className="h-full">
                  <div className="px-4 pt-4">
                    <TabsList className="bg-secondary">
                      <TabsTrigger value="logs">Logs en Tiempo Real</TabsTrigger>
                      <TabsTrigger value="artifacts">Artefactos</TabsTrigger>
                    </TabsList>
                  </div>

                  <TabsContent value="logs" className="mt-0">
                    <ScrollArea className="h-[500px] px-4 pb-4">
                      {displayRun?.logs?.length > 0 ? (
                        <div className="space-y-0.5 pt-3">
                          {displayRun.logs.map((log, i) => (
                            <div key={i} className={`log-entry ${log.level}`}>
                              <span className="text-muted-foreground">
                                [{new Date(log.timestamp).toLocaleTimeString()}]
                              </span>{' '}
                              <span className={`text-xs ${
                                log.level === 'error' ? 'text-red-300' :
                                log.level === 'warning' ? 'text-amber-300' :
                                log.level === 'success' ? 'text-emerald-300' : 'text-muted-foreground'
                              }`}>{log.message}</span>
                            </div>
                          ))}
                          <div ref={logsEndRef} />
                        </div>
                      ) : (
                        <div className="text-center py-16 text-muted-foreground">
                          <p className="text-xs">Los logs aparecerán aquí durante la ejecución</p>
                        </div>
                      )}
                    </ScrollArea>
                  </TabsContent>

                  <TabsContent value="artifacts" className="mt-0">
                    <div className="p-4 space-y-3">
                      {displayRun?.artifacts ? (
                        Object.keys(displayRun.artifacts).length > 0 ? (
                          <div className="space-y-2">
                            {displayRun.artifacts.script && (
                              <div className="p-3 rounded-lg bg-white/3 border border-border">
                                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Script Generado</p>
                                <p className="text-xs"><strong>ES:</strong> {displayRun.artifacts.script.title_es}</p>
                                <p className="text-xs"><strong>EN:</strong> {displayRun.artifacts.script.title_en}</p>
                                {displayRun.artifacts.script.tags && (
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {displayRun.artifacts.script.tags.slice(0, 6).map(tag => (
                                      <span key={tag} className="px-2 py-0.5 bg-white/5 rounded text-xs text-muted-foreground">#{tag}</span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                            {displayRun.artifacts.youtube_url && (
                              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                                <p className="text-xs font-semibold text-emerald-300 mb-1">Video publicado en YouTube</p>
                                <a
                                  href={displayRun.artifacts.youtube_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary text-xs hover:underline"
                                >
                                  {displayRun.artifacts.youtube_url}
                                </a>
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-xs text-muted-foreground text-center py-8">No hay artefactos aún</p>
                        )
                      ) : (
                        <p className="text-xs text-muted-foreground text-center py-8">Selecciona una ejecución para ver artefactos</p>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
