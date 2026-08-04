import { useState } from 'react';
import { Search, Download, Trash2, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { useBenchmark } from '../../context/BenchmarkContext';
import { exportToCsv, exportSingleRun } from '../../utils/csvExport';
import { getModelById } from '../../data/models';
import { ResultsTable } from '../benchmark/ResultsTable';
import type { BenchmarkRun } from '../../types';

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'Just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

function HistoryCard({ run, onDelete }: { run: BenchmarkRun; onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="card animate-fade-in-up"
      style={{ marginBottom: '0.75rem', overflow: 'hidden' }}
    >
      {/* Header row */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.875rem',
        padding: '1rem 1.25rem',
        cursor: 'pointer',
      }} onClick={() => setExpanded(!expanded)}>
        {/* Prompt */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: '0.9rem',
            fontWeight: 600,
            color: 'var(--text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            marginBottom: '0.375rem',
          }}>
            "{run.prompt}"
          </div>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
            {/* Model chips */}
            {run.results.map((result) => {
              const model = getModelById(result.modelId);
              return (
                <span
                  key={result.modelId}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    padding: '0.2rem 0.5rem',
                    borderRadius: '999px',
                    background: model?.bgColor ?? 'var(--bg-hover)',
                    color: model?.color ?? 'var(--text-secondary)',
                    border: `1px solid ${model?.color ?? 'var(--border-color)'}33`,
                  }}
                >
                  {model?.logo} {result.modelName}
                </span>
              );
            })}
          </div>
        </div>

        {/* Right side info */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          flexShrink: 0,
        }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              justifyContent: 'flex-end',
            }}>
              <Clock size={11} />
              {timeAgo(run.timestamp)}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
              {run.results.length} models • {run.runDuration.toFixed(1)}s
            </div>
          </div>

          <button
            id={`export-run-${run.id}`}
            onClick={(e) => { e.stopPropagation(); exportSingleRun(run); }}
            className="btn btn-icon btn-secondary"
            title="Export as CSV"
            style={{ color: 'var(--text-secondary)' }}
          >
            <Download size={14} />
          </button>

          <button
            id={`delete-run-${run.id}`}
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="btn btn-icon"
            title="Delete run"
            style={{
              color: 'var(--accent-danger)',
              background: 'rgba(239,68,68,0.08)',
              border: '1px solid rgba(239,68,68,0.2)',
            }}
          >
            <Trash2 size={14} />
          </button>

          {expanded
            ? <ChevronUp size={16} style={{ color: 'var(--text-muted)' }} />
            : <ChevronDown size={16} style={{ color: 'var(--text-muted)' }} />
          }
        </div>
      </div>

      {/* Expanded results */}
      {expanded && (
        <div style={{
          borderTop: '1px solid var(--border-color)',
          padding: '1rem 1.25rem',
          background: 'var(--bg-hover)',
        }}>
          <ResultsTable run={run} compact />
        </div>
      )}
    </div>
  );
}

export function BenchmarkHistory() {
  const { runs, deleteRun } = useBenchmark();
  const [search, setSearch] = useState('');
  const [filterModel, setFilterModel] = useState<string>('all');

  const filtered = runs.filter((run) => {
    const matchesSearch = run.prompt.toLowerCase().includes(search.toLowerCase());
    const matchesModel =
      filterModel === 'all' ||
      run.selectedModels.includes(filterModel as never);
    return matchesSearch && matchesModel;
  });

  return (
    <div>
      {/* Toolbar */}
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        marginBottom: '1.25rem',
        flexWrap: 'wrap',
        alignItems: 'center',
      }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: '1', minWidth: '200px' }}>
          <Search
            size={14}
            style={{
              position: 'absolute',
              left: '0.75rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
              pointerEvents: 'none',
            }}
          />
          <input
            id="history-search"
            type="text"
            placeholder="Search benchmarks by prompt…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: '2.25rem' }}
          />
        </div>

        {/* Model filter */}
        <select
          id="history-filter-model"
          value={filterModel}
          onChange={(e) => setFilterModel(e.target.value)}
          className="input"
          style={{ width: 'auto', minWidth: '150px' }}
        >
          <option value="all">All models</option>
          <option value="openai">ChatGPT</option>
          <option value="google">Gemini</option>
          <option value="anthropic">Claude</option>
          <option value="meta">Llama</option>
          <option value="mistral">Mistral</option>
        </select>

        {/* Export all */}
        <button
          id="export-all-csv"
          onClick={() => exportToCsv(filtered)}
          disabled={filtered.length === 0}
          className="btn btn-success btn-sm"
          style={{ gap: '0.375rem', whiteSpace: 'nowrap' }}
        >
          <Download size={14} />
          Export All ({filtered.length})
        </button>
      </div>

      {/* Results count */}
      <div style={{
        fontSize: '0.8125rem',
        color: 'var(--text-muted)',
        marginBottom: '0.75rem',
      }}>
        Showing {filtered.length} of {runs.length} benchmarks
      </div>

      {/* History list */}
      {filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            No benchmarks found
          </div>
          <div style={{ fontSize: '0.875rem', marginTop: '0.375rem' }}>
            {runs.length === 0
              ? 'Run your first benchmark to see results here'
              : 'Try adjusting your search or filter'}
          </div>
        </div>
      ) : (
        <div>
          {filtered.map((run) => (
            <HistoryCard
              key={run.id}
              run={run}
              onDelete={() => deleteRun(run.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
