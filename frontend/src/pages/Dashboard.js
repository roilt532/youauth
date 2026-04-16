import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Zap, CheckCircle, AlertCircle, Clock, Upload, TrendingUp, Gauge, Play, RotateCcw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Skeleton } from '../components/ui/skeleton';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const StatusBadge = ({ status }) => {
  const map = {
    completed: { label: 'Completado', cls: 'badge-success' },
    running: { label: 'Ejecutando', cls: 'badge-running' },
    failed: { label: 'Fallido', cls: 'badge-failed' },
    pending: { label: 'Pendiente', cls: 'badge-pending' },
    skipped: { label: 'Omitido', cls: 'badge-skipped' },
  };
  const s = map[status] || { label: status, cls: 'badge-idle' };
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>{s.label}</span>;
};

const KPICard = ({ icon: Icon, label, value, delta, color, loading }) => (
  <Card className="bg-card border-border">
    <CardContent className="p-5">
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-10 rounded-xl" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-16" />
        </div>
      ) : (
        <div className="flex items-start justify-between">
          <div>
            <div className={`h-10 w-10 rounded-xl flex items-center justify-center mb-3 ${color}`}>
              <Icon size={20} className="text-white" />
            </div>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{label}</p>
            <p className="text-2xl font-semibold tabular-nums mt-1" style={{fontFamily: 'Space Grotesk'}}>{value}</p>
            {delta !== undefined && (
              <p className={`text-xs mt-1 ${delta >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {delta >= 0 ? '+' : ''}{delta} hoy
              </p>
            )}
          </div>
        </div>
      )}
    </CardContent>
  </Card>
);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/dashboard/stats`);
      setStats(res.data);
    } catch (e) {
      console.error('Stats error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header glow */}
      <div className="relative overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(900px circle at 20% -10%, rgba(255,0,0,0.18), transparent 55%), radial-gradient(700px circle at 85% 0%, rgba(46,168,255,0.14), transparent 52%)'
          }}
        />
        <div className="relative px-6 py-8">
          <div>
            <h1 className="text-3xl font-semibold text-foreground" style={{fontFamily: 'Space Grotesk'}}>
              Panel de Control
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">Automatización completa de YouTube para niños</p>
          </div>
        </div>
      </div>

      <div className="px-6 pb-8 space-y-6">
        {/* KPI Grid */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4" data-testid="dashboard-kpi-grid">
          <KPICard
            icon={Upload}
            label="Videos Subidos"
            value={loading ? '—' : stats?.today_uploads ?? 0}
            delta={stats?.today_uploads}
            color="bg-primary"
            loading={loading}
          />
          <KPICard
            icon={CheckCircle}
            label="Tasa de Éxito"
            value={loading ? '—' : `${stats?.success_rate ?? 0}%`}
            color="bg-emerald-600"
            loading={loading}
          />
          <KPICard
            icon={AlertCircle}
            label="Fallidos"
            value={loading ? '—' : stats?.failed_runs ?? 0}
            color="bg-red-600"
            loading={loading}
          />
          <KPICard
            icon={Clock}
            label="En Cola"
            value={loading ? '—' : stats?.pending_jobs ?? 0}
            color="bg-amber-600"
            loading={loading}
          />
        </div>

        {/* Quota Meter */}
        {!loading && stats && (
          <Card className="bg-card border-border" data-testid="dashboard-quota-meter">
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Gauge size={18} className="text-primary" />
                  <span className="text-sm font-medium">Cuota YouTube API</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {stats.quota_used.toLocaleString()} / {stats.quota_total.toLocaleString()} unidades
                </span>
              </div>
              <Progress
                value={stats.quota_percent}
                className="h-2"
                style={{
                  '--progress-color': stats.quota_percent > 80 ? '#ef4444' : stats.quota_percent > 60 ? '#f59e0b' : '#22c55e'
                }}
              />
              <p className="text-xs text-muted-foreground mt-2">
                {stats.quota_percent}% usado hoy · Límite gratuito: 10,000 unidades/día · 1 subida = 1,600 unidades
              </p>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
          {/* Recent Runs */}
          <div className="xl:col-span-8">
            <Card className="bg-card border-border">
              <CardHeader className="px-5 py-4 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-semibold">Ejecuciones Recientes</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => navigate('/history')} className="text-xs text-muted-foreground hover:text-foreground">
                  Ver todas
                </Button>
              </CardHeader>
              <CardContent className="px-5 pb-5">
                {loading ? (
                  <div className="space-y-3">
                    {[1,2,3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
                  </div>
                ) : stats?.recent_runs?.length > 0 ? (
                  <div className="space-y-2">
                    {stats.recent_runs.map((run) => (
                      <div
                        key={run.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-white/3 hover:bg-white/5 border border-border"
                        data-testid="dashboard-recent-run-row"
                      >
                        <div className="flex items-center gap-3">
                          <StatusBadge status={run.status} />
                          <div>
                            <p className="text-sm font-medium">{run.job_title || 'Video'}</p>
                            <p className="text-xs text-muted-foreground font-mono">{run.id?.slice(0,8)}...</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {run.artifacts?.youtube_url && (
                            <a
                              href={run.artifacts.youtube_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary hover:underline"
                            >
                              Ver video
                            </a>
                          )}
                          <p className="text-xs text-muted-foreground">
                            {run.created_at ? new Date(run.created_at).toLocaleDateString('es-ES') : '—'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Zap size={40} className="mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No hay ejecuciones aún</p>
                    <Button
                      size="sm"
                      className="mt-3 bg-primary hover:bg-red-600"
                      onClick={() => navigate('/queue')}
                      data-testid="dashboard-add-first-job-button"
                    >
                      Crear primer video
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="xl:col-span-4 space-y-4">
            <Card className="bg-card border-border">
              <CardHeader className="px-5 py-4">
                <CardTitle className="text-sm font-semibold">Acciones Rápidas</CardTitle>
              </CardHeader>
              <CardContent className="px-5 pb-5 space-y-3">
                <Button
                  className="w-full bg-primary hover:bg-red-600 text-white"
                  onClick={() => navigate('/queue')}
                  data-testid="dashboard-create-job-button"
                >
                  <Play size={16} className="mr-2" /> Nuevo Video
                </Button>
                <Button
                  variant="outline"
                  className="w-full border-border text-foreground hover:bg-white/5"
                  onClick={() => navigate('/pipeline')}
                  data-testid="dashboard-view-pipeline-button"
                >
                  <Zap size={16} className="mr-2" /> Ver Pipeline
                </Button>
                <Button
                  variant="outline"
                  className="w-full border-border text-foreground hover:bg-white/5"
                  onClick={() => navigate('/analytics')}
                  data-testid="dashboard-view-analytics-button"
                >
                  <TrendingUp size={16} className="mr-2" /> Analytics
                </Button>
              </CardContent>
            </Card>

            {/* Stats summary */}
            <Card className="bg-card border-border">
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">Resumen Total</p>
                {loading ? (
                  <div className="space-y-2">{[1,2,3].map(i => <Skeleton key={i} className="h-4 w-full" />)}</div>
                ) : (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Jobs totales</span>
                      <span className="font-medium">{stats?.total_jobs ?? 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Runs totales</span>
                      <span className="font-medium">{stats?.total_runs ?? 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Completados</span>
                      <span className="font-medium text-emerald-400">{stats?.completed_runs ?? 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Fallidos</span>
                      <span className="font-medium text-red-400">{stats?.failed_runs ?? 0}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
