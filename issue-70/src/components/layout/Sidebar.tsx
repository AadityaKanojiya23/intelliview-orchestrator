import { useState } from 'react';
import {
  LayoutDashboard,
  Zap,
  History,
  BarChart3,
  ChevronRight,
  Cpu,
  Menu,
  X,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

type Page = 'dashboard' | 'benchmark' | 'history' | 'charts';

interface SidebarProps {
  activePage: Page;
  onNavigate: (page: Page) => void;
}

const NAV_ITEMS: { id: Page; label: string; icon: React.FC<{ size?: number; className?: string }> }[] = [
  { id: 'dashboard',  label: 'Dashboard',  icon: LayoutDashboard },
  { id: 'benchmark',  label: 'Run Benchmark', icon: Zap },
  { id: 'history',   label: 'History',     icon: History },
  { id: 'charts',    label: 'Analytics',   icon: BarChart3 },
];

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  const { theme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNav = (page: Page) => {
    onNavigate(page);
    setMobileOpen(false);
  };

  const sidebarContent = (
    <div className="sidebar" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Logo */}
      <div style={{
        padding: '1.5rem 1.25rem 1rem',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div style={{
            width: '2.25rem',
            height: '2.25rem',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1, #7c3aed)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(99,102,241,0.4)',
            flexShrink: 0,
          }}>
            <Cpu size={16} color="#fff" />
          </div>
          <div>
            <div style={{
              fontSize: '0.875rem',
              fontWeight: 700,
              color: '#f1f5f9',
              lineHeight: 1.2,
            }}>
              LLM Bench
            </div>
            <div style={{ fontSize: '0.7rem', color: 'rgba(148,163,184,0.7)', fontWeight: 500 }}>
              Comparison Tool
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: '0.75rem 0.75rem', flex: 1 }}>
        <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'rgba(148,163,184,0.5)', letterSpacing: '0.08em', textTransform: 'uppercase', padding: '0.5rem 0.25rem', marginBottom: '0.25rem' }}>
          Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNav(item.id)}
              className={`nav-item ${isActive ? 'active' : ''}`}
              style={{ marginBottom: '0.15rem' }}
              id={`nav-${item.id}`}
            >
              <Icon size={16} className="nav-icon" />
              <span style={{ flex: 1 }}>{item.label}</span>
              {isActive && <ChevronRight size={14} style={{ opacity: 0.6 }} />}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '1rem 1.25rem',
        borderTop: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{
          fontSize: '0.75rem',
          color: 'rgba(148,163,184,0.5)',
          textAlign: 'center',
        }}>
          No real API calls • Mock data
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.25rem',
          marginTop: '0.25rem',
        }}>
          <div className="pulse-dot" />
          <span style={{ fontSize: '0.7rem', color: 'rgba(16,185,129,0.8)', fontWeight: 500 }}>Simulation Mode</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile menu button */}
      <button
        id="mobile-menu-btn"
        onClick={() => setMobileOpen(!mobileOpen)}
        style={{
          display: 'none',
          position: 'fixed',
          top: '1rem',
          left: '1rem',
          zIndex: 100,
          background: theme === 'dark' ? '#1e293b' : '#fff',
          border: '1px solid var(--border-color)',
          borderRadius: '0.5rem',
          padding: '0.5rem',
          cursor: 'pointer',
          color: 'var(--text-primary)',
          boxShadow: 'var(--shadow-md)',
        }}
        className="mobile-menu-btn"
        aria-label="Toggle menu"
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Overlay */}
      <div
        className={`sidebar-overlay ${mobileOpen ? 'open' : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        {sidebarContent}
      </aside>

      <style>{`
        @media (max-width: 1024px) {
          .mobile-menu-btn { display: flex !important; align-items: center; justify-content: center; }
        }
      `}</style>
    </>
  );
}
