import React from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  Activity,
  Layers,
  KeyRound,
  Radio,
} from 'lucide-react';

export type BadgeVariant =
  | 'demo'
  | 'paper'
  | 'live'
  | 'bullish'
  | 'bearish'
  | 'neutral'
  | 'accent'
  | 'warning'
  | 'success'
  | 'danger'
  | 'purple'
  | 'stale';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  icon?: React.ElementType;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'sm',
  className = '',
  icon: Icon,
}) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-xs font-semibold',
  }[size];

  const variantClasses = {
    demo: 'bg-amber-500/10 text-amber-300 border border-amber-500/30 font-semibold tracking-wider uppercase',
    paper: 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 font-semibold tracking-wider uppercase font-mono',
    live: 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold tracking-wider uppercase font-mono',
    bullish: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono',
    bearish: 'bg-rose-500/10 text-rose-400 border border-rose-500/20 font-mono',
    neutral: 'bg-slate-800/80 text-slate-300 border border-slate-700/80',
    accent: 'bg-sky-500/10 text-sky-400 border border-sky-500/30 font-mono',
    warning: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
    success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border border-rose-500/30',
    purple: 'bg-purple-500/10 text-purple-300 border border-purple-500/30 font-mono',
    stale: 'bg-orange-500/10 text-orange-400 border border-orange-500/30',
  }[variant];

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-full ${sizeClasses} ${variantClasses} ${className}`}
    >
      {Icon && <Icon className="w-3 h-3 shrink-0" />}
      {children}
    </span>
  );
};

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm', className = '' }) => {
  const norm = (status || '').toUpperCase().trim();

  switch (norm) {
    case 'PAPER TRADING':
    case 'SIMULATION':
      return (
        <Badge variant="paper" size={size} icon={Layers} className={className}>
          PAPER TRADING
        </Badge>
      );
    case 'DEMO DATA':
    case 'DEMO':
      return (
        <Badge variant="demo" size={size} icon={ShieldCheck} className={className}>
          DEMO DATA ONLY
        </Badge>
      );
    case 'HISTORICAL DATA':
    case 'CUSTOM_CSV':
      return (
        <Badge variant="accent" size={size} icon={Clock} className={className}>
          HISTORICAL DATA
        </Badge>
      );
    case 'LIVE DATA':
      return (
        <Badge variant="live" size={size} icon={Radio} className={className}>
          LIVE DATA
        </Badge>
      );
    case 'AI ONLINE':
      return (
        <Badge variant="purple" size={size} icon={Sparkles} className={className}>
          AI ONLINE
        </Badge>
      );
    case 'AI UNAVAILABLE':
    case 'AI OFFLINE':
      return (
        <Badge variant="neutral" size={size} icon={AlertTriangle} className={className}>
          AI UNAVAILABLE
        </Badge>
      );
    case 'AI FALLBACK':
    case 'AI FALLBACK ACTIVE':
      return (
        <Badge variant="warning" size={size} icon={Sparkles} className={className}>
          AI FALLBACK ACTIVE
        </Badge>
      );
    case 'RISK PASSED':
    case 'APPROVED':
      return (
        <Badge variant="success" size={size} icon={CheckCircle2} className={className}>
          RISK PASSED
        </Badge>
      );
    case 'RISK BLOCKED':
    case 'REJECTED':
      return (
        <Badge variant="danger" size={size} icon={XCircle} className={className}>
          RISK BLOCKED
        </Badge>
      );
    case 'MARKET OPEN':
    case 'OPEN':
      return (
        <Badge variant="success" size={size} icon={Activity} className={className}>
          MARKET OPEN
        </Badge>
      );
    case 'MARKET CLOSED':
    case 'CLOSED':
      return (
        <Badge variant="neutral" size={size} icon={Clock} className={className}>
          MARKET CLOSED
        </Badge>
      );
    case 'STALE DATA':
    case 'STALE':
      return (
        <Badge variant="stale" size={size} icon={AlertTriangle} className={className}>
          STALE DATA
        </Badge>
      );
    case 'BROKER CONNECTED':
      return (
        <Badge variant="success" size={size} icon={KeyRound} className={className}>
          BROKER CONNECTED
        </Badge>
      );
    case 'BROKER NOT CONNECTED':
      return (
        <Badge variant="neutral" size={size} icon={KeyRound} className={className}>
          BROKER NOT CONNECTED
        </Badge>
      );
    case 'LIVE TRADING DISABLED':
      return (
        <Badge variant="danger" size={size} icon={ShieldAlert} className={className}>
          LIVE BROKER: DISABLED
        </Badge>
      );
    case 'BUY_CANDIDATE':
      return (
        <Badge variant="bullish" size={size} icon={CheckCircle2} className={className}>
          BUY CANDIDATE
        </Badge>
      );
    case 'SELL_CANDIDATE':
      return (
        <Badge variant="bearish" size={size} icon={Activity} className={className}>
          SELL CANDIDATE
        </Badge>
      );
    case 'HOLD':
      return (
        <Badge variant="neutral" size={size} icon={Clock} className={className}>
          HOLD
        </Badge>
      );
    case 'NO_TRADE':
      return (
        <Badge variant="neutral" size={size} icon={XCircle} className={className}>
          NO TRADE
        </Badge>
      );
    case 'INVALID_DATA':
      return (
        <Badge variant="danger" size={size} icon={AlertTriangle} className={className}>
          INVALID DATA
        </Badge>
      );
    case 'EXPIRED':
      return (
        <Badge variant="neutral" size={size} icon={Clock} className={className}>
          EXPIRED
        </Badge>
      );
    default:
      return (
        <Badge variant="neutral" size={size} className={className}>
          {status}
        </Badge>
      );
  }
};
