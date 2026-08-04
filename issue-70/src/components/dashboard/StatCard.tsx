import type { ReactNode } from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  iconBg: string;
  gradientStart: string;
  gradientEnd: string;
  subtext?: string;
  delay?: number;
}

export function StatCard({
  label,
  value,
  icon,
  iconBg,
  gradientStart,
  gradientEnd,
  subtext,
  delay = 0,
}: StatCardProps) {
  return (
    <div
      className="stat-card animate-fade-in-up"
      style={{
        '--gradient-start': gradientStart,
        '--gradient-end': gradientEnd,
        animationDelay: `${delay}ms`,
        opacity: 0,
      } as React.CSSProperties}
    >
      <div
        className="stat-icon-wrapper"
        style={{ background: iconBg }}
      >
        {icon}
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {subtext && (
        <div style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginTop: '0.375rem',
          fontWeight: 400,
        }}>
          {subtext}
        </div>
      )}
    </div>
  );
}
