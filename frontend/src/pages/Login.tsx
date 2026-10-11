import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, LogIn, Waves } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/layout/theme-toggle';
import { login, setToken, setUser } from '@/services/auth';

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('demo-operator');
  const [password, setPassword] = useState('demo123');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const data = await login(username, password);
      setToken(data.access_token);
      setUser(data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background sonar-grid p-6">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md rounded-2xl border bg-card/80 backdrop-blur shadow-sonar p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-11 w-11 rounded-md bg-gradient-to-br from-sonar-cyan to-blue-600 flex items-center justify-center shadow-sonar">
            <Waves className="h-6 w-6 text-sonar-abyss" />
          </div>
          <div>
            <div className="text-xl font-bold">OceanGuard AI</div>
            <div className="text-xs text-muted-foreground">Marine Intelligence Platform · SIH 2026</div>
          </div>
        </div>

        <h2 className="text-lg font-semibold mb-1">Sign in to continue</h2>
        <p className="text-xs text-muted-foreground mb-6">
          Use the seeded credentials or any account created via{' '}
          <code className="font-mono text-foreground/80">/api/auth/register</code>.
        </p>

        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="text-xs text-muted-foreground">Username</span>
            <input
              className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>

          <label className="block">
            <span className="text-xs text-muted-foreground">Password</span>
            <input
              type="password"
              className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && (
            <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-md p-2">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
            Sign in
          </Button>
        </form>

        <div className="mt-6 text-xs text-muted-foreground border-t border-border/40 pt-4 space-y-1">
          <div>
            Demo accounts (created by the seeder):
          </div>
          <div className="font-mono">
            admin / admin123 &nbsp;·&nbsp; demo-operator / demo123
          </div>
          <div className="text-[11px] opacity-70">
            Rotate these credentials before any non-demo deployment.
          </div>
        </div>
      </div>
    </div>
  );
}