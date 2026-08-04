import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

type Page = 'dashboard' | 'benchmark' | 'history' | 'charts';

interface LayoutProps {
  children: ReactNode;
  activePage: Page;
  onNavigate: (page: Page) => void;
}

export function Layout({ children, activePage, onNavigate }: LayoutProps) {
  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />
      <div className="main-content">
        <Header activePage={activePage} />
        <main className="page-body">
          {children}
        </main>
      </div>
    </div>
  );
}
