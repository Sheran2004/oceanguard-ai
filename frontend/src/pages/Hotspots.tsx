import { useEffect, useState } from 'react';
import { MapPin } from 'lucide-react';
import { api } from '@/services/api';
import type { Hotspot } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { HotspotMap } from '@/components/map/hotspot-map';

export function HotspotsPage() {
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .hotspots()
      .then(setHotspots)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <MapPin className="h-5 w-5 text-sonar-cyan" /> Debris Hotspots
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
          Aggregated by 0.5° tiles. Areas with the most detections and anomaly flags are highlighted. The map uses
          synthetic demo coordinates unless a real survey dataset is configured.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Geospatial Distribution</CardTitle>
            <CardDescription>Marker radius scales with detection count.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="rounded-b-xl overflow-hidden border-t border-border/40">
              <HotspotMap hotspots={hotspots} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hotspot Regions</CardTitle>
            <CardDescription>{hotspots.length} regions aggregated.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[60vh] overflow-y-auto scrollbar-thin pr-1">
            {hotspots.map((h) => (
              <div key={h.region_label} className="rounded-md border border-border/60 p-3">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-sm">{h.region_label}</div>
                  <Badge
                    tone={
                      h.risk_level === 'high' ? 'red' : h.risk_level === 'medium' ? 'amber' : 'emerald'
                    }
                  >
                    {h.risk_level}
                  </Badge>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {h.detection_count} detections · {h.anomaly_count} anomalies · avg {(h.avg_confidence * 100).toFixed(0)}%
                </div>
                {h.latitude !== null && h.longitude !== null && (
                  <div className={cn('mt-1 text-[11px] font-mono text-muted-foreground')}>
                    {h.latitude.toFixed(3)}, {h.longitude.toFixed(3)} · Demo Coordinates
                  </div>
                )}
              </div>
            ))}
            {!loading && hotspots.length === 0 && (
              <div className="text-xs text-muted-foreground">
                No hotspots yet. Upload scans with GPS metadata or run the demo data generator.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>About Hotspot Terminology</CardTitle>
          <CardDescription>The map shows detection hotspots, not confirmed pollution hotspots.</CardDescription>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground space-y-2">
          <p>
            Markers on the map represent aggregated detection counts per region. A "high" risk marker means many
            detections or anomaly events exist there in the dataset — it does NOT mean that pollution has been
            independently confirmed by external sources.
          </p>
          <p>
            Until a detection has been reviewed and approved by qualified personnel, treat all hotspots as
            decision-support signals only.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}