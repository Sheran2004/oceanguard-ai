import * as React from 'react';
import { cn } from '@/lib/utils';

export const Separator = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('h-px w-full bg-border/60', className)} {...props} />
);

export const Spinner = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      'inline-block h-4 w-4 animate-spin rounded-full border-2 border-sonar-cyan border-t-transparent',
      className,
    )}
    {...props}
  />
);

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('animate-pulse rounded-md bg-secondary/40', className)} {...props} />;
}

export function StatTile({
  label,
  value,
  hint,
  tone = 'default',
  className,
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'default' | 'cyan' | 'emerald' | 'amber' | 'red' | 'purple';
  className?: string;
}) {
  const toneColor: Record<string, string> = {
    default: 'text-foreground',
    cyan: 'text-sonar-cyan',
    emerald: 'text-emerald-300',
    amber: 'text-amber-300',
    red: 'text-red-300',
    purple: 'text-purple-300',
  };
  return (
    <div className={cn('rounded-xl border border-slate-700/50 bg-card/70 p-4 shadow-sonar', className)}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{label}</div>
      <div className={cn('mt-2 text-3xl font-bold', toneColor[tone])}>{value}</div>
      {hint ? <div className="mt-1 text-xs text-muted-foreground/80">{hint}</div> : null}
    </div>
  );
}