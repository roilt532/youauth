import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { History, ExternalLink, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { Skeleton } from '../components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const StatusBadge = ({ status }) => {
  const map = {
    completed: { label: 'Completado', cls: 'badge-success' },
    running: { label: 'Ejecutando', cls: 'badge-running' },
    failed: { label: 'Fallido', cls: 'badge-failed' },
    pending: { label: 'Pendiente', cls: 'badge-pending' },
  };
  const s = map[status] || { label: status, cls: 'badge-idle' };
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>{s.label}</span>;
};

export default function HistoryPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [logsOpen, setLogsOpen] = useState(false);

  const fetchRuns = async () => {
    try {
      const res = await axios.get(`${API}/runs`, { params: { limit: 50 } });
      setRuns(res.data.runs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRuns(); }, []);

  const openLogs = (run) => {
    setSelectedRun(run);
    setLogsOpen(true);
  };

  const formatDuration = (start, end) => {
    if (!start || !end) return '—';
    const diff = (new Date(end) - new Date(start)) / 1000;
    if (diff < 60) return `${Math.round(diff)}s`;
    return `${Math.round(diff / 60)}m ${Math.round(diff % 60)}s`;
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{background: 'radial-gradient(600px circle at 70% -5%, rgba(255,0,0,0.1), transparent 50%)'}} />
        <div className="relative px-6 py-8">
          <h1 className="text-3xl font-semibold" style={{fontFamily: 'Space Grotesk'}}>Historial de Ejecuciones</h1>
          <p className="text-muted-foreground mt-1 text-sm">{runs.length} ejecuciones registradas</p>
        </div>
      </div>

      <div className="px-6 pb-8">
        <Card className="bg-card border-border">
          <CardContent className="p-0">
            {loading ? (
              <div className="p-5 space-y-3">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-16 w-full" />)}</div>
            ) : runs.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground">
                <History size={48} className="mx-auto mb-3 opacity-20" />
                <p className="text-sm font-medium">No hay ejecuciones aún</p>
                <p className="text-xs mt-1">Ejecuta tu primer job desde la Cola</p>
              </div>
            ) : (
              <div>
                {/* Header */}
                <div className="grid grid-cols-12 gap-4 px-5 py-3 border-b border-border">
                  <span className="col-span-1 text-xs text-muted-foreground font-medium">Estado</span>
                  <span className="col-span-4 text-xs text-muted-foreground font-medium">Job</span>
                  <span className="col-span-2 text-xs text-muted-foreground font-medium">Duración</span>
                  <span className="col-span-3 text-xs text-muted-foreground font-medium">Fecha</span>
                  <span className="col-span-2 text-xs text-muted-foreground font-medium">Acciones</span>
                </div>
                <div className="divide-y divide-border">
                  {runs.map(run => (
                    <div
                      key={run.id}
                      className="grid grid-cols-12 gap-4 px-5 py-4 hover:bg-white/2 items-center"
                      data-testid="history-run-row"
                    >
                      <div className="col-span-1">
                        <StatusBadge status={run.status} />
                      </div>
                      <div className="col-span-4">
                        <p className="text-sm font-medium truncate">{run.job_title || 'Video'}</p>
                        <p className="text-xs text-muted-foreground font-mono">{run.id?.slice(0,8)}...</p>
                      </div>
                      <div className="col-span-2">
                        <span className="text-xs text-muted-foreground">
                          {formatDuration(run.created_at, run.completed_at)}
                        </span>
                      </div>
                      <div className="col-span-3">
                        <span className="text-xs text-muted-foreground">
                          {run.created_at ? new Date(run.created_at).toLocaleString('es-ES') : '—'}
                        </span>
                      </div>
                      <div className="col-span-2 flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-xs hover:bg-white/5"
                          onClick={() => openLogs(run)}
                          data-testid="history-run-logs-open-button"
                        >
                          <Eye size={12} className="mr-1" /> Logs
                        </Button>
                        {run.artifacts?.youtube_url && (
                          <a
                            href={run.artifacts.youtube_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs text-primary hover:bg-primary/10">
                              <ExternalLink size={12} />
                            </Button>
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Logs Modal */}
      <Dialog open={logsOpen} onOpenChange={setLogsOpen}>
        <DialogContent className="bg-card border-border text-foreground max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle style={{fontFamily: 'Space Grotesk'}}>
              Logs: {selectedRun?.job_title || 'Run'}
            </DialogTitle>
          </DialogHeader>
          {selectedRun && (
            <Tabs defaultValue="logs">
              <TabsList className="bg-secondary">
                <TabsTrigger value="logs">Logs</TabsTrigger>
                <TabsTrigger value="steps">Pasos</TabsTrigger>
                <TabsTrigger value="artifacts">Artefactos</TabsTrigger>
              </TabsList>

              <TabsContent value="logs">
                <ScrollArea className="h-80 mt-3">
                  {selectedRun.logs?.length > 0 ? (
                    <div className="space-y-1 font-mono text-xs">
                      {selectedRun.logs.map((log, i) => (
                        <div key={i} className={`${
                          log.level === 'error' ? 'text-red-300' :
                          log.level === 'warning' ? 'text-amber-300' :
                          log.level === 'success' ? 'text-emerald-300' : 'text-muted-foreground'
                        }`}>
                          <span className="opacity-50">[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                          {log.message}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground text-center py-8">No hay logs disponibles</p>
                  )}
                </ScrollArea>
              </TabsContent>

              <TabsContent value="steps">
                <div className="space-y-2 mt-3">
                  {selectedRun.steps?.map(step => (
                    <div key={step.name} className="flex items-center justify-between p-2 rounded-lg bg-white/3">
                      <span className="text-sm">{step.label || step.name}</span>
                      <span className={`text-xs ${
                        step.status === 'completed' ? 'text-emerald-300' :
                        step.status === 'failed' ? 'text-red-300' :
                        step.status === 'running' ? 'text-sky-300' : 'text-muted-foreground'
                      }`}>{step.status}</span>
                    </div>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="artifacts">
                <div className="space-y-2 mt-3">
                  {selectedRun.artifacts?.script && (
                    <div className="p-3 rounded-lg bg-white/3">
                      <p className="text-xs font-semibold text-muted-foreground mb-1">Script</p>
                      <p className="text-xs">ES: {selectedRun.artifacts.script.title_es}</p>
                      <p className="text-xs">EN: {selectedRun.artifacts.script.title_en}</p>
                    </div>
                  )}
                  {selectedRun.artifacts?.youtube_url && (
                    <div className="p-3 rounded-lg bg-emerald-500/10">
                      <p className="text-xs font-semibold text-emerald-300 mb-1">Video YouTube</p>
                      <a href={selectedRun.artifacts.youtube_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline">
                        {selectedRun.artifacts.youtube_url}
                      </a>
                    </div>
                  )}
                  {!selectedRun.artifacts?.script && !selectedRun.artifacts?.youtube_url && (
                    <p className="text-xs text-muted-foreground text-center py-8">No hay artefactos disponibles</p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
