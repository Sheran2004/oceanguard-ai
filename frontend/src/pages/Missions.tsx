import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Anchor, FileText, Plus, ScanSearch } from 'lucide-react';
import { api } from '@/services/api';
import type { Mission, Scan } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { StatTile } from '@/components/ui/primitives';
import { cn, formatDate, formatNumber } from '@/lib/utils';

export function MissionsPage() {
  const navigate = useNavigate();
  const [missions, setMissions] = useState<Mission[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [draft, setDraft] = useState({ mission_id: '', name: '', survey_area: '', operator: '', description: '' });

  const load = async () => {
    setLoading(true);
    try {
      const [m, s] = await Promise.all([api.listMissions(), api.listScans()]);
      setMissions(m);
      setScans(s);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<number, Scan[]>();
    for (const s of scans) {
      const list = map.get(s.mission_id) || [];
      list.push(s);
      map.set(s.mission_id, list);
    }
    return map;
  }, [scans]);

  const create = async () => {
    if (!draft.mission_id || !draft.name) return;
    await api.createMission({
      mission_id: draft.mission_id,
      name: draft.name,
      survey_area: draft.survey_area || undefined,
      operator: draft.operator || undefined,
      description: draft.description || undefined,
    });
    setDraft({ mission_id: '', name: '', survey_area: '', operator: '', description: '' });
    setCreating(false);
    await load();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Anchor className="h-5 w-5 text-sonar-cyan" /> Mission Management
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            A mission is a logical grouping of side-scan sonar surveys. Track scan counts, detection totals and
            high-priority review queues per mission.
          </p>
        </div>
        <Button onClick={() => setCreating((c) => !c)}>
          <Plus className="h-4 w-4" /> New Mission
        </Button>
      </div>

      {creating && (
        <Card>
          <CardHeader>
            <CardTitle>Create Mission</CardTitle>
            <CardDescription>Missions group scans and detections for reporting.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <label>
                <span className="text-xs text-muted-foreground">Mission ID</span>
                <input
                  className="mt-1 w-full rounded-md bg-input px-3 py-2"
                  value={draft.mission_id}
                  onChange={(e) => setDraft({ ...draft, mission_id: e.target.value })}
                  placeholder="ARABIAN-SEA-2026-001"
                />
              </label>
              <label>
                <span className="text-xs text-muted-foreground">Name</span>
                <input
                  className="mt-1 w-full rounded-md bg-input px-3 py-2"
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  placeholder="Coastal Debris Survey"
                />
              </label>
              <label>
                <span className="text-xs text-muted-foreground">Survey Area</span>
                <input
                  className="mt-1 w-full rounded-md bg-input px-3 py-2"
                  value={draft.survey_area}
                  onChange={(e) => setDraft({ ...draft, survey_area: e.target.value })}
                />
              </label>
              <label>
                <span className="text-xs text-muted-foreground">Operator</span>
                <input
                  className="mt-1 w-full rounded-md bg-input px-3 py-2"
                  value={draft.operator}
                  onChange={(e) => setDraft({ ...draft, operator: e.target.value })}
                />
              </label>
              <label className="md:col-span-2">
                <span className="text-xs text-muted-foreground">Description</span>
                <textarea
                  className="mt-1 w-full rounded-md bg-input px-3 py-2"
                  rows={2}
                  value={draft.description}
                  onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                />
              </label>
            </div>
            <div className="flex justify-end gap-2 mt-3">
              <Button variant="ghost" onClick={() => setCreating(false)}>
                Cancel
              </Button>
              <Button onClick={create}>Save Mission</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {missions.map((m) => {
          const ms = grouped.get(m.id) || [];
          return (
            <Card key={m.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{m.name}</CardTitle>
                    <CardDescription className="font-mono mt-1">{m.mission_id}</CardDescription>
                  </div>
                  <Badge tone={m.status === 'active' ? 'emerald' : 'slate'}>{m.status}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-2">
                  <StatTile label="Scans" value={formatNumber(ms.length)} tone="cyan" />
                  <StatTile label="Detections" value={formatNumber(m.detection_count)} tone="emerald" />
                  <StatTile label="High Priority" value={formatNumber(m.high_priority_count)} tone="red" />
                </div>
                <div className="mt-3 text-xs text-muted-foreground space-y-0.5">
                  <div>
                    <span className="text-muted-foreground/80">Survey Area: </span>
                    {m.survey_area || '—'}
                  </div>
                  <div>
                    <span className="text-muted-foreground/80">Operator: </span>
                    {m.operator || '—'}
                  </div>
                  <div>
                    <span className="text-muted-foreground/80">Created: </span>
                    {formatDate(m.created_at)}
                  </div>
                </div>
                {m.description && (
                  <div className="mt-3 text-xs text-muted-foreground/80 line-clamp-3">{m.description}</div>
                )}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => navigate(`/scans?mission=${m.id}`)}
                  >
                    <ScanSearch className="h-4 w-4" /> View Scans
                  </Button>
                  <Button
                    size="sm"
                    variant="subtle"
                    onClick={async () => {
                      await api.generateReport(m.id);
                      navigate('/reports');
                    }}
                  >
                    <FileText className="h-4 w-4" /> Generate Report
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {!loading && missions.length === 0 && (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              No missions yet. Create one or run the demo data generator.
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>About Demo Data</CardTitle>
          <CardDescription>Numbers shown above reflect the demo dataset unless a real model is configured.</CardDescription>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground">
          To regenerate the demo dataset, run{' '}
          <code className={cn('px-1 py-0.5 rounded bg-secondary/60 font-mono')}>
            python scripts/generate_demo_data.py
          </code>
          . The script creates synthetic side-scan sonar imagery and DEMO DATA labels.
        </CardContent>
      </Card>
    </div>
  );
}