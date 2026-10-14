import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ChevronRight,
  EyeOff,
  Loader2,
  Maximize2,
  RefreshCw,
  ScanLine,
  Sparkles,
  UploadCloud,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import { api } from '@/services/api';
import type { Detection, Mission, Scan, SystemInfo } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator, Skeleton, StatTile } from '@/components/ui/primitives';
import { cn, formatPercent, priorityColor, priorityLabel, classColor, reviewColor, formatNumber } from '@/lib/utils';

const VIEW_MODES: Array<{ id: 'original' | 'enhanced' | 'overlay'; label: string }> = [
  { id: 'original', label: 'Original' },
  { id: 'enhanced', label: 'Enhanced' },
  { id: 'overlay', label: 'AI Overlay' },
];

const CLASS_COLOR_MAP: Record<string, string> = {
  'Marine Debris': '#22c55e',
  'Fishing Net': '#3b82f6',
  'Plastic Debris': '#facc15',
  'Metal Object': '#ef4444',
  'Man-made Object': '#d946ef',
  'Unknown Anomaly': '#22d3ee',
};

export function SonarAnalysisPage() {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [missions, setMissions] = useState<Mission[]>([]);
  const [selectedMissionId, setSelectedMissionId] = useState<number | ''>('');
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [scan, setScan] = useState<Scan | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [activeDetectionId, setActiveDetectionId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<'original' | 'enhanced' | 'overlay'>('overlay');
  const [showBoxes, setShowBoxes] = useState(true);
  const [zoom, setZoom] = useState<number>(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileMeta, setFileMeta] = useState<{ name: string; size: number; type: string } | null>(null);
  const [previewDataUri, setPreviewDataUri] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string | null>(null);

  useEffect(() => {
    api.listMissions().then(setMissions).catch(() => setMissions([]));
    api.systemInfo().then(setSystemInfo).catch(() => setSystemInfo(null));
  }, []);

  const loadScan = useCallback(async (id: number) => {
    setBusy(true);
    setError(null);
    try {
      const s = await api.getScan(id);
      setScan(s);
      setDetections(s.detections || []);
      setActiveDetectionId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scan');
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (scanId) {
      const id = Number(scanId);
      if (!Number.isNaN(id)) {
        loadScan(id);
      }
    }
  }, [scanId, loadScan]);

  const handleFileSelected = async (file: File) => {
    setError(null);
    setProgressMessage('Reading image…');
    setFileMeta({ name: file.name, size: file.size, type: file.type });
    const reader = new FileReader();
    reader.onload = () => setPreviewDataUri(reader.result as string);
    reader.readAsDataURL(file);
    setBusy(true);
    try {
      setProgressMessage('Uploading…');
      const form = new FormData();
      form.append('file', file);
      if (selectedMissionId) form.append('mission_id', String(selectedMissionId));
      form.append('is_demo', 'false');
      form.append('auto_analyze', 'true');
      setProgressMessage('Running AI inference…');
      const created = await api.uploadScan(form);
      setProgressMessage('Post-processing detections…');
      setScan(created);
      const detail = await api.getScan(created.id);
      setDetections(detail.detections || []);
      setActiveDetectionId(detail.detections?.[0]?.id ?? null);
      navigate(`/sonar-analysis/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setBusy(false);
      setProgressMessage(null);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelected(file);
  };

  const reanalyze = async () => {
    if (!scan) return;
    setBusy(true);
    setError(null);
    try {
      await api.analyzeScan(scan.id);
      const detail = await api.getScan(scan.id);
      setScan(detail);
      setDetections(detail.detections || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reanalysis failed');
    } finally {
      setBusy(false);
    }
  };

  const imageUrl = useMemo(() => {
    if (!scan) return previewDataUri ?? '';
    if (viewMode === 'enhanced') return api.scanEnhancedUrl(scan.id) + `?t=${Date.now()}`;
    if (viewMode === 'overlay') return api.scanOverlayUrl(scan.id) + `?t=${Date.now()}`;
    return api.scanImageUrl(scan.id) + `?t=${Date.now()}`;
  }, [scan, previewDataUri, viewMode]);

  const activeDetection = detections.find((d) => d.id === activeDetectionId) || null;

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ScanLine className="h-5 w-5 text-sonar-cyan" /> Sonar Analysis Workspace
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            Upload a side-scan sonar image. The system validates the file, preprocesses the signal, runs the AI
            inference, computes AI-assisted review priorities and lets you inspect each detection.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {scan && (
            <Badge tone={scan.is_demo ? 'amber' : 'emerald'}>
              {scan.is_demo ? 'DEMO DATA' : 'REAL USER DATA'}
            </Badge>
          )}
          <Badge tone={systemInfo?.is_real_model ? 'emerald' : 'amber'}>
            {systemInfo?.is_real_model ? 'Trained Model' : 'Model Unavailable'}
          </Badge>
          {systemInfo && (
            <Badge tone="cyan">
              {systemInfo.model_name} v{systemInfo.model_version}
            </Badge>
          )}
        </div>
      </div>

      {/* Real/Demo info banner when viewing a scan */}
      {scan && (
        <div
          className={cn(
            'rounded-md border p-3 text-xs flex items-center gap-3',
            scan.is_demo
              ? 'border-amber-500/30 bg-amber-500/5 text-amber-200'
              : 'border-emerald-500/30 bg-emerald-500/5 text-emerald-200',
          )}
        >
          {scan.is_demo ? (
            <>
              <span className="font-semibold">Demo Data</span>
              <span className="text-amber-200/80">
                This scan was generated by the demo data script — coordinates and detections are synthetic.
              </span>
            </>
          ) : (
            <>
              <span className="font-semibold">Uploaded Image</span>
              <span className="text-emerald-200/80">
                This image was uploaded by the operator. Its upload status does not
                indicate that AI detection has been performed successfully.
              </span>
            </>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr_360px] gap-4">
        {/* LEFT — Upload panel */}
        <Card>
          <CardHeader>
            <CardTitle>Upload</CardTitle>
            <CardDescription>Side-scan sonar imagery (PNG, JPG, BMP, TIFF, WEBP).</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              className="rounded-lg border border-dashed border-sonar-cyan/40 bg-sonar-deep/40 hover:bg-sonar-deep/60 transition-colors cursor-pointer p-5 text-center"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={onDrop}
            >
              <UploadCloud className="h-8 w-8 mx-auto text-sonar-cyan" />
              <div className="mt-2 text-sm font-medium">Drop image or click to browse</div>
              <div className="text-xs text-muted-foreground mt-1">PNG · JPG · BMP · TIFF · WEBP · ≤ 25 MB</div>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".png,.jpg,.jpeg,.bmp,.tif,.tiff,.webp,image/*"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFileSelected(f);
                }}
              />
            </div>
            {fileMeta && (
              <div className="mt-3 text-xs text-muted-foreground">
                Selected: <span className="text-foreground">{fileMeta.name}</span> ({Math.round(fileMeta.size / 1024)} KB)
              </div>
            )}

            <div className="mt-4 space-y-3">
              <label className="block">
                <span className="text-xs uppercase tracking-wide text-muted-foreground">Mission</span>
                <select
                  className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                  value={selectedMissionId}
                  onChange={(e) => setSelectedMissionId(e.target.value ? Number(e.target.value) : '')}
                >
                  <option value="">Auto (default mission)</option>
                  {missions.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </label>

              <div className="rounded-md border border-border/60 p-3 text-xs space-y-1">
                <div className="text-foreground/80 font-medium flex items-center gap-2">
                  <Sparkles className="h-3 w-3 text-sonar-cyan" /> Pipeline
                </div>
                <div className="text-muted-foreground">
                  Image Validation → CLAHE + Denoise → Sharpen → Inference → NMS → Anomaly → Priority
                </div>
              </div>

              {progressMessage && (
                <div className="flex items-center gap-2 text-xs text-sonar-cyan">
                  <Loader2 className="h-3 w-3 animate-spin" /> {progressMessage}
                </div>
              )}
              {error && <div className="text-xs text-red-400">{error}</div>}
            </div>
          </CardContent>
        </Card>

        {/* CENTER — Viewer */}
        <Card className="flex flex-col">
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <div>
              <CardTitle>{scan ? `Scan ${scan.scan_uid}` : 'Sonar Viewer'}</CardTitle>
              <CardDescription>
                {scan
                  ? `${scan.original_name} · ${scan.width}×${scan.height}px · ${formatNumber(scan.file_size)} bytes`
                  : 'Upload a sonar image to begin.'}
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex rounded-md overflow-hidden border border-border/60">
                {VIEW_MODES.map((m) => (
                  <button
                    key={m.id}
                    className={cn(
                      'px-3 py-1.5 text-xs',
                      viewMode === m.id
                        ? 'bg-sonar-cyan text-sonar-abyss font-semibold'
                        : 'bg-secondary text-foreground/80 hover:bg-secondary/70',
                    )}
                    onClick={() => setViewMode(m.id)}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
              <Button size="sm" variant="ghost" onClick={() => setShowBoxes((s) => !s)}>
                {showBoxes ? <EyeOff className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                {showBoxes ? 'Hide Boxes' : 'Show Boxes'}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))}>
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="text-xs font-mono">{Math.round(zoom * 100)}%</span>
              <Button size="sm" variant="ghost" onClick={() => setZoom((z) => Math.min(2.5, +(z + 0.1).toFixed(2)))}>
                <ZoomIn className="h-4 w-4" />
              </Button>
              {scan && (
                <Button size="sm" variant="subtle" onClick={reanalyze} disabled={busy}>
                  <RefreshCw className={cn('h-4 w-4', busy && 'animate-spin')} /> Reanalyze
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1 min-h-[460px] relative bg-sonar-abyss sonar-grid overflow-auto">
            {imageUrl ? (
              <div className="relative inline-block" style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
                <img
                  src={imageUrl}
                  alt="sonar"
                  className="max-w-full block"
                  draggable={false}
                  onLoad={() => {/* noop */}}
                />
                {showBoxes && viewMode !== 'overlay' && detections.length > 0 && (
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox={`0 0 ${scan?.width || 1000} ${scan?.height || 1000}`}
                    preserveAspectRatio="xMidYMid meet"
                  >
                    {detections.map((d, idx) => {
                      const color = CLASS_COLOR_MAP[d.class_name] || '#94a3b8';
                      const active = d.id === activeDetectionId;
                      return (
                        <g key={d.id}>
                          <rect
                            x={d.x1}
                            y={d.y1}
                            width={d.x2 - d.x1}
                            height={d.y2 - d.y1}
                            fill="none"
                            stroke={color}
                            strokeWidth={active ? 3 : 1.6}
                          />
                          <text
                            x={d.x1 + 4}
                            y={Math.max(0, d.y1 - 4)}
                            fill={color}
                            fontSize="11"
                            fontFamily="monospace"
                          >
                            #{idx + 1} {d.class_name} {Math.round(d.confidence * 100)}%
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                )}
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground text-sm">
                <ScanLine className="h-10 w-10 mb-3 text-sonar-cyan/70 animate-pulse" />
                <div>No sonar image loaded.</div>
                <div className="text-xs">Drop a file on the left panel to begin analysis.</div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* RIGHT — Detection panel */}
        <Card>
          <CardHeader>
            <CardTitle>Detections</CardTitle>
            <CardDescription>
  {detections.length === 0 ? (
    <div className="space-y-2">
      {systemInfo?.is_real_model ? (
        <>
          <p className="font-medium text-foreground">
            No objects detected at the current confidence threshold.
          </p>

          <p>
            The AI model did not find any objects with sufficient confidence
            in this image. This does not confirm that the image is free of
            marine debris.
          </p>

          <p>
            The model was trained on a water-tank sonar dataset. Results may
            vary on images from different sonar systems or environments.
            Verify important findings manually.
          </p>
        </>
      ) : (
        <p>
          No detections are available because a trained sonar model is not
          configured. No AI predictions were generated.
        </p>
      )}
    </div>
  ) : (
    `${detections.length} detection${detections.length === 1 ? '' : 's'} on this scan.`
  )}
</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[60vh] overflow-y-auto scrollbar-thin pr-1">
            {detections.map((d, idx) => (
              <button
                key={d.id}
                className={cn(
                  'w-full text-left rounded-md border p-3 transition-colors',
                  d.id === activeDetectionId
                    ? 'border-sonar-cyan/60 bg-sonar-cyan/10'
                    : 'border-border/60 hover:border-sonar-cyan/30 hover:bg-secondary/40',
                )}
                onClick={() => setActiveDetectionId(d.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold">DETECTION #{String(idx + 1).padStart(2, '0')}</div>
                  <Badge
                    className={cn(priorityColor(d.priority))}
                  >
                    {priorityLabel(d.priority)}
                  </Badge>
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs">
                  <span className={cn('px-1.5 py-0.5 rounded border', classColor(d.class_name))}>
                    {d.class_name}
                  </span>
                  <span className="text-muted-foreground">{formatPercent(d.confidence, 1)}</span>
                  {d.is_anomaly && <Badge tone="purple">Anomaly</Badge>}
                </div>
                <div className="mt-1 text-[11px] text-muted-foreground font-mono">
                  X:{Math.round(d.x1)} Y:{Math.round(d.y1)} → {Math.round(d.x2)}×{Math.round(d.y2)}
                </div>
              </button>
            ))}
            {!scan && !busy && (
              <div className="text-xs text-muted-foreground">Upload a scan to begin.</div>
            )}
            {busy && (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-[72px]" />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* AI Insight panel */}
      {scan && (
        <Card>
          <CardHeader>
            <CardTitle>Detection Details</CardTitle>
            <CardDescription>
              {activeDetection
                ? `Showing ${activeDetection.class_name} at X:${Math.round(activeDetection.x1)} Y:${Math.round(activeDetection.y1)}`
                : 'Select a detection on the right to view details.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2 space-y-2">
              {activeDetection ? (
                <>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <StatTile label="Class" value={activeDetection.class_name} />
                    <StatTile
                      label="Confidence"
                      value={formatPercent(activeDetection.confidence, 1)}
                      tone="cyan"
                    />
                    <StatTile
                      label="Priority"
                      value={priorityLabel(activeDetection.priority)}
                      tone={
                        activeDetection.priority === 'high'
                          ? 'red'
                          : activeDetection.priority === 'medium'
                            ? 'amber'
                            : activeDetection.priority === 'review'
                              ? 'purple'
                              : 'emerald'
                      }
                    />
                    <StatTile
                      label="Anomaly Score"
                      value={activeDetection.anomaly_score.toFixed(2)}
                      tone={activeDetection.is_anomaly ? 'purple' : 'emerald'}
                    />
                  </div>
                  <div className="rounded-md border border-border/60 p-3 text-xs">
                    <div className="text-foreground/80 font-semibold mb-1">Pixel Coordinates</div>
                    <div className="text-muted-foreground">
                      X: {Math.round(activeDetection.x1)} → {Math.round(activeDetection.x2)} &nbsp;·&nbsp; Y:{' '}
                      {Math.round(activeDetection.y1)} → {Math.round(activeDetection.y2)}
                      <br />
                      Footprint: {Math.round(activeDetection.width)} × {Math.round(activeDetection.height)} px (
                      {(activeDetection.area_ratio * 100).toFixed(2)}% of scan)
                    </div>
                  </div>
                  <div className="rounded-md border border-border/60 p-3 text-xs">
                    <div className="text-foreground/80 font-semibold mb-1">Review Status</div>
                    <Badge className={cn(reviewColor(activeDetection.review_status))}>
                      {activeDetection.review_status.toUpperCase()}
                    </Badge>
                    {activeDetection.reviewer_comment && (
                      <div className="mt-2 text-muted-foreground">"{activeDetection.reviewer_comment}"</div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-xs text-muted-foreground">No detection selected.</div>
              )}
            </div>
            <div className="md:col-span-2 rounded-md border border-border/60 p-3">
              <div className="text-foreground/80 text-xs font-semibold mb-2">AI Explanation</div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {activeDetection?.explanation ||
                  'Select a detection to read the AI explanation. Wording uses terms like "consistent with", "likely", "possible" — AI output is a decision-support signal that requires human verification.'}
              </p>
              <Separator className="my-3" />
              <div className="text-[11px] text-muted-foreground">
                Note: The AI model returns regions that look <em>consistent with</em> the labeled class. Unknown
                underwater anomalies are flagged for review and are NOT classified as dangerous.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick metadata footer */}
      {scan && (
        <Card>
          <CardHeader>
            <CardTitle>Scan Metadata</CardTitle>
            <CardDescription>Operational context for this sonar scan.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div>
              <div className="text-muted-foreground">Status</div>
              <Badge tone={scan.status === 'complete' ? 'emerald' : 'amber'}>{scan.status}</Badge>
            </div>
            <div>
              <div className="text-muted-foreground">Mission</div>
              <div className="font-mono">#{scan.mission_id}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Detections</div>
              <div>{scan.detection_count}</div>
            </div>
            <div>
              <div className="text-muted-foreground">High Priority</div>
              <div>{scan.high_priority_count}</div>
            </div>
            {scan.location && (
              <>
                <div>
                  <div className="text-muted-foreground">Latitude</div>
                  <div className="font-mono">{scan.location.latitude?.toFixed(4) ?? '—'}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Longitude</div>
                  <div className="font-mono">{scan.location.longitude?.toFixed(4) ?? '—'}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Depth</div>
                  <div>{scan.location.depth_m != null ? `${scan.location.depth_m.toFixed(1)} m` : '—'}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Region</div>
                  <div className="font-mono">{scan.location.region_label ?? '—'}</div>
                </div>
              </>
            )}
            {!scan.location && (
              <div className="md:col-span-4 text-xs text-muted-foreground">
                Geolocation unavailable for this scan.
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end">
        <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
          Back to Dashboard <ChevronRight className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}