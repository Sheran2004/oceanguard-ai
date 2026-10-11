// Utility helpers used across components.

export function cn(...args: Array<string | false | null | undefined>) {
  return args.filter(Boolean).join(' ');
}

export function formatPercent(v: number | null | undefined, digits = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return `${(v * 100).toFixed(digits)}%`;
}

export function formatNumber(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return v.toLocaleString();
}

export function formatDate(value: string | null | undefined, fallback = '—'): string {
  if (!value) return fallback;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return fallback;
  return d.toLocaleString();
}

export function priorityColor(p: string | undefined): string {
  switch ((p || '').toLowerCase()) {
    case 'high':
      return 'bg-red-500/15 text-red-300 border-red-500/40';
    case 'medium':
      return 'bg-amber-500/15 text-amber-200 border-amber-500/40';
    case 'low':
      return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40';
    case 'review':
      return 'bg-purple-500/15 text-purple-300 border-purple-500/40';
    default:
      return 'bg-slate-500/15 text-slate-300 border-slate-500/40';
  }
}

export function priorityLabel(p: string | undefined): string {
  switch ((p || '').toLowerCase()) {
    case 'high':
      return 'High';
    case 'medium':
      return 'Medium';
    case 'low':
      return 'Low';
    case 'review':
      return 'Review';
    default:
      return p ?? 'Unknown';
  }
}

export function reviewColor(status: string | undefined): string {
  switch ((status || '').toLowerCase()) {
    case 'approved':
      return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40';
    case 'rejected':
      return 'bg-red-500/15 text-red-300 border-red-500/40';
    case 'review':
      return 'bg-purple-500/15 text-purple-300 border-purple-500/40';
    default:
      return 'bg-slate-500/15 text-slate-300 border-slate-500/40';
  }
}

export function classColor(className: string | undefined): string {
  switch ((className || '').toLowerCase()) {
    case 'marine debris':
      return 'border-emerald-500/40 text-emerald-300';
    case 'fishing net':
      return 'border-blue-500/40 text-blue-300';
    case 'plastic debris':
      return 'border-yellow-500/40 text-yellow-200';
    case 'metal object':
      return 'border-red-500/40 text-red-300';
    case 'man-made object':
      return 'border-fuchsia-500/40 text-fuchsia-300';
    case 'unknown anomaly':
      return 'border-cyan-500/40 text-cyan-300';
    default:
      return 'border-slate-500/40 text-slate-300';
  }
}

export function downloadBlob(url: string, filename: string) {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.target = '_blank';
  link.rel = 'noreferrer';
  document.body.appendChild(link);
  link.click();
  link.remove();
}