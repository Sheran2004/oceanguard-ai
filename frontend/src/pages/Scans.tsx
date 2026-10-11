import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowLeftRight, ExternalLink, Filter, RefreshCw, ScanSearch, Trash2 } from 'lucide-react';
import { api } from '@/services/api';
import type { CompareResult, Mission, Scan } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn, formatDate, formatNumber } from '@/lib/utils';

export function ScansPage() {
  const [params, setParams] = useSearchParams();
  const missionFilter = params.get('mission');
  const [sourceFilter, setSourceFilter] = useState<'all' | 'real' | 'demo'>('all');
  const [scans, setScans] = useState<Scan[]>([]);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [compareA, setCompareA] = useState<number | null>(null);
  const [compareB, setCompareB] = useState<number | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const missionId = missionFilter ? Number(missionFilter) : undefined;
      const isDemo = sourceFilter === 'all' ? null : sourceFilter === 'demo';
      const [list, ms] = await Promise.all([
        api.listScans(missionId, isDemo),
        api.listMissions(),
      ]);
      setScans(list);
      setMissions(ms);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [missionFilter, sourceFilter]);

  const missionName = useMemo(() => {
    if (!missionFilter) return null;
    return missions.find((m) => m.id === Number(missionFilter))?.name || 'Unknown mission';
  }, [missionFilter, missions]);

  const runCompare = async () => {
    if (!compareA || !compareB) return;
    const res = await api.compareScans(compareA, compareB);
    setCompareResult(res);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ScanSearch className="h-5 w-5 text-sonar-cyan" /> Scan History
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {missionName ? `Scans in mission: ${missionName}` : 'All scans across missions. Filter, compare and export.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md overflow-hidden border border-border/60">
            {(['all', 'real', 'demo'] as const).map((s) => (
              <button
                key={s}
                className={cn(
                  'px-3 py-1.5 text-xs',
                  sourceFilter === s
                    ? s === 'real'
                      ? 'bg-emerald-400 text-sonar-deep font-semibold'
                      : s === 'demo'
                        ? 'bg-amber-400 text-sonar-deep font-semibold'
                        : 'bg-sonar-cyan text-sonar-abyss font-semibold'
                    : 'bg-secondary text-foreground/80',
                )}
                onClick={() => setSourceFilter(s)}
              >
                {s.toUpperCase()}
              </button>
            ))}
          </div>
          {missionFilter && (
            <Button variant="ghost" onClick={() => setParams({})}>
              <Trash2 className="h-4 w-4" /> Clear filter
            </Button>
          )}
          <Button variant="subtle" onClick={load}>
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Temporal Comparison</CardTitle>
          <CardDescription>Select two scans of the same area to compute persistent / new / removed detections.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
            <label>
              <span className="text-xs text-muted-foreground">Scan A</span>
              <select
                className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                value={compareA ?? ''}
                onChange={(e) => setCompareA(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">—</option>
                {scans.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.scan_uid} ({formatDate(s.timestamp, 'unknown')})
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="text-xs text-muted-foreground">Scan B</span>
              <select
                className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                value={compareB ?? ''}
                onChange={(e) => setCompareB(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">—</option>
                {scans.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.scan_uid} ({formatDate(s.timestamp, 'unknown')})
                  </option>
                ))}
              </select>
            </label>
            <div className="flex justify-end">
              <Button onClick={runCompare} disabled={!compareA || !compareB}>
                <ArrowLeftRight className="h-4 w-4" /> Compare
              </Button>
            </div>
          </div>
          {compareResult && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatTile label="Persistent" value={compareResult.persistent} tone="emerald" />
              <StatTile label="New" value={compareResult.new_detections} tone="amber" />
              <StatTile label="Removed" value={compareResult.removed} tone="red" />
              <StatTile label="Changed Regions" value={compareResult.changed_regions} tone="cyan" />
              <div className="md:col-span-4 text-xs text-muted-foreground">
                {compareResult.notes.map((n, i) => (
                  <div key={i}>• {n}</div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All Scans</CardTitle>
          <CardDescription>{scans.length} scan{scans.length === 1 ? '' : 's'} on file.</CardDescription>
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
                  <th className="text-left py-2 pr-3">Location</th>
                  <th className="text-left py-2 pr-3">Detections</th>
                  <th className="text-left py-2 pr-3">Anomalies</th>
                  <th className="text-left py-2 pr-3">High Priority</th>
                  <th className="text-left py-2 pr-3">Status</th>
                  <th className="text-left py-2 pr-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.id} className="border-b border-border/40 hover:bg-secondary/40">
                    <td className="py-2 pr-3 font-mono text-xs">{s.scan_uid}</td>
                    <td className="py-2 pr-3">
                      <Badge tone={s.is_demo ? 'amber' : 'emerald'}>{s.is_demo ? 'DEMO' : 'REAL'}</Badge>
                    </td>
                    <td className="py-2 pr-3 text-xs">#{s.mission_id}</td>
                    <td className="py-2 pr-3 text-xs text-muted-foreground">{formatDate(s.timestamp)}</td>
                    <td className="py-2 pr-3 text-xs font-mono">
                      {s.location
                        ? `${s.location.latitude?.toFixed(2)}, ${s.location.longitude?.toFixed(2)}${s.location.is_demo ? ' (demo)' : ''}`
                        : '—'}
                    </td>
                    <td className="py-2 pr-3 text-xs">{formatNumber(s.detection_count)}</td>
                    <td className="py-2 pr-3 text-xs">{formatNumber(s.anomaly_count)}</td>
                    <td className="py-2 pr-3 text-xs">{formatNumber(s.high_priority_count)}</td>
                    <td className="py-2 pr-3 text-xs">
                      <Badge tone={s.status === 'complete' ? 'emerald' : 'amber'}>{s.status}</Badge>
                    </td>
                    <td className="py-2 pr-3 text-xs space-x-2">
                      <Link to={`/sonar-analysis/${s.id}`} className="text-sonar-cyan hover:underline">
                        Analyze
                      </Link>
                      <Link to={`/scans?compare=${s.id}`} className="text-muted-foreground hover:underline">
                        <ExternalLink className="inline h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
                {!loading && scans.length === 0 && (
                  <tr>
                    <td colSpan={10} className="py-4 text-center text-muted-foreground text-xs">
                      No scans in this filter.
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

function StatTile({ label, value, tone = 'default' }: { label: string; value: number | string; tone?: 'default' | 'cyan' | 'emerald' | 'amber' | 'red' }) {
  const toneColor: Record<string, string> = {
    default: 'text-foreground',
    cyan: 'text-sonar-cyan',
    emerald: 'text-emerald-300',
    amber: 'text-amber-300',
    red: 'text-red-300',
  };
  return (
    <div className={cn('rounded-md border border-border/60 bg-card/60 p-3')}>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={cn('text-xl font-semibold', toneColor[tone])}>{value}</div>
    </div>
  );
}