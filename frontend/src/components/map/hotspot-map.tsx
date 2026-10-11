import { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip as LeafletTooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { Hotspot } from '@/types';
import { useTheme } from '@/hooks/use-theme';

// Fix default icon paths for Leaflet when bundling with Vite.
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: () => string })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const TONE_COLOR: Record<string, string> = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#22c55e',
};

const DARK_TILES = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const LIGHT_TILES = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

function ThemeTiles() {
  const { theme } = useTheme();
  const map = useMap();
  useEffect(() => {
    // Re-render tiles when the theme changes by invalidating the tile layer.
    map.invalidateSize();
  }, [theme, map]);
  return (
    <TileLayer
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      url={theme === 'light' ? LIGHT_TILES : DARK_TILES}
      key={theme}
    />
  );
}

export function HotspotMap({ hotspots }: { hotspots: Hotspot[] }) {
  const valid = hotspots.filter((h) => h.latitude !== null && h.longitude !== null) as Array<
    Hotspot & { latitude: number; longitude: number }
  >;
  const center: [number, number] =
    valid.length > 0
      ? [valid[0].latitude, valid[0].longitude]
      : [18.5, 65.0];

  return (
    <MapContainer
      center={center}
      zoom={4}
      style={{ height: '100%', minHeight: 480, width: '100%' }}
      scrollWheelZoom
    >
      <ThemeTiles />
      {valid.map((h, i) => (
        <CircleMarker
          key={`${h.region_label}-${i}`}
          center={[h.latitude, h.longitude]}
          radius={Math.min(28, 6 + Math.sqrt(h.detection_count))}
          pathOptions={{ color: TONE_COLOR[h.risk_level] || '#22d3ee', fillOpacity: 0.45, weight: 2 }}
        >
          <LeafletTooltip permanent={false} direction="top" offset={[0, -8]}>
            <div className="text-xs">
              <div className="font-semibold">{h.region_label}</div>
              <div>{h.detection_count} detections</div>
            </div>
          </LeafletTooltip>
          <Popup>
            <div className="space-y-1">
              <div className="font-semibold">{h.region_label}</div>
              <div>Detection hotspot</div>
              <div>Detections: {h.detection_count}</div>
              <div>Anomalies: {h.anomaly_count}</div>
              <div>Avg confidence: {(h.avg_confidence * 100).toFixed(1)}%</div>
              <div className="text-[10px] uppercase tracking-wide opacity-70">
                Risk (AI-assisted): {h.risk_level}
              </div>
              <div className="text-[10px] opacity-70">
                Demo coordinates unless otherwise marked.
              </div>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}