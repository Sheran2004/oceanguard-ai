import * as React from 'react';
import { cn } from '@/lib/utils';

type Tone = 'default' | 'cyan' | 'emerald' | 'amber' | 'red' | 'purple' | 'slate';

const tones: Record<Tone, string> = {
  default: 'bg-secondary text-foreground/80 border-border',
  cyan: 'bg-sonar-cyan/10 text-sonar-cyan border-sonar-cyan/30',
  emerald: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  amber: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  red: 'bg-red-500/10 text-red-300 border-red-500/30',
  purple: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
  slate: 'bg-slate-500/10 text-slate-300 border-slate-500/30',
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ className, tone = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide',
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}