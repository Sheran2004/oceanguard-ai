import { useEffect, useState } from 'react';
import { Activity, Database, Radio } from 'lucide-react';
import { api } from '@/services/api';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/layout/theme-toggle';

interface HealthSnapshot {
  api: 'ok' | 'down';
  detectionRate: number;
}

export function Topbar() {
  const [health, setHealth] = useState<HealthSnapshot>({ api: 'down', detectionRate: 0 });
  const [time, setTime] = useState<string>(new Date().toLocaleTimeString());

  useEffect(() => {
    let mounted = true;
    const tick = async () => {
      try {
        const res = await api.health();
        if (!mounted) return;
        setHealth((h) => ({
          ...h,
          api: res ? 'ok' : 'down',
        }));
      } catch {
        if (!mounted) return;
        setHealth((h) => ({ ...h, api: 'down' }));
      }
    };
    tick();
    const i = setInterval(() => {
      tick();
      setTime(new Date().toLocaleTimeString());
    }, 5000);
    return () => {
      mounted = false;
      clearInterval(i);
    };
  }, []);

  return (
    <header className="h-14 px-6 flex items-center justify-between border-b border-border/60 bg-card/40 backdrop-blur sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">SIH 2026 · PS SIH26057</span>
        <span className="text-xs text-muted-foreground/70">Disaster Management · Software</span>
      </div>
      <div className="flex items-center gap-3 text-xs">
        <ThemeToggle />
        <span className="hidden md:inline text-muted-foreground font-mono">{time}</span>
        <Badge tone={health.api === 'ok' ? 'emerald' : 'red'} className="gap-1">
          <Activity className="h-3 w-3" /> API {health.api.toUpperCase()}
        </Badge>
        <Badge tone="cyan" className="gap-1">
          <Radio className="h-3 w-3" /> Sonar Link
        </Badge>
        <Badge tone="purple" className="gap-1">
          <Database className="h-3 w-3" /> v1.0
        </Badge>
      </div>
    </header>
  );
}