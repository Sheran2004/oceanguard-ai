import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ScanSearch,
  ListChecks,
  MapPin,
  Waves,
  BarChart3,
  ShieldCheck,
  Cpu,
  FileText,
  Settings,
  History,
  WavesIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

const NAV_GROUPS: { title: string; items: { to: string; label: string; icon: React.ComponentType<{ className?: string }> }[] }[] = [
  {
    title: 'Operations',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/sonar-analysis', label: 'Sonar Analysis', icon: ScanSearch },
      { to: '/missions', label: 'Missions', icon: ListChecks },
      { to: '/scans', label: 'Scan History', icon: History },
      { to: '/detections', label: 'Detections', icon: WavesIcon },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { to: '/hotspots', label: 'Debris Hotspots', icon: MapPin },
      { to: '/analytics', label: 'Analytics', icon: BarChart3 },
      { to: '/review', label: 'Human Review', icon: ShieldCheck },
    ],
  },
  {
    title: 'Platform',
    items: [
      { to: '/models', label: 'Models', icon: Cpu },
      { to: '/reports', label: 'Reports', icon: FileText },
      { to: '/settings', label: 'Settings', icon: Settings },
    ],
  },
];

export function Sidebar({ systemInfo }: { systemInfo?: { demo_mode: boolean; model_name: string; model_version: string } | null }) {
  return (
    <aside className="hidden lg:flex flex-col w-64 shrink-0 border-r border-border/60 bg-card/40 backdrop-blur">
      <div className="px-5 py-5 flex items-center gap-3 border-b border-border/60">
        <div className="h-9 w-9 rounded-md bg-gradient-to-br from-sonar-cyan to-blue-600 flex items-center justify-center shadow-sonar">
          <Waves className="h-5 w-5 text-sonar-abyss" />
        </div>
        <div>
          <div className="text-sm font-semibold tracking-wide">OceanGuard AI</div>
          <div className="text-[11px] text-muted-foreground">Marine Intelligence Platform</div>
        </div>
      </div>

      <div className="px-3 py-4 flex-1 overflow-y-auto scrollbar-thin">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="mb-5">
            <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground/70">
              {group.title}
            </div>
            <nav className="flex flex-col gap-0.5">
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      'group flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                      isActive
                        ? 'bg-sonar-cyan/10 text-sonar-cyan border border-sonar-cyan/30'
                        : 'text-muted-foreground hover:text-foreground hover:bg-secondary/60 border border-transparent',
                    )
                  }
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </nav>
          </div>
        ))}
      </div>

      <div className="border-t border-border/60 px-4 py-4 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>API connected</span>
        </div>
        <div className="mt-2 leading-relaxed">
          Model <span className="text-foreground/80 font-mono">{systemInfo?.model_name ?? '—'}</span> v
          <span className="font-mono">{systemInfo?.model_version ?? '—'}</span>
        </div>
        {systemInfo?.demo_mode ? (
          <Badge tone="amber" className="mt-2">Demo Inference</Badge>
        ) : (
          <Badge tone="emerald" className="mt-2">Real Model</Badge>
        )}
      </div>
    </aside>
  );
}