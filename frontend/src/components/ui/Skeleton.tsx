import type { HTMLAttributes } from 'react';

/* ============================================================
   Skeleton Base Component
   ============================================================ */
interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'card' | 'circle' | 'map';
}

function Skeleton({ variant = 'text', className = '', ...props }: SkeletonProps) {
  const baseClass = 'animate-skeleton';

  const variantClass: Record<string, string> = {
    text: 'h-4 w-full rounded',
    card: 'h-24 w-full rounded-lg',
    circle: 'h-10 w-10 rounded-full shrink-0',
    map: 'h-80 w-full rounded-lg',
  };

  return (
    <div
      className={`${baseClass} ${variantClass[variant] || ''} ${className}`}
      {...props}
    />
  );
}

/* ============================================================
   WorldListSkeleton — 世界列表骨架
   ============================================================ */
export function WorldListSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border border-ink-800 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton variant="text" className="w-48 h-5" />
            <Skeleton variant="circle" className="h-6 w-16 rounded-full" />
          </div>
          <Skeleton variant="text" className="w-full h-3" />
          <Skeleton variant="text" className="w-2/3 h-3" />
          <div className="flex gap-4 pt-1">
            <Skeleton variant="text" className="w-20 h-3" />
            <Skeleton variant="text" className="w-20 h-3" />
            <Skeleton variant="text" className="w-20 h-3" />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ============================================================
   SectCardSkeleton — 宗门卡片骨架
   ============================================================ */
export function SectCardSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-1">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 border-b border-ink-800">
          <Skeleton variant="circle" className="h-8 w-8" />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" className="w-24 h-4" />
            <Skeleton variant="text" className="w-full h-1.5" />
          </div>
          <div className="space-y-1">
            <Skeleton variant="text" className="w-12 h-3" />
            <Skeleton variant="text" className="w-12 h-3" />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ============================================================
   MapSkeleton — 地图骨架
   ============================================================ */
export function MapSkeleton() {
  return (
    <div className="relative w-full h-full min-h-[400px] rounded-lg border border-ink-800 overflow-hidden">
      <Skeleton variant="map" className="absolute inset-0" />
      {/* 模拟节点 */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-ink-500 text-sm font-sans">加载地图中...</div>
      </div>
    </div>
  );
}

export default Skeleton;