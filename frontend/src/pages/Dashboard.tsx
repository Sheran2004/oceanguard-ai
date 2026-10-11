import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  Anchor,
  Crosshair,
  Database,
  Filter,
  Layers,
  ScanSearch,
  ShieldAlert,
  Sigma,
  Waves,
} from 'lucide-react';
import { api } from '@/services/api';
import type { AnalyticsSummary, Detection, Scan, TimelinePoint } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { StatTile, Skeleton } from '@/components/ui/primitives';
import { cn, formatDate, formatNumber, formatPercent } from '@/lib/utils';

const COLORS = ['#22d3ee', '#3b82f6', '#a855f7', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

export function DashboardPage() {
  const [includeDemo, setIncludeDemo] = useState(true);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [recentDetections, setRecentDetections] = useState<Detection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [s, t, sc, det] = await Promise.all([
          api.analyticsSummary(includeDemo),
          api.timeline(),
          api.listScans(undefined, includeDemo ? null : false),
          api.listDetections({}),
        ]);
        setSummary(s);
        setTimeline(t.filter((p) => includeDemo || true));
        setScans(sc);
        setRecentDetections(det.slice(0, 6));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [includeDemo]);

  const classChart = useMemo(() => {
    if (!summary) return [];
    return Object.entries(summary.class_distribution).map(([name, value]) => ({ name, value }));
  }, [summary]);

  const priorityChart = useMemo(() => {
    if (!summary) return [];
    const order = ['high', 'medium', 'low', 'review'];
    return order.map((p) => ({ name: p, value: summary.priority_distribution[p] || 0 }));
  }, [summary]);

  const buckets = summary?.confidence_buckets || [];

  const stats = summary
    ? [
        { label: 'Total Scans', value: formatNumber(summary.total_scans), icon: ScanSearch, tone: 'cyan' as const },
        { label: 'Detections', value: formatNumber(summary.total_detections), icon: Crosshair, tone: 'emerald' as const },
        { label: 'Marine Debris', value: formatNumber(summary.debris_count), icon: Waves, tone: 'emerald' as const },
        { label: 'Anomalies', value: formatNumber(summary.anomaly_count), icon: AlertTriangle, tone: 'amber' as const },
        { label: 'High Priority', value: formatNumber(summary.high_priority_count), icon: ShieldAlert, tone: 'red' as const },
        { label: 'Avg Confidence', value: formatPercent(summary.avg_confidence, 1), icon: Activity, tone: 'cyan' as const },
        { label: 'Missions', value: formatNumber(summary.total_missions), icon: Anchor, tone: 'purple' as const },
        {
          label: 'Data Source',
          value: includeDemo ? 'Real + Demo' : 'Real Only',
          icon: Database,
          tone: includeDemo ? 'amber' as const : 'emerald' as const,
          hint: includeDemo ? 'Showing demo + real data' : 'Demo data hidden',
        },
      ]
    : [];

  return (
    <div className="p-6 space-y-6">
      {/* Title row */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-sonar-cyan" />
            <h1 className="text-2xl font-bold tracking-tight">Command Center Dashboard</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Turning underwater sonar imagery into actionable marine intelligence. Use the toggle to view real
            user-uploaded data only, or include demo data for context.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md overflow-hidden border border-border/60">
            <button
              className={cn(
                'px-3 py-1.5 text-xs',
                includeDemo
                  ? 'bg-sonar-cyan text-sonar-abyss font-semibold'
                  : 'bg-secondary text-foreground/80',
              )}
              onClick={() => setIncludeDemo(true)}
            >
              Real + Demo
            </button>
            <button
              className={cn(
                'px-3 py-1.5 text-xs',
                !includeDemo
                  ? 'bg-emerald-400 text-sonar-deep font-semibold'
                  : 'bg-secondary text-foreground/80',
              )}
              onClick={() => setIncludeDemo(false)}
            >
              <Filter className="inline h-3 w-3 mr-1" /> Real Only
            </button>
          </div>
          <Badge tone={includeDemo ? 'amber' : 'emerald'}>
            {includeDemo ? 'Demo Included' : 'Real Only'}
          </Badge>
          <Link to="/sonar-analysis">
            <span className="text-xs text-sonar-cyan hover:underline">Open Sonar Analysis →</span>
          </Link>
        </div>
      </div>

      {/* Real vs Demo split */}
      {summary?.real_vs_demo && (
        <Card>
          <CardHeader>
            <CardTitle>Real vs Demo Data</CardTitle>
            <CardDescription>Operational data vs demo dataset. Real scans come from user uploads.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3">
                <div className="text-[10px] uppercase tracking-wide text-emerald-300 font-semibold">Real Scans</div>
                <div className="text-2xl font-bold text-emerald-300 mt-1">{summary.real_vs_demo.real.scans}</div>
                <div className="text-[11px] text-muted-foreground mt-1">User-uploaded surveys</div>
              </div>
              <div className="rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3">
                <div className="text-[10px] uppercase tracking-wide text-emerald-300 font-semibold">Real Detections</div>
                <div className="text-2xl font-bold text-emerald-300 mt-1">{summary.real_vs_demo.real.detections}</div>
                <div className="text-[11px] text-muted-foreground mt-1">{summary.real_vs_demo.real.anomalies} anomalies · {summary.real_vs_demo.real.high} high</div>
              </div>
              <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
                <div className="text-[10px] uppercase tracking-wide text-amber-300 font-semibold">Demo Scans</div>
                <div className="text-2xl font-bold text-amber-300 mt-1">{summary.real_vs_demo.demo.scans}</div>
                <div className="text-[11px] text-muted-foreground mt-1">Generated by scripts/generate_demo_data.py</div>
              </div>
              <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
                <div className="text-[10px] uppercase tracking-wide text-amber-300 font-semibold">Demo Detections</div>
                <div className="text-2xl font-bold text-amber-300 mt-1">{summary.real_vs_demo.demo.detections}</div>
                <div className="text-[11px] text-muted-foreground mt-1">{summary.real_vs_demo.demo.anomalies} anomalies · {summary.real_vs_demo.demo.high} high</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stat tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
        {stats.map((s) => (
          <StatTile
            key={s.label}
            label={s.label}
            value={s.value}
            tone={s.tone}
            hint={(s as { hint?: string }).hint}
          />
        ))}
        {loading &&
          Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-[88px]" />
          ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Detection Trend (14d)</CardTitle>
            <CardDescription>Detections vs anomaly-flagged regions across recent scans.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer>
                <LineChart data={summary?.anomaly_trend || []}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="2 3" />
                  <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a1f33',
                      border: '1px solid rgba(34, 211, 238, 0.2)',
                      borderRadius: 8,
                      color: '#e0f2fe',
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
                  <Line type="monotone" dataKey="detections" stroke="#22d3ee" strokeWidth={2} dot={false} name="Detections" />
                  <Line type="monotone" dataKey="anomalies" stroke="#a855f7" strokeWidth={2} dot={false} name="Anomalies" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Priority Distribution</CardTitle>
            <CardDescription>AI-assisted review priority across all detections.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={priorityChart}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={48}
                    outerRadius={80}
                    paddingAngle={3}
                  >
                    {priorityChart.map((entry, i) => (
                      <Cell key={i} fill={entry.name === 'high' ? '#ef4444' : entry.name === 'medium' ? '#f59e0b' : entry.name === 'low' ? '#22c55e' : '#a855f7'} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a1f33',
                      border: '1px solid rgba(34, 211, 238, 0.2)',
                      borderRadius: 8,
                      color: '#e0f2fe',
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Detections by Class</CardTitle>
            <CardDescription>Aggregate counts per object class.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer>
                <BarChart data={classChart}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="2 3" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a1f33',
                      border: '1px solid rgba(34, 211, 238, 0.2)',
                      borderRadius: 8,
                      color: '#e0f2fe',
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {classChart.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Confidence Distribution</CardTitle>
            <CardDescription>Detection confidence across the fleet.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer>
                <BarChart data={buckets}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="2 3" />
                  <XAxis dataKey="range" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a1f33',
                      border: '1px solid rgba(34, 211, 238, 0.2)',
                      borderRadius: 8,
                      color: '#e0f2fe',
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Detections</CardTitle>
            <CardDescription>Latest AI-assisted review priorities.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {recentDetections.length === 0 ? (
              <div className="text-xs text-muted-foreground">No detections yet. Upload a scan or generate demo data.</div>
            ) : (
              recentDetections.map((d) => (
                <div key={d.id} className="rounded-md border border-border/60 p-3">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium">{d.class_name}</div>
                    <Badge
                      tone={
                        d.priority === 'high'
                          ? 'red'
                          : d.priority === 'medium'
                            ? 'amber'
                            : d.priority === 'review'
                              ? 'purple'
                              : 'emerald'
                      }
                    >
                      {d.priority.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                    <Sigma className="h-3 w-3" /> {formatPercent(d.confidence, 1)} confidence · {d.detection_uid}
                  </div>
                  {d.explanation ? (
                    <div className="text-xs text-muted-foreground/80 mt-1 line-clamp-2">{d.explanation}</div>
                  ) : null}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scan Timeline</CardTitle>
          <CardDescription>Per-scan detection counts over the dataset lifetime.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={timeline}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="2 3" />
                <XAxis dataKey="scan_uid" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0a1f33',
                    border: '1px solid rgba(34, 211, 238, 0.2)',
                    borderRadius: 8,
                    color: '#e0f2fe',
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
                <Bar dataKey="detections" stackId="a" fill="#22d3ee" name="Detections" />
                <Bar dataKey="anomalies" stackId="a" fill="#a855f7" name="Anomalies" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Recent scans list */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Scans</CardTitle>
          <CardDescription>Last {Math.min(scans.length, 6)} scans with detection counts.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border/50">
                  <th className="text-left py-2 pr-3">Scan ID</th>
                  <th className="text-left py-2 pr-3">Source</th>
                  <th className="text-left py-2 pr-3">Mission</th>
                  <th className="text-left py-2 pr-3">Timestamp</th>
                  <th className="text-left py-2 pr-3">Detections</th>
                  <th className="text-left py-2 pr-3">High Priority</th>
                  <th className="text-left py-2 pr-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {scans.slice(0, 6).map((s) => (
                  <tr key={s.id} className="border-b border-border/40 hover:bg-secondary/40">
                    <td className="py-2 pr-3 font-mono text-xs">{s.scan_uid}</td>
                    <td className="py-2 pr-3">
                      <Badge tone={s.is_demo ? 'amber' : 'emerald'}>{s.is_demo ? 'DEMO' : 'REAL'}</Badge>
                    </td>
                    <td className="py-2 pr-3 text-xs">#{s.mission_id}</td>
                    <td className={cn('py-2 pr-3 text-xs text-muted-foreground')}>{formatDate(s.timestamp)}</td>
                    <td className="py-2 pr-3 text-xs">{s.detection_count}</td>
                    <td className="py-2 pr-3 text-xs">{s.high_priority_count}</td>
                    <td className="py-2 pr-3 text-xs">
                      <Badge tone={s.status === 'complete' ? 'emerald' : s.status === 'failed' ? 'red' : 'cyan'}>
                        {s.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
                {scans.length === 0 && !loading && (
                  <tr>
                    <td colSpan={7} className="py-4 text-center text-muted-foreground text-xs">
                      No scans yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}