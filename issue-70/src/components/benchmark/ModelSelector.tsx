import { Check } from 'lucide-react';
import { LLM_MODELS } from '../../data/models';
import { useBenchmark } from '../../context/BenchmarkContext';
import type { LLMProvider } from '../../types';

export function ModelSelector() {
  const { selectedModels, setSelectedModels, isRunning } = useBenchmark();

  const toggleModel = (id: LLMProvider) => {
    if (isRunning) return;
    setSelectedModels(
      selectedModels.includes(id)
        ? selectedModels.filter((m) => m !== id)
        : [...selectedModels, id]
    );
  };

  const selectAll = () => {
    if (isRunning) return;
    setSelectedModels(LLM_MODELS.map((m) => m.id));
  };

  const selectNone = () => {
    if (isRunning) return;
    setSelectedModels([]);
  };

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '0.75rem',
      }}>
        <label className="label" style={{ margin: 0 }}>
          Select Models to Compare
          <span className="badge badge-primary" style={{ marginLeft: '0.5rem' }}>
            {selectedModels.length} selected
          </span>
        </label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            id="select-all-models"
            onClick={selectAll}
            disabled={isRunning}
            className="btn btn-secondary btn-sm"
          >
            All
          </button>
          <button
            id="select-no-models"
            onClick={selectNone}
            disabled={isRunning}
            className="btn btn-secondary btn-sm"
          >
            None
          </button>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
        gap: '0.625rem',
      }}>
        {LLM_MODELS.map((model) => {
          const isSelected = selectedModels.includes(model.id);
          return (
            <button
              key={model.id}
              id={`model-select-${model.id}`}
              onClick={() => toggleModel(model.id)}
              disabled={isRunning}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.625rem',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-lg)',
                border: `2px solid ${isSelected ? model.color : 'var(--border-color)'}`,
                background: isSelected ? model.bgColor : 'var(--bg-secondary)',
                cursor: isRunning ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                opacity: isRunning ? 0.6 : 1,
                textAlign: 'left',
                width: '100%',
              }}
              aria-pressed={isSelected}
            >
              {/* Checkbox indicator */}
              <div style={{
                width: '20px',
                height: '20px',
                borderRadius: '6px',
                border: `2px solid ${isSelected ? model.color : 'var(--border-color)'}`,
                background: isSelected ? model.color : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 0.15s ease',
              }}>
                {isSelected && <Check size={12} color="#fff" strokeWidth={3} />}
              </div>

              {/* Model info */}
              <div style={{ minWidth: 0 }}>
                <div style={{
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: isSelected ? model.color : 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  transition: 'color 0.15s ease',
                }}>
                  <span>{model.logo}</span>
                  <span>{model.name}</span>
                </div>
                <div style={{
                  fontSize: '0.6875rem',
                  color: 'var(--text-muted)',
                  marginTop: '0.1rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {model.version}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
