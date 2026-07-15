import { useState } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Download, Trophy } from 'lucide-react';
import type { BenchmarkResult, SortField, SortDirection } from '../../types';
import { getModelById } from '../../data/models';
import { exportSingleRun } from '../../utils/csvExport';
import type { BenchmarkRun } from '../../types';

interface ScoreBarProps {
  value: number;
  max?: number;
  color: string;
}

function ScoreBar({ value, max = 10, color }: ScoreBarProps) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="score-bar">
      <span style={{
        fontSize: '0.8125rem',
        fontWeight: 600,
        color: 'var(--text-primary)',
        minWidth: '2.5rem',
        textAlign: 'right',
      }}>
        {max === 100 ? `${value}%` : value.toFixed(1)}
      </span>
      <div className="score-track" style={{ flex: 1 }}>
        <div
          className="score-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

function getScoreColor(score: number, max = 10): string {
  const pct = score / max;
  if (pct >= 0.85) return 'var(--accent-success)';
  if (pct >= 0.70) return 'var(--accent-info)';
  if (pct >= 0.55) return 'var(--accent-warning)';
  return 'var(--accent-danger)';
}

interface SortIconProps {
  field: SortField;
  activeField: SortField | null;
  direction: SortDirection;
}

function SortIcon({ field, activeField, direction }: SortIconProps) {
  if (field !== activeField) return <ArrowUpDown size={12} style={{ opacity: 0.4 }} />;
  return direction === 'asc'
    ? <ArrowUp size={12} />
    : <ArrowDown size={12} />;
}

interface ResultsTableProps {
  run: BenchmarkRun;
  compact?: boolean;
}

export function ResultsTable({ run }: ResultsTableProps) {
  const [sortField, setSortField] = useState<SortField | null>('overallScore');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sorted = [...run.results].sort((a, b) => {
    if (!sortField) return 0;
    const av = a.metrics[sortField];
    const bv = b.metrics[sortField];
    const dir = sortDirection === 'asc' ? 1 : -1;
    return (av - bv) * dir;
  });

  const bestScore = Math.max(...run.results.map((r) => r.metrics.overallScore));
  const isWinner = (r: BenchmarkResult) => r.metrics.overallScore === bestScore;

  const SORT_COLS: { field: SortField; label: string }[] = [
    { field: 'responseQuality', label: 'Quality' },
    { field: 'responseTime',    label: 'Latency (s)' },
    { field: 'tokenUsage',      label: 'Tokens' },
    { field: 'estimatedCost',   label: 'Cost (₹)' },
    { field: 'overallScore',    label: 'Overall' },
  ];

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '0.875rem',
      }}>
        <div>
          <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, margin: 0, color: 'var(--text-primary)' }}>
            Benchmark Results
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.15rem 0 0' }}>
            Click column headers to sort • {run.results.length} models compared
          </p>
        </div>
        <button
          id={`export-csv-${run.id}`}
          onClick={() => exportSingleRun(run)}
          className="btn btn-secondary btn-sm"
          style={{ gap: '0.375rem' }}
        >
          <Download size={13} />
          Export CSV
        </button>
      </div>

      <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '180px' }}>Model</th>
              {SORT_COLS.map(({ field, label }) => (
                <th
                  key={field}
                  onClick={() => handleSort(field)}
                  style={{ textAlign: 'right' }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', justifyContent: 'flex-end' }}>
                    {label}
                    <SortIcon field={field} activeField={sortField} direction={sortDirection} />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((result, idx) => {
              const model = getModelById(result.modelId);
              const winner = isWinner(result);
              return (
                <tr
                  key={result.modelId}
                  className="animate-fade-in-up"
                  style={{
                    animationDelay: `${idx * 50}ms`,
                    background: winner
                      ? 'rgba(16, 185, 129, 0.04)'
                      : undefined,
                  }}
                >
                  {/* Model name */}
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                      <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        background: model?.bgColor ?? 'var(--bg-hover)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1rem',
                        flexShrink: 0,
                        border: `1px solid ${model?.color ?? 'var(--border-color)'}33`,
                      }}>
                        {model?.logo ?? '?'}
                      </div>
                      <div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.3rem',
                          fontWeight: 600,
                          fontSize: '0.875rem',
                          color: model?.color ?? 'var(--text-primary)',
                        }}>
                          {result.modelName}
                          {winner && (
                            <span title="Best overall score" style={{ display: 'inline-flex' }}>
                              <Trophy size={13} color="var(--accent-warning)" />
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {result.modelVersion}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Quality */}
                  <td style={{ minWidth: '120px' }}>
                    <ScoreBar
                      value={result.metrics.responseQuality}
                      max={10}
                      color={getScoreColor(result.metrics.responseQuality)}
                    />
                  </td>

                  {/* Latency */}
                  <td style={{ textAlign: 'right' }}>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.875rem',
                      color: result.metrics.responseTime <= 2
                        ? 'var(--accent-success)'
                        : result.metrics.responseTime <= 3.5
                          ? 'var(--accent-warning)'
                          : 'var(--accent-danger)',
                      fontWeight: 600,
                    }}>
                      {result.metrics.responseTime.toFixed(2)}s
                    </span>
                  </td>

                  {/* Tokens */}
                  <td style={{ textAlign: 'right' }}>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.875rem',
                      color: 'var(--text-primary)',
                      fontWeight: 600,
                    }}>
                      {result.metrics.tokenUsage.toLocaleString()}
                    </span>
                  </td>

                  {/* Cost */}
                  <td style={{ textAlign: 'right' }}>
                    <span style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.875rem',
                      color: result.metrics.estimatedCost < 0.59
                        ? 'var(--accent-success)'
                        : result.metrics.estimatedCost < 1.01
                          ? 'var(--accent-warning)'
                          : 'var(--accent-danger)',
                      fontWeight: 600,
                    }}>
                      ₹{result.metrics.estimatedCost.toFixed(2)}
                    </span>
                  </td>

                  {/* Overall score */}
                  <td style={{ minWidth: '130px' }}>
                    <ScoreBar
                      value={result.metrics.overallScore}
                      max={10}
                      color={getScoreColor(result.metrics.overallScore)}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
