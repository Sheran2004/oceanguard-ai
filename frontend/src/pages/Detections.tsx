import { useEffect, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { api } from '@/services/api';
import type { Detection } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn, formatPercent, priorityColor, priorityLabel, classColor, reviewColor, formatDate } from '@/lib/utils';

const CLASSES = ['', 'Marine Debris', 'Fishing Net', 'Plastic Debris', 'Metal Object', 'Man-made Object', 'Unknown Anomaly'];

export function DetectionsPage() {
  const [filters, setFilters] = useState({
    class_name: '',
    priority: '',
    is_anomaly: '' as '' | 'true' | 'false',
    min_confidence: '',
    q: '',
  });
  const [items, setItems] = useState<Detection[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filters.class_name) params.class_name = filters.class_name;
      if (filters.priority) params.priority = filters.priority;
      if (filters.is_anomaly) params.is_anomaly = filters.is_anomaly;
      if (filters.min_confidence) params.min_confidence = filters.min_confidence;
      const list = await api.listDetections(params);
      setItems(list);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.class_name, filters.priority, filters.is_anomaly, filters.min_confidence]);

  const filtered = useMemo(() => {
    if (!filters.q) return items;
    const q = filters.q.toLowerCase();
    return items.filter(
      (d) =>
        d.class_name.toLowerCase().includes(q) ||
        d.detection_uid.toLowerCase().includes(q) ||
        (d.explanation || '').toLowerCase().includes(q),
    );
  }, [items, filters.q]);

  return (
    <div className="p-6 space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Detections</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Filter and search every detection across all scans. Click a row to view detail.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Combine class, priority, anomaly flag and confidence threshold.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            <label>
              <span className="text-xs text-muted-foreground">Search</span>
              <div className="mt-1 flex items-center gap-2 rounded-md bg-input px-3 py-2">
                <Search className="h-3.5 w-3.5 text-muted-foreground" />
                <input
                  className="bg-transparent outline-none text-sm flex-1"
                  placeholder="fishing net, DET-..."
                  value={filters.q}
                  onChange={(e) => setFilters({ ...filters, q: e.target.value })}
                />
              </div>
            </label>
            <label>
              <span className="text-xs text-muted-foreground">Class</span>
              <select
                className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                value={filters.class_name}
                onChange={(e) => setFilters({ ...filters, class_name: e.target.value })}
              >
                <option value="">All</option>
                {CLASSES.filter(Boolean).map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="text-xs text-muted-foreground">Priority</span>
              <select
                className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                value={filters.priority}
                onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
              >
                <option value="">All</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
                <option value="review">Review</option>
              </select>
            </label>
            <label>
              <span className="text-xs text-muted-foreground">Anomaly</span>
              <select
                className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                value={filters.is_anomaly}
                onChange={(e) => setFilters({ ...filters, is_anomaly: e.target.value as '' | 'true' | 'false' })}
              >
                <option value="">All</option>
                <option value="true">Anomaly only</option>
                <option value="false">Known only</option>
              </select>
            </label>
            <label>
              <span className="text-xs text-muted-foreground">Min Confidence</span>
              <input
                type="number"
                step="0.05"
                min={0}
                max={1}
                className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                placeholder="0.0 - 1.0"
                value={filters.min_confidence}
                onChange={(e) => setFilters({ ...filters, min_confidence: e.target.value })}
              />
            </label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{filtered.length} detections</CardTitle>
          <CardDescription>Filtered list. Click column headers are not sortable; use filters.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border/50">
                  <th className="text-left py-2 pr-3">Detection</th>
                  <th className="text-left py-2 pr-3">Scan</th>
                  <th className="text-left py-2 pr-3">Class</th>
                  <th className="text-left py-2 pr-3">Confidence</th>
                  <th className="text-left py-2 pr-3">Priority</th>
                  <th className="text-left py-2 pr-3">Anomaly</th>
                  <th className="text-left py-2 pr-3">Review</th>
                  <th className="text-left py-2 pr-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => (
                  <tr key={d.id} className="border-b border-border/40 hover:bg-secondary/40">
                    <td className="py-2 pr-3 font-mono text-xs">{d.detection_uid}</td>
                    <td className="py-2 pr-3 font-mono text-xs">#{d.scan_id}</td>
                    <td className="py-2 pr-3">
                      <span className={cn('px-1.5 py-0.5 rounded border', classColor(d.class_name))}>
                        {d.class_name}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-xs">{formatPercent(d.confidence, 1)}</td>
                    <td className="py-2 pr-3">
                      <span className={cn('inline-block px-1.5 py-0.5 rounded border text-[10px] uppercase', priorityColor(d.priority))}>
                        {priorityLabel(d.priority)}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-xs">
                      {d.is_anomaly ? <Badge tone="purple">Anomaly</Badge> : '—'}
                    </td>
                    <td className="py-2 pr-3">
                      <span className={cn('inline-block px-1.5 py-0.5 rounded border text-[10px] uppercase', reviewColor(d.review_status))}>
                        {d.review_status}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-xs text-muted-foreground">{formatDate(d.created_at)}</td>
                  </tr>
                ))}
                {!loading && filtered.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-6 text-center text-muted-foreground text-xs">
                      No matching detections.
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