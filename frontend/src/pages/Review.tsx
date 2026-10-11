import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Download, ShieldCheck, ShieldX, Sparkles, XCircle } from 'lucide-react';
import { api } from '@/services/api';
import type { AnomalyRecord, Detection } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { StatTile } from '@/components/ui/primitives';
import { cn, formatPercent, priorityColor, priorityLabel, classColor, reviewColor, formatDate, downloadBlob } from '@/lib/utils';

type FilterMode = 'pending' | 'review' | 'approved' | 'rejected' | 'all';

export function ReviewPage() {
  const [mode, setMode] = useState<FilterMode>('pending');
  const [items, setItems] = useState<Detection[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);
  const [comments, setComments] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [dets, ans] = await Promise.all([api.listDetections({}), api.anomalies()]);
      setItems(dets);
      setAnomalies(ans);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const counts = useMemo(() => {
    return {
      pending: items.filter((i) => i.review_status === 'pending').length,
      review: items.filter((i) => i.review_status === 'review').length,
      approved: items.filter((i) => i.review_status === 'approved').length,
      rejected: items.filter((i) => i.review_status === 'rejected').length,
    };
  }, [items]);

  const filtered = useMemo(() => {
    if (mode === 'all') return items;
    return items.filter((i) => i.review_status === mode);
  }, [items, mode]);

  const review = async (id: number, decision: 'approved' | 'rejected' | 'review') => {
    setBusy(id);
    try {
      await api.reviewDetection(id, { decision, comment: comments[id] || '' });
      await load();
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="p-6 space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-sonar-cyan" /> Human Review
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Approve, reject or mark detections as needing review. Reviewer decisions and comments are stored and
            can be exported for future model retraining.
          </p>
        </div>
        <Button
          variant="subtle"
          onClick={() => downloadBlob(api.reviewExportUrl(), 'oceanguard_review_dataset.csv')}
        >
          <Download className="h-4 w-4" /> Export Review Dataset
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatTile label="Pending" value={counts.pending} tone="cyan" />
        <StatTile label="Needs Review" value={counts.review} tone="purple" />
        <StatTile label="Approved" value={counts.approved} tone="emerald" />
        <StatTile label="Rejected" value={counts.rejected} tone="red" />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {(['pending', 'review', 'approved', 'rejected', 'all'] as FilterMode[]).map((m) => (
          <Button
            key={m}
            size="sm"
            variant={mode === m ? 'primary' : 'subtle'}
            onClick={() => setMode(m)}
          >
            {m.toUpperCase()}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Review Queue ({filtered.length})</CardTitle>
            <CardDescription>
              {mode === 'pending'
                ? 'Decide on pending AI-assisted review priorities.'
                : `Showing ${mode} detections.`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {filtered.map((d) => (
              <div key={d.id} className="rounded-md border border-border/60 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="font-mono text-xs text-muted-foreground">{d.detection_uid}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={cn('px-1.5 py-0.5 rounded border', classColor(d.class_name))}>
                        {d.class_name}
                      </span>
                      <span className="text-xs">{formatPercent(d.confidence, 1)}</span>
                      <span className={cn('px-1.5 py-0.5 rounded border text-[10px] uppercase', priorityColor(d.priority))}>
                        {priorityLabel(d.priority)}
                      </span>
                      <span className={cn('px-1.5 py-0.5 rounded border text-[10px] uppercase', reviewColor(d.review_status))}>
                        {d.review_status}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button size="sm" variant="subtle" onClick={() => review(d.id, 'approved')} disabled={busy === d.id}>
                      <CheckCircle2 className="h-4 w-4 text-emerald-300" /> Approve
                    </Button>
                    <Button size="sm" variant="subtle" onClick={() => review(d.id, 'rejected')} disabled={busy === d.id}>
                      <XCircle className="h-4 w-4 text-red-300" /> Reject
                    </Button>
                    <Button size="sm" variant="subtle" onClick={() => review(d.id, 'review')} disabled={busy === d.id}>
                      <ShieldX className="h-4 w-4 text-purple-300" /> Needs Review
                    </Button>
                  </div>
                </div>
                {d.explanation && (
                  <div className="mt-2 text-xs text-muted-foreground">{d.explanation}</div>
                )}
                <div className="mt-2 flex items-center gap-2">
                  <input
                    placeholder="Reviewer comment (optional)"
                    className="w-full rounded-md bg-input px-3 py-1.5 text-xs"
                    value={comments[d.id] ?? d.reviewer_comment ?? ''}
                    onChange={(e) => setComments({ ...comments, [d.id]: e.target.value })}
                  />
                </div>
              </div>
            ))}
            {!loading && filtered.length === 0 && (
              <div className="text-xs text-muted-foreground text-center py-6">No detections in this filter.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Unknown Anomaly Worklist</CardTitle>
            <CardDescription>{anomalies.length} anomaly records — review required.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[60vh] overflow-y-auto scrollbar-thin pr-1">
            {anomalies.map((a) => (
              <div key={a.anomaly_id} className="rounded-md border border-border/60 p-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-mono">{a.detection_uid}</div>
                  <Badge tone="purple">{a.score.toFixed(2)}</Badge>
                </div>
                <div className="text-xs mt-1 text-muted-foreground">{a.class_name}</div>
                <div className="text-[11px] text-muted-foreground mt-1">{a.description}</div>
                <div className="text-[11px] text-muted-foreground mt-1">
                  Region: <span className="font-mono">{a.region_label ?? '—'}</span> · {a.method}
                </div>
                {a.created_at && <div className="text-[11px] text-muted-foreground mt-1">{formatDate(a.created_at)}</div>}
              </div>
            ))}
            {anomalies.length === 0 && <div className="text-xs text-muted-foreground">No anomaly records.</div>}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-sonar-cyan" /> Active Learning Note
          </CardTitle>
          <CardDescription>How your reviews improve the system.</CardDescription>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground space-y-2">
          <p>
            Each review you submit is stored and can be exported as CSV via the button above. Approved and rejected
            detections form the next retraining dataset — they include predicted class, confidence, reviewer decision
            and operator comment.
          </p>
          <p>
            Until a real trained model is configured, this dataset prepares the feedback loop but does not change
            inference behaviour.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}