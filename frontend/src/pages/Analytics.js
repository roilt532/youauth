import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { TrendingUp, Eye, ThumbsUp, Video, Wifi, WifiOff } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { Button } from '../components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CHART_STYLE = {
  grid: 'rgba(255,255,255,0.06)',
  axis: 'rgba(170,178,197,0.7)',
  primary: '#FF0000',
  secondary: '#2EA8FF',
  success: '#2ED47A'
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-card border border-border rounded-lg p-3 shadow-xl">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-xs" style={{ color: p.color }}>
          {p.name}: {p.value?.toLocaleString()}
        </p>
      ))}
    </div>
  );
};

export default function Analytics() {
  const [data, setData] = useState(null);
  const [runHistory, setRunHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    try {
      const [channelRes, historyRes] = await Promise.all([
        axios.get(`${API}/analytics/channel`),
        axios.get(`${API}/analytics/run-history`)
      ]);
      setData(channelRes.data);
      setRunHistory(historyRes.data.history || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAnalytics(); }, []);

  const chartData = runHistory.slice(0, 14).reverse().map(d => ({
    date: d.date,
    completados: d.completed,
    fallidos: d.failed,
    total: d.total
  }));

  return (
    <div className="min-h-screen bg-background">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{background: 'radial-gradient(600px circle at 60% -5%, rgba(46,168,255,0.14), transparent 50%)'}} />
        <div className="relative px-6 py-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold" style={{fontFamily: 'Space Grotesk'}}>Analytics</h1>
            <p className="text-muted-foreground mt-1 text-sm">Rendimiento del canal y automatización</p>
          </div>
          <Button variant="outline" size="sm" className="border-border" onClick={fetchAnalytics}>
            Actualizar
          </Button>
        </div>
      </div>

      <div className="px-6 pb-8 space-y-6">
        {/* YouTube Connection Status */}
        {!loading && (
          <div className={`flex items-center gap-3 p-4 rounded-xl border ${
            data?.connected
              ? 'border-emerald-500/30 bg-emerald-500/10'
              : 'border-amber-400/30 bg-amber-400/10'
          }`}>
            {data?.connected ? (
              <><Wifi size={18} className="text-emerald-300" />
              <p className="text-sm text-emerald-300">Canal conectado: <strong>{data.channel?.title}</strong></p></>
            ) : (
              <><WifiOff size={18} className="text-amber-300" />
              <div>
                <p className="text-sm text-amber-300">YouTube no conectado</p>
                <p className="text-xs text-muted-foreground">Configura las credenciales OAuth en Ajustes para ver las analíticas del canal</p>
              </div></>
            )}
          </div>
        )}

        {/* Channel KPIs */}
        {data?.connected && data.channel && (
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
            {[
              { icon: Eye, label: 'Vistas Totales', value: data.channel.view_count?.toLocaleString() || 0, color: 'bg-primary' },
              { icon: TrendingUp, label: 'Suscriptores', value: data.channel.subscriber_count?.toLocaleString() || 0, color: 'bg-sky-600' },
              { icon: Video, label: 'Videos Totales', value: data.channel.video_count?.toLocaleString() || 0, color: 'bg-emerald-600' },
              { icon: ThumbsUp, label: 'Likes Totales', value: data.stats?.total_likes?.toLocaleString() || 0, color: 'bg-amber-600' },
            ].map(({ icon: Icon, label, value, color }) => (
              <Card key={label} className="bg-card border-border">
                <CardContent className="p-5">
                  <div className={`h-10 w-10 rounded-xl flex items-center justify-center mb-3 ${color}`}>
                    <Icon size={20} className="text-white" />
                  </div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
                  <p className="text-2xl font-semibold tabular-nums mt-1" style={{fontFamily: 'Space Grotesk'}}>{value}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Automation Run History Chart */}
        <Card className="bg-card border-border">
          <CardHeader className="px-5 py-4">
            <CardTitle className="text-sm font-semibold">Historial de Automatización (14 días)</CardTitle>
          </CardHeader>
          <CardContent className="px-5 pb-5">
            {loading ? (
              <Skeleton className="h-56 w-full" />
            ) : chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} />
                  <XAxis dataKey="date" tick={{ fill: CHART_STYLE.axis, fontSize: 10 }} />
                  <YAxis tick={{ fill: CHART_STYLE.axis, fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', color: CHART_STYLE.axis }} />
                  <Bar dataKey="completados" fill={CHART_STYLE.success} radius={[4,4,0,0]} />
                  <Bar dataKey="fallidos" fill={CHART_STYLE.primary} radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-56 flex items-center justify-center text-muted-foreground">
                <p className="text-sm">No hay datos de automatización aún</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Videos Table */}
        {data?.connected && data.videos?.length > 0 && (
          <Card className="bg-card border-border">
            <CardHeader className="px-5 py-4">
              <CardTitle className="text-sm font-semibold">Top Videos del Canal</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {data.videos.slice(0, 10).map(video => (
                  <div key={video.id} className="flex items-center gap-4 px-5 py-3 hover:bg-white/2">
                    <div className="flex-1 min-w-0">
                      <a href={video.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium hover:text-primary truncate block">
                        {video.title}
                      </a>
                      <p className="text-xs text-muted-foreground">{video.published_at ? new Date(video.published_at).toLocaleDateString('es-ES') : ''}</p>
                    </div>
                    <div className="flex gap-4 text-xs text-muted-foreground shrink-0">
                      <span><Eye size={12} className="inline mr-1" />{video.view_count?.toLocaleString()}</span>
                      <span><ThumbsUp size={12} className="inline mr-1" />{video.like_count?.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
