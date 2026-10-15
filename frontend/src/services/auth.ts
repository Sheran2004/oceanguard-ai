// Auth helpers — token storage + login/logout API.
import { apiUrl } from './api-base';

const TOKEN_KEY = 'oceanguard.token';
const USER_KEY = 'oceanguard.user';

export interface AuthUser {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role: string;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setUser(user: AuthUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export async function login(username: string, password: string) {
  const res = await fetch(apiUrl('/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<{
    access_token: string;
    token_type: string;
    expires_in: number;
    user: AuthUser;
  }>;
}

export async function register(payload: {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
}) {
  const res = await fetch(apiUrl('/auth/register'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `${res.status} ${res.statusText}`);
  }

  return res.json() as Promise<AuthUser>;
}

export async function fetchMe(token: string): Promise<AuthUser> {
  const res = await fetch(apiUrl('/auth/me'), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}