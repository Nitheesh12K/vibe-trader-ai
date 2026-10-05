import React from 'react';

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => {
  return (
    <div
      className={`animate-pulse bg-white/[0.05] rounded-lg ${className}`}
      aria-hidden="true"
    />
  );
};

export const SkeletonCard: React.FC<{ count?: number }> = ({ count = 1 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-[#0D1322]/80 border border-white/[0.08] rounded-2xl p-5 space-y-3"
        >
          <div className="flex justify-between items-center">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-5 w-12 rounded-full" />
          </div>
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-3 w-full" />
        </div>
      ))}
    </div>
  );
};

export const SkeletonRow: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 4,
  cols = 5,
}) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, r) => (
        <div
          key={r}
          className="flex items-center gap-3 p-3 bg-white/[0.02] border border-white/[0.04] rounded-lg"
        >
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
};
