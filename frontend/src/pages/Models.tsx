import { useEffect, useState } from 'react';
import { Cpu, Database } from 'lucide-react';
import { api } from '@/services/api';
import type { ModelVersion, SystemInfo } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatTile } from '@/components/ui/primitives';
import { formatDate, formatPercent } from '@/lib/utils';

export function ModelsPage() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [models, setModels] = useState<ModelVersion[]>([]);

  useEffect(() => {
    api.systemInfo().then(setInfo).catch(() => setInfo(null));
    api.listModels().then(setModels).catch(() => setModels([]));
  }, []);

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Cpu className="h-5 w-5 text-sonar-cyan" /> Model Registry
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Track model versions, datasets and inference thresholds. Demo metrics are intentionally not displayed.
        </p>
      </div>

      {info && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatTile label="Active Model" value={info.model_name} tone="cyan" />
          <StatTile label="Version" value={`v${info.model_version}`} tone="cyan" />
          <StatTile label="Type" value={info.model_type} tone="purple" />
          <StatTile label="Confidence Threshold" value={info.confidence_threshold.toFixed(2)} tone="amber" />
          <StatTile label="IoU Threshold" value={info.iou_threshold.toFixed(2)} tone="amber" />
          <StatTile label="Anomaly Threshold" value={info.anomaly_threshold.toFixed(2)} tone="amber" />
          <StatTile label="Mode" value={info.demo_mode ? 'Demo' : 'Production'} tone={info.demo_mode ? 'amber' : 'emerald'} />
          <StatTile label="Dataset" value={info.dataset_label} tone="cyan" />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Configured Object Classes</CardTitle>
          <CardDescription>Loaded from config/classes.yaml — fully editable.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {info &&
              Object.entries(info.classes).map(([cid, meta]) => (
                <div key={cid} className="rounded-md border border-border/60 p-3">
                  <div className="flex items-center justify-between">
                    <div className="font-mono text-xs">id {cid}</div>
                    <Badge tone={meta.is_anomaly ? 'purple' : 'cyan'}>
                      {meta.base_priority}
                    </Badge>
                  </div>
                  <div className="mt-1 text-sm font-semibold">{meta.name}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{meta.description}</div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model Versions</CardTitle>
          <CardDescription>{models.length} model version(s) registered.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border/50">
                  <th className="text-left py-2 pr-3">Name</th>
                  <th className="text-left py-2 pr-3">Version</th>
                  <th className="text-left py-2 pr-3">Type</th>
                  <th className="text-left py-2 pr-3">Dataset</th>
                  <th className="text-left py-2 pr-3">Status</th>
                  <th className="text-left py-2 pr-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.id} className="border-b border-border/40 hover:bg-secondary/40">
                    <td className="py-2 pr-3 font-mono text-xs">{m.name}</td>
                    <td className="py-2 pr-3 text-xs">v{m.version}</td>
                    <td className="py-2 pr-3 text-xs">{m.model_type}</td>
                    <td className="py-2 pr-3 text-xs">{m.dataset || '—'}</td>
                    <td className="py-2 pr-3 text-xs">
                      <Badge tone={m.status === 'demo' ? 'amber' : 'emerald'}>{m.status}</Badge>
                    </td>
                    <td className="py-2 pr-3 text-xs text-muted-foreground">{formatDate(m.created_at)}</td>
                  </tr>
                ))}
                {models.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-4 text-center text-xs text-muted-foreground">
                      No model versions registered.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          {models.some((m) => !m.metrics_json) && (
            <div className="mt-3 text-xs text-muted-foreground flex items-center gap-2">
              <Database className="h-3 w-3" /> Evaluation metrics unavailable for the demo model.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Disclaimer</CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground space-y-2">
          <p>
            The default model loaded by OceanGuard AI is a deterministic demo inference engine. It is intentionally
            easy to swap: replace <code className="font-mono px-1 py-0.5 bg-secondary/60 rounded">model_loader.py</code>{' '}
            with a real checkpoint loader (e.g. Ultralytics YOLO), or set <code className="font-mono px-1 py-0.5 bg-secondary/60 rounded">ENABLE_DEMO_MODE=false</code>{' '}
            in your <code className="font-mono px-1 py-0.5 bg-secondary/60 rounded">.env</code> and provide a real
            weights file at <code className="font-mono px-1 py-0.5 bg-secondary/60 rounded">MODEL_PATH</code>.
          </p>
          <p>
            Until a real, validated deployment model is configured, the system displays the "Demo Inference" badge
            and never claims production accuracy.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}