import { Zap, Loader2, AlertCircle } from 'lucide-react';
import { useBenchmark } from '../../context/BenchmarkContext';
import { ModelSelector } from './ModelSelector';

export function BenchmarkRunner() {
  const { prompt, setPrompt, selectedModels, runBenchmark, isRunning } =
    useBenchmark();

  const canRun =
    prompt.trim().length > 0 && selectedModels.length > 0 && !isRunning;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (canRun) runBenchmark();
  };

  const samplePrompts = [
    'Explain quantum computing in simple terms',
    'Write a Python function to calculate Fibonacci numbers',
    'What are the ethical implications of AI in healthcare?',
    'How does blockchain technology work?',
    'Summarize the key principles of machine learning',
  ];

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Prompt area */}
        <div>
          <label htmlFor="benchmark-prompt" className="label">
            Enter Your Prompt
          </label>
          <textarea
            id="benchmark-prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask something you want to benchmark across multiple LLMs..."
            className="input textarea"
            rows={5}
            disabled={isRunning}
            style={{ fontFamily: 'var(--font-sans)' }}
          />
          {/* Quick prompts */}
          <div style={{ marginTop: '0.625rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '0.5rem' }}>
              Quick prompts:
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', marginTop: '0.375rem' }}>
              {samplePrompts.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPrompt(p)}
                  disabled={isRunning}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.75rem' }}
                >
                  {p.length > 35 ? p.slice(0, 35) + '…' : p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Model selector */}
        <ModelSelector />

        {/* Validation warning */}
        {!canRun && !isRunning && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            fontSize: '0.8125rem',
            color: 'var(--accent-warning)',
          }}>
            <AlertCircle size={14} />
            {prompt.trim().length === 0
              ? 'Please enter a prompt to benchmark'
              : 'Please select at least one model'}
          </div>
        )}

        {/* Running state */}
        {isRunning && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            padding: '1rem 1.25rem',
            borderRadius: 'var(--radius-lg)',
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.2)',
          }}>
            <Loader2 size={20} color="var(--accent-primary)" className="animate-spin" />
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Running benchmark across {selectedModels.length} model{selectedModels.length > 1 ? 's' : ''}…
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                Simulating responses and computing metrics
              </div>
            </div>
            {/* Animated dots */}
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
              {selectedModels.map((_, i) => (
                <div
                  key={i}
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: 'var(--accent-primary)',
                    animation: `pulse-ring 1.2s ease-in-out ${i * 0.2}s infinite`,
                    opacity: 0.7,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Submit button */}
        <button
          id="run-benchmark-btn"
          type="submit"
          disabled={!canRun}
          className="btn btn-primary btn-lg"
          style={{ alignSelf: 'flex-start', gap: '0.5rem' }}
        >
          {isRunning ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Running Benchmark…
            </>
          ) : (
            <>
              <Zap size={18} />
              Run Benchmark
            </>
          )}
        </button>
      </div>
    </form>
  );
}
