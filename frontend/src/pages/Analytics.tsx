import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import { api } from '@/services/api';
import type { AnalyticsSummary, Mission, TimelinePoint } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { StatTile, Skeleton } from '@/components/ui/primitives';
import { formatNumber, formatPercent } from '@/lib/utils';

const COLORS = ['#22d3ee', '#3b82f6', '#a855f7', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

export function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.analyticsSummary(), api.timeline(), api.listMissions()])
      .then(([s, t, m]) => {
        setSummary(s);
        setTimeline(t);
        setMissions(m);
      })
      .finally(() => setLoading(false));
  }, []);

  const classChart = useMemo(
    () => (summary ? Object.entries(summary.class_distribution).map(([name, value]) => ({ name, value })) : []),
    [summary],
  );

  const priorityChart = useMemo(() => {
    if (!summary) return [];
    const order = ['high', 'medium', 'low', 'review'];
    return order.map((p) => ({ name: p, value: summary.priority_distribution[p] || 0 }));
  }, [summary]);

  const buckets = summary?.confidence_buckets || [];
  const trend = summary?.anomaly_trend || [];

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center gap-3">
        <BarChart3 className="h-5 w-5 text-sonar-cyan" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground">Detection counts, distributions and trends across the platform.</p>
        </div>
      </div>

      {loading && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      )}

      {summary && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
            <StatTile label="Scans" value={formatNumber(summary.total_scans)} tone="cyan" />
            <StatTile label="Missions" value={formatNumber(summary.total_missions)} tone="purple" />
            <StatTile label="Detections" value={formatNumber(summary.total_detections)} tone="emerald" />
            <StatTile label="Marine Debris" value={formatNumber(summary.debris_count)} tone="emerald" />
            <StatTile label="Anomalies" value={formatNumber(summary.anomaly_count)} tone="amber" />
            <StatTile label="High Priority" value={formatNumber(summary.high_priority_count)} tone="red" />
            <StatTile label="Avg Confidence" value={formatPercent(summary.avg_confidence, 1)} tone="cyan" />
            <StatTile
              label="Active Missions"
              value={missions.filter((m) => m.status === 'active').length}
              tone="purple"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Detection Class Distribution</CardTitle>
                <CardDescription>Counts per class label.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
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
                <CardTitle>Priority Mix</CardTitle>
                <CardDescription>AI-assisted review priority levels.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={priorityChart} dataKey="value" nameKey="name" outerRadius={90}>
                        {priorityChart.map((entry, i) => (
                          <Cell
                            key={i}
                            fill={
                              entry.name === 'high'
                                ? '#ef4444'
                                : entry.name === 'medium'
                                  ? '#f59e0b'
                                  : entry.name === 'low'
                                    ? '#22c55e'
                                    : '#a855f7'
                            }
                          />
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

            <Card>
              <CardHeader>
                <CardTitle>Confidence Distribution</CardTitle>
                <CardDescription>Histogram of detection confidence scores.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
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
                <CardTitle>Anomaly / Detection Trend</CardTitle>
                <CardDescription>14-day activity, demo dataset.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer>
                    <LineChart data={trend}>
                      <CartesianGrid stroke="#1e293b" strokeDasharray="2 3" />
                      <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }} />
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
                      <Line dataKey="detections" stroke="#22d3ee" strokeWidth={2} dot={false} name="Detections" />
                      <Line dataKey="anomalies" stroke="#a855f7" strokeWidth={2} dot={false} name="Anomalies" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Mission Statistics</CardTitle>
                <CardDescription>Per-mission aggregate metrics.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer>
                    <BarChart
                      data={missions.map((m) => ({
                        name: m.mission_id,
                        detections: m.detection_count,
                        high: m.high_priority_count,
                      }))}
                    >
                      <CartesianGrid stroke="#1e293b" strokeDasharray="2 3" />
                      <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} />
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
                      <Bar dataKey="detections" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="high" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Scan Timeline</CardTitle>
              <CardDescription>Per-scan detection counts across the platform.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer>
                  <LineChart data={timeline}>
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
                    <Line dataKey="detections" stroke="#22d3ee" strokeWidth={2} name="Detections" />
                    <Line dataKey="anomalies" stroke="#a855f7" strokeWidth={2} name="Anomalies" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}