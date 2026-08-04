import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useBenchmark } from '../../context/BenchmarkContext';

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  dashboard: { title: 'Dashboard', subtitle: 'Overview of benchmark activity' },
  benchmark: { title: 'Run Benchmark', subtitle: 'Compare LLMs side by side' },
  history:   { title: 'Benchmark History', subtitle: 'Browse past benchmark runs' },
  charts:    { title: 'Analytics', subtitle: 'Visual performance insights' },
};

interface HeaderProps {
  activePage: string;
}

export function Header({ activePage }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const { runs } = useBenchmark();
  const { title, subtitle } = PAGE_TITLES[activePage] ?? PAGE_TITLES.dashboard;

  return (
    <header className="page-header" style={{ justifyContent: 'space-between' }}>
      {/* Title */}
      <div style={{ paddingLeft: '0.25rem' }}>
        <h1 style={{
          fontSize: '1.125rem',
          fontWeight: 700,
          color: 'var(--text-primary)',
          lineHeight: 1.2,
          margin: 0,
        }}>
          {title}
        </h1>
        <p style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          margin: 0,
          marginTop: '0.15rem',
        }}>
          {subtitle}
        </p>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {/* Benchmark count badge */}
        <div style={{
          background: 'var(--bg-accent)',
          border: '1px solid var(--border-color)',
          borderRadius: '999px',
          padding: '0.35rem 0.875rem',
          fontSize: '0.8125rem',
          color: 'var(--accent-primary)',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
        }}>
          <span style={{
            width: '6px', height: '6px',
            borderRadius: '50%',
            background: 'var(--accent-primary)',
            display: 'inline-block',
          }} />
          {runs.length} runs
        </div>

        {/* Theme toggle */}
        <button
          id="theme-toggle"
          onClick={toggleTheme}
          className="btn btn-icon btn-secondary"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          style={{ color: 'var(--text-secondary)' }}
        >
          {theme === 'dark'
            ? <Sun size={16} />
            : <Moon size={16} />
          }
        </button>
      </div>
    </header>
  );
}
