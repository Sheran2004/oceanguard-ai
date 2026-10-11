import { useEffect, useState } from 'react';
import { Download, FileText, Loader2, RefreshCw } from 'lucide-react';
import { api } from '@/services/api';
import type { Mission, ReportRecord } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';

export function ReportsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [generating, setGenerating] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [m, r] = await Promise.all([api.listMissions(), api.listReports()]);
      setMissions(m);
      setReports(r);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const generate = async (missionId: number) => {
    setGenerating(missionId);
    try {
      await api.generateReport(missionId);
      await load();
    } finally {
      setGenerating(null);
    }
  };

  return (
    <div className="p-6 space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="h-5 w-5 text-sonar-cyan" /> Mission Analysis Reports
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            Generate professional PDF reports for any mission. Includes summary metrics, scan list, important
            detections, AI insight and a disclaimer that AI output requires qualified human verification.
          </p>
        </div>
        <Button variant="subtle" onClick={load}>
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Generate Report</CardTitle>
            <CardDescription>Choose a mission to compile a PDF report.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {missions.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-md border border-border/60 p-3">
                <div>
                  <div className="text-sm font-semibold">{m.name}</div>
                  <div className="text-xs text-muted-foreground font-mono">{m.mission_id}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone="cyan">{m.scan_count} scans</Badge>
                  <Button size="sm" onClick={() => generate(m.id)} disabled={generating === m.id}>
                    {generating === m.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )}
                    Generate PDF
                  </Button>
                </div>
              </div>
            ))}
            {missions.length === 0 && !loading && (
              <div className="text-xs text-muted-foreground">No missions available.</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Generated Reports</CardTitle>
            <CardDescription>{reports.length} report(s) on file.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[60vh] overflow-y-auto scrollbar-thin pr-1">
            {reports.map((r) => (
              <div key={r.id} className="rounded-md border border-border/60 p-3">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-xs">{r.filename}</div>
                  <a
                    href={api.reportDownloadUrl(r.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sonar-cyan text-xs hover:underline inline-flex items-center gap-1"
                  >
                    <Download className="h-3 w-3" /> Download
                  </a>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Mission #{r.mission_id} · {r.generated_by} · {formatDate(r.created_at)}
                </div>
              </div>
            ))}
            {reports.length === 0 && !loading && (
              <div className="text-xs text-muted-foreground">No reports yet. Generate one from a mission.</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Disclaimer</CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground">
          AI-generated detections are decision-support outputs and should be independently verified by qualified
          personnel. Reports include a data-limitations section that reflects this principle.
        </CardContent>
      </Card>
    </div>
  );
}