import { useState } from 'react';
import { Layout } from './components/layout/Layout';
import { ThemeProvider } from './context/ThemeContext';
import { BenchmarkProvider } from './context/BenchmarkContext';
import { Dashboard } from './pages/Dashboard';
import { Benchmark } from './pages/Benchmark';
import { History } from './pages/History';
import { Charts } from './pages/Charts';

type Page = 'dashboard' | 'benchmark' | 'history' | 'charts';

function AppContent() {
  const [activePage, setActivePage] = useState<Page>('dashboard');

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard />;
      case 'benchmark': return <Benchmark />;
      case 'history':   return <History />;
      case 'charts':    return <Charts />;
      default:          return <Dashboard />;
    }
  };

  return (
    <Layout activePage={activePage} onNavigate={setActivePage}>
      {renderPage()}
    </Layout>
  );
}

function App() {
  return (
    <ThemeProvider>
      <BenchmarkProvider>
        <AppContent />
      </BenchmarkProvider>
    </ThemeProvider>
  );
}

export default App;
