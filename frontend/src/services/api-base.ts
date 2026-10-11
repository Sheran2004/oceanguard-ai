/** Shared API base for local proxy and separately deployed backend. */
const configuredBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim();
export const API_BASE = (configuredBase || '/api').replace(/\/+$/, '');

export function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}