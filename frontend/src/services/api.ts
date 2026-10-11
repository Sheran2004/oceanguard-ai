// Centralized API client. All fetch calls go through here so the dev proxy
// can rewrite /api -> backend, and production can use relative URLs.

import { getToken } from './auth';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

async function jsonFetch<T>(input: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init?.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token && !('Authorization' in headers)) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${input}`, { ...init, headers });
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      message = body?.detail || body?.error || message;
    } catch {
      /* ignore parse errors */
    }
    throw new Error(message);
  }
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

export const api = {
  // System
  health: () => jsonFetch<Record<string, unknown>>(`/system/info`),
  systemInfo: () => jsonFetch<import('@/types').SystemInfo>(`/system/info`),
  listModels: () => jsonFetch<import('@/types').ModelVersion[]>(`/models`),

  // Missions
  listMissions: () => jsonFetch<import('@/types').Mission[]>(`/missions`),
  getMission: (id: number) => jsonFetch<import('@/types').Mission>(`/missions/${id}`),
  createMission: (payload: Partial<import('@/types').Mission>) =>
    jsonFetch<import('@/types').Mission>(`/missions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // Scans
  listScans: (missionId?: number, isDemo?: boolean | null) => {
    const params: string[] = [];
    if (missionId !== undefined && missionId !== null) params.push(`mission_id=${missionId}`);
    if (isDemo !== undefined && isDemo !== null) params.push(`is_demo=${isDemo}`);
    const q = params.length ? `?${params.join('&')}` : '';
    return jsonFetch<import('@/types').Scan[]>(`/scans${q}`);
  },
  getScan: (id: number) => jsonFetch<import('@/types').Scan>(`/scans/${id}`),
  uploadScan: (form: FormData) =>
    jsonFetch<import('@/types').Scan>(`/scans/upload`, { method: 'POST', body: form }),
  analyzeScan: (id: number) => jsonFetch<import('@/types').Scan>(`/scans/${id}/analyze`, { method: 'POST' }),
  scanImageUrl: (id: number) => `${API_BASE}/scans/${id}/image`,
  scanOverlayUrl: (id: number) => `${API_BASE}/scans/${id}/overlay`,
  scanEnhancedUrl: (id: number) => `${API_BASE}/scans/${id}/enhanced`,
  compareScans: (scanAId: number, scanBId: number) =>
    jsonFetch<import('@/types').CompareResult>(`/scans/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scan_a_id: scanAId, scan_b_id: scanBId }),
    }),

  // Detections
  listDetections: (params: Record<string, string | number | boolean | undefined | null> = {}) => {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v === undefined || v === null || v === '') return;
      usp.set(k, String(v));
    });
    const q = usp.toString();
    return jsonFetch<import('@/types').Detection[]>(`/detections${q ? `?${q}` : ''}`);
  },
  reviewDetection: (id: number, payload: { decision: string; reviewer?: string; comment?: string }) =>
    jsonFetch<{ id: number; detection_uid: string; review_status: string; reviewer_comment?: string | null }>(
      `/detections/${id}/review`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewer: 'operator', ...payload }),
      },
    ),

  // Analytics
  analyticsSummary: (includeDemo = true) =>
    jsonFetch<import('@/types').AnalyticsSummary>(
      `/analytics/summary${includeDemo ? '' : '?include_demo=false'}`,
    ),
  timeline: () => jsonFetch<import('@/types').TimelinePoint[]>(`/analytics/timeline`),

  // Hotspots
  hotspots: () => jsonFetch<import('@/types').Hotspot[]>(`/hotspots`),

  // Reports
  listReports: (missionId?: number) => {
    const q = missionId ? `?mission_id=${missionId}` : '';
    return jsonFetch<import('@/types').ReportRecord[]>(`/reports${q}`);
  },
  generateReport: (missionId: number) =>
    jsonFetch<import('@/types').ReportRecord>(`/reports/missions/${missionId}`, { method: 'POST' }),
  reportDownloadUrl: (id: number) => `${API_BASE}/reports/${id}/download`,

  // Anomalies
  anomalies: (missionId?: number) => {
    const qs = missionId ? `?mission_id=${missionId}` : '';
    return jsonFetch<import('@/types').AnomalyRecord[]>(`/anomalies${qs}`);
  },

  // Review export
  reviewExportUrl: () => `${API_BASE}/reviews/export`,
};