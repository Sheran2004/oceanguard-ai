import { useEffect, useState } from 'react';
import { Save, ShieldCheck, Sliders, Waves } from 'lucide-react';
import { api } from '@/services/api';
import type { SystemInfo } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/primitives';

export function SettingsPage() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [confThreshold, setConfThreshold] = useState(0.25);
  const [iouThreshold, setIouThreshold] = useState(0.45);
  const [anomalyThreshold, setAnomalyThreshold] = useState(0.65);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.systemInfo().then((data) => {
      setInfo(data);
      setConfThreshold(data.confidence_threshold);
      setIouThreshold(data.iou_threshold);
      setAnomalyThreshold(data.anomaly_threshold);
    });
  }, []);

  const save = () => {
    // The thresholds live in the backend environment. Saving here is a UX
    // stub that updates local state and shows confirmation.
    localStorage.setItem(
      'oceanguard.thresholds',
      JSON.stringify({
        confidence_threshold: confThreshold,
        iou_threshold: iouThreshold,
        anomaly_threshold: anomalyThreshold,
      }),
    );
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Sliders className="h-5 w-5 text-sonar-cyan" /> Settings
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configure inference thresholds and review system metadata. Real configuration is read from environment variables
          when the backend restarts.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inference Thresholds</CardTitle>
          <CardDescription>Adjust confidence, IoU and anomaly thresholds.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ThresholdInput
            label="Confidence Threshold"
            value={confThreshold}
            min={0}
            max={1}
            step={0.01}
            onChange={setConfThreshold}
            help="Detections below this score are dropped."
          />
          <ThresholdInput
            label="IoU Threshold"
            value={iouThreshold}
            min={0}
            max={1}
            step={0.01}
            onChange={setIouThreshold}
            help="Non-max suppression IoU cutoff."
          />
          <ThresholdInput
            label="Anomaly Threshold"
            value={anomalyThreshold}
            min={0}
            max={1}
            step={0.01}
            onChange={setAnomalyThreshold}
            help="Minimum anomaly score to flag unknown patterns."
          />
        </CardContent>
        <div className="flex items-center justify-end gap-3 px-5 pb-5">
          {saved && <span className="text-xs text-emerald-300">Saved locally.</span>}
          <Button onClick={save}>
            <Save className="h-4 w-4" /> Save
          </Button>
        </div>
      </Card>

      {info && (
        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
            <CardDescription>Snapshot of the running backend.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <Info label="Application" value={info.app_name} />
            <Info label="Environment" value={info.app_env} />
            <Info label="Model" value={`${info.model_name} v${info.model_version}`} />
            <Info label="Type" value={info.model_type} />
            <Info label="Mode" value={info.demo_mode ? 'Demo Inference' : 'Production'} tone={info.demo_mode ? 'amber' : 'emerald'} />
            <Info label="Dataset" value={info.dataset_label} />
            <Info label="Model Path" value={info.model_path} mono />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-sonar-cyan" /> Safety &amp; Disclaimers
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground space-y-2">
          <p>
            {info?.disclaimer ||
              'AI-generated detections are decision-support outputs and should be independently verified by qualified personnel.'}
          </p>
          <Separator />
          <p>
            OceanGuard AI does not claim autonomous operational decisions. Operators must always apply domain
            expertise before any survey-based action.
          </p>
          <p>
            <Waves className="inline h-3 w-3 text-sonar-cyan mr-1" />
            Demo coordinates are clearly labelled in the UI. The "Demo Coordinates" tag is shown in the hotspot map
            when synthetic GPS data is in use.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function ThresholdInput({
  label,
  value,
  min,
  max,
  step,
  onChange,
  help,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  help?: string;
}) {
  return (
    <div className="rounded-md border border-border/60 p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="flex items-center gap-2 mt-1">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1 accent-sonar-cyan"
        />
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-20 rounded-md bg-input px-2 py-1 text-sm"
        />
      </div>
      {help && <div className="text-[11px] text-muted-foreground mt-2">{help}</div>}
    </div>
  );
}

function Info({ label, value, tone, mono }: { label: string; value: string; tone?: 'amber' | 'emerald'; mono?: boolean }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={mono ? 'font-mono text-xs' : 'text-sm'}>
        {tone ? (
          <Badge tone={tone}>{value}</Badge>
        ) : (
          value
        )}
      </div>
    </div>
  );
}