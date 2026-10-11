import { useEffect, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { api } from '@/services/api';
import type { SystemInfo } from '@/types';
import { getUser, clearToken } from '@/services/auth';
import { Button } from '@/components/ui/button';

export function AppShell() {
  const navigate = useNavigate();
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const user = getUser();

  useEffect(() => {
    if (!user) {
      navigate('/login', { replace: true });
      return;
    }
    api.systemInfo().then(setSystemInfo).catch(() => setSystemInfo(null));
  }, [user, navigate]);

  if (!user) return null;

  const handleLogout = () => {
    clearToken();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen flex bg-background text-foreground">
      <Sidebar
        systemInfo={
          systemInfo
            ? {
                demo_mode: systemInfo.demo_mode,
                model_name: systemInfo.model_name,
                model_version: systemInfo.model_version,
              }
            : null
        }
      />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <Outlet />
        </main>
        <footer className="border-t border-border/60 px-6 py-3 text-[11px] text-muted-foreground flex flex-wrap items-center justify-between gap-2">
          <span>
            © 2026 OceanGuard AI — Decision-support prototype. Detections are AI-assisted review priorities and require
            human verification.
          </span>
          <div className="flex items-center gap-3">
            <span className="font-mono">{user.username} ({user.role})</span>
            <Button size="sm" variant="ghost" onClick={handleLogout}>
              <LogOut className="h-3 w-3" /> Logout
            </Button>
            <span className="font-mono">SIH 2026 · SIH26057</span>
          </div>
        </footer>
      </div>
    </div>
  );
}