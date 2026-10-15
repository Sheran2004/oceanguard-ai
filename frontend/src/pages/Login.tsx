import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, LogIn, UserPlus, Waves } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/layout/theme-toggle';
import {
  login,
  register,
  setToken,
  setUser,
} from '@/services/auth';

export function LoginPage() {
  const navigate = useNavigate();

  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const switchMode = () => {
    setIsRegister((previous) => !previous);
    setError(null);
    setSuccess(null);
    setPassword('');
    setConfirmPassword('');
  };

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const cleanUsername = username.trim();
    const cleanEmail = email.trim();
    const cleanName = fullName.trim();

    if (isRegister) {
      if (password.length < 6) {
        setError('Password must contain at least 6 characters.');
        return;
      }

      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }

      if (!/^[a-zA-Z0-9_-]{3,80}$/.test(cleanUsername)) {
        setError(
          'Username must be 3–80 characters and contain only letters, numbers, _ or -.',
        );
        return;
      }
    }

    setBusy(true);

    try {
      if (isRegister) {
        await register({
          username: cleanUsername,
          password,
          ...(cleanEmail ? { email: cleanEmail } : {}),
          ...(cleanName ? { full_name: cleanName } : {}),
        });

        setUsername(cleanUsername);
        setPassword('');
        setConfirmPassword('');
        setEmail('');
        setFullName('');
        setIsRegister(false);
        setSuccess('Account created successfully! Please sign in.');
      } else {
        const data = await login(cleanUsername, password);

        setToken(data.access_token);
        setUser(data.user);

        navigate('/dashboard');
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : isRegister
            ? 'Registration failed. Please try again.'
            : 'Login failed. Please try again.',
      );
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
            <div className="text-xs text-muted-foreground">
              Marine Intelligence Platform · SIH 2026
            </div>
          </div>
        </div>

        <h2 className="text-lg font-semibold mb-1">
          {isRegister ? 'Create your account' : 'Sign in to continue'}
        </h2>

        <p className="text-xs text-muted-foreground mb-6">
          {isRegister
            ? 'Register to access the OceanGuard AI platform.'
            : 'Sign in with your registered username and password.'}
        </p>

        <form onSubmit={submit} className="space-y-4">
          {isRegister && (
            <>
              <label className="block">
                <span className="text-xs text-muted-foreground">
                  Full name
                </span>
                <input
                  className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                  maxLength={120}
                  placeholder="Your full name"
                />
              </label>

              <label className="block">
                <span className="text-xs text-muted-foreground">
                  Email address
                </span>
                <input
                  type="email"
                  className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </label>
            </>
          )}

          <label className="block">
            <span className="text-xs text-muted-foreground">Username</span>
            <input
              className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              minLength={3}
              maxLength={80}
              placeholder="Enter username"
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
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              minLength={6}
              placeholder="Enter password"
              required
            />
          </label>

          {isRegister && (
            <label className="block">
              <span className="text-xs text-muted-foreground">
                Confirm password
              </span>
              <input
                type="password"
                className="mt-1 w-full rounded-md bg-input px-3 py-2 text-sm"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                minLength={6}
                placeholder="Re-enter password"
                required
              />
            </label>
          )}

          {error && (
            <div
              role="alert"
              className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded-md p-3"
            >
              {error}
            </div>
          )}

          {success && (
            <div
              role="status"
              className="text-xs text-green-500 bg-green-500/10 border border-green-500/30 rounded-md p-3"
            >
              {success}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : isRegister ? (
              <UserPlus className="h-4 w-4" />
            ) : (
              <LogIn className="h-4 w-4" />
            )}

            {busy
              ? 'Please wait...'
              : isRegister
                ? 'Create Account'
                : 'Sign In'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          {isRegister
            ? 'Already have an account?'
            : "Don't have an account?"}{' '}

          <button
            type="button"
            onClick={switchMode}
            className="font-semibold text-foreground underline underline-offset-4 hover:opacity-80"
          >
            {isRegister ? 'Sign in' : 'Register'}
          </button>
        </div>
      </div>
    </div>
  );
}