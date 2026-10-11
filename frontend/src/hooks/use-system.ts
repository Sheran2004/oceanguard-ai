import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { SystemInfo } from '@/types';

let cached: SystemInfo | null = null;
const listeners = new Set<(info: SystemInfo | null) => void>();

export function useSystemInfo(): SystemInfo | null {
  const [info, setInfo] = useState<SystemInfo | null>(cached);

  useEffect(() => {
    const handler = (next: SystemInfo | null) => setInfo(next);
    listeners.add(handler);
    return () => {
      listeners.delete(handler);
    };
  }, []);

  useEffect(() => {
    if (cached) return;
    api
      .systemInfo()
      .then((data) => {
        cached = data;
        listeners.forEach((l) => l(data));
      })
      .catch(() => {
        cached = null;
        listeners.forEach((l) => l(null));
      });
  }, []);

  return info;
}