import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from 'react';
import type { BenchmarkRun, LLMProvider } from '../types';
import { BENCHMARK_HISTORY } from '../data/benchmarkHistory';
import { simulateBenchmark } from '../utils/benchmarkSimulator';

interface BenchmarkContextValue {
  runs: BenchmarkRun[];
  currentRun: BenchmarkRun | null;
  isRunning: boolean;
  selectedModels: LLMProvider[];
  prompt: string;
  setPrompt: (p: string) => void;
  setSelectedModels: (models: LLMProvider[]) => void;
  runBenchmark: () => Promise<void>;
  clearCurrentRun: () => void;
  deleteRun: (id: string) => void;
}

const BenchmarkContext = createContext<BenchmarkContextValue | undefined>(
  undefined
);

export function BenchmarkProvider({ children }: { children: ReactNode }) {
  const [runs, setRuns] = useState<BenchmarkRun[]>(BENCHMARK_HISTORY);
  const [currentRun, setCurrentRun] = useState<BenchmarkRun | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedModels, setSelectedModels] = useState<LLMProvider[]>([
    'openai',
    'google',
    'anthropic',
  ]);
  const [prompt, setPrompt] = useState('');

  const runBenchmark = useCallback(async () => {
    if (!prompt.trim() || selectedModels.length === 0) return;
    setIsRunning(true);
    setCurrentRun(null);

    // Simulate async latency (1-4 seconds based on model count)
    const delay = 1000 + selectedModels.length * 500 + Math.random() * 1500;
    await new Promise((res) => setTimeout(res, delay));

    const result = simulateBenchmark(prompt.trim(), selectedModels);
    setCurrentRun(result);
    setRuns((prev) => [result, ...prev]);
    setIsRunning(false);
  }, [prompt, selectedModels]);

  const clearCurrentRun = useCallback(() => setCurrentRun(null), []);

  const deleteRun = useCallback(
    (id: string) => setRuns((prev) => prev.filter((r) => r.id !== id)),
    []
  );

  return (
    <BenchmarkContext.Provider
      value={{
        runs,
        currentRun,
        isRunning,
        selectedModels,
        prompt,
        setPrompt,
        setSelectedModels,
        runBenchmark,
        clearCurrentRun,
        deleteRun,
      }}
    >
      {children}
    </BenchmarkContext.Provider>
  );
}

export function useBenchmark(): BenchmarkContextValue {
  const ctx = useContext(BenchmarkContext);
  if (!ctx)
    throw new Error('useBenchmark must be used within BenchmarkProvider');
  return ctx;
}
