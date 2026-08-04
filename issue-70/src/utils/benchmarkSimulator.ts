import type { BenchmarkResult, BenchmarkRun, LLMProvider } from '../types';
import { LLM_MODELS } from '../data/models';

// Simulated response templates per model characteristic
const MODEL_RESPONSE_TEMPLATES: Record<LLMProvider, string[]> = {
  openai: [
    "I'll provide a comprehensive and structured analysis of this topic...",
    "This is an excellent question. Let me break this down step by step...",
    "From a technical perspective, here's what you need to know...",
  ],
  google: [
    "Based on the latest information available, here's a detailed overview...",
    "Let me address this with precision and clarity...",
    "Here's a well-researched perspective on this topic...",
  ],
  anthropic: [
    "I want to give you a thoughtful, nuanced answer here...",
    "Let me carefully consider multiple angles before answering...",
    "This is a topic I find genuinely interesting. Here's my take...",
  ],
  meta: [
    "Here's an open-source perspective on this question...",
    "Let me give you a direct and efficient answer...",
    "Based on my training, I can offer the following insights...",
  ],
  mistral: [
    "Voilà, let me offer a precise and efficient response...",
    "I'll approach this with clarity and technical precision...",
    "Here's a concise yet comprehensive answer to your query...",
  ],
};

// Baseline metrics per model (will be randomized slightly)
const MODEL_BASELINES: Record<LLMProvider, Partial<BenchmarkResult['metrics']>> = {
  openai:    { responseQuality: 9.2, responseTime: 1.9, tokenUsage: 380, estimatedCost: 0.96, completeness: 94, coherence: 93, creativity: 88, accuracy: 95 },
  google:    { responseQuality: 8.9, responseTime: 1.5, tokenUsage: 340, estimatedCost: 0.71, completeness: 91, coherence: 92, creativity: 86, accuracy: 92 },
  anthropic: { responseQuality: 9.3, responseTime: 2.2, tokenUsage: 415, estimatedCost: 1.04, completeness: 95, coherence: 97, creativity: 90, accuracy: 93 },
  meta:      { responseQuality: 8.3, responseTime: 3.3, tokenUsage: 360, estimatedCost: 0.30, completeness: 85, coherence: 84, creativity: 79, accuracy: 87 },
  mistral:   { responseQuality: 8.6, responseTime: 2.0, tokenUsage: 350, estimatedCost: 0.44, completeness: 88, coherence: 89, creativity: 82, accuracy: 89 },
};

function jitter(value: number, pct: number): number {
  const delta = value * pct;
  return parseFloat((value + (Math.random() * 2 - 1) * delta).toFixed(3));
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function calcOverallScore(metrics: Omit<BenchmarkResult['metrics'], 'overallScore'>): number {
  const qualityWeight = 0.35;
  const timeWeight = 0.20;
  const costWeight = 0.15;
  const completenessWeight = 0.10;
  const coherenceWeight = 0.10;
  const accuracyWeight = 0.10;

  // Normalize time: lower = better (assume max 5s = 0, 0.5s = 10)
  const normalizedTime = clamp(10 - ((metrics.responseTime - 0.5) / 4.5) * 10, 0, 10);
  // Normalize cost: lower = better (assume max $0.02 = 0, $0 = 10)
  const normalizedCost = clamp(10 - (metrics.estimatedCost / 1.68) * 10, 0, 10);

  const score =
    metrics.responseQuality * qualityWeight +
    normalizedTime * timeWeight +
    normalizedCost * costWeight +
    (metrics.completeness / 10) * completenessWeight +
    (metrics.coherence / 10) * coherenceWeight +
    (metrics.accuracy / 10) * accuracyWeight;

  return parseFloat(clamp(score, 0, 10).toFixed(2));
}

export function simulateBenchmark(
  prompt: string,
  selectedModels: LLMProvider[]
): BenchmarkRun {
  const runId = `bench-${Date.now()}`;
  const timestamp = new Date().toISOString();

  const results: BenchmarkResult[] = selectedModels.map((modelId) => {
    const model = LLM_MODELS.find((m) => m.id === modelId)!;
    const base = MODEL_BASELINES[modelId];
    const templates = MODEL_RESPONSE_TEMPLATES[modelId];

    // Jitter metrics with ±15% noise
    const responseQuality = clamp(jitter(base.responseQuality!, 0.15), 5, 10);
    const responseTime = clamp(jitter(base.responseTime!, 0.2), 0.5, 8);
    const tokenUsage = Math.round(jitter(base.tokenUsage!, 0.2));
    const estimatedCost = clamp(jitter(base.estimatedCost!, 0.2), 0.08, 4.20);
    const completeness = clamp(Math.round(jitter(base.completeness!, 0.1)), 60, 100);
    const coherence = clamp(Math.round(jitter(base.coherence!, 0.1)), 60, 100);
    const creativity = clamp(Math.round(jitter(base.creativity!, 0.15)), 55, 100);
    const accuracy = clamp(Math.round(jitter(base.accuracy!, 0.1)), 60, 100);

    const partialMetrics = {
      responseQuality: parseFloat(responseQuality.toFixed(1)),
      responseTime: parseFloat(responseTime.toFixed(2)),
      tokenUsage,
      estimatedCost: parseFloat(estimatedCost.toFixed(2)),
      completeness,
      coherence,
      creativity,
      accuracy,
    };

    const overallScore = calcOverallScore(partialMetrics);

    const responseTemplate = templates[Math.floor(Math.random() * templates.length)];
    const response = `${responseTemplate}\n\n[Simulated response for: "${prompt.slice(0, 60)}${prompt.length > 60 ? '...' : ''}"]\n\nThis response was generated by ${model.name} (${model.version}) and contains approximately ${tokenUsage} tokens.`;

    return {
      modelId,
      modelName: model.name,
      modelVersion: model.version,
      metrics: { ...partialMetrics, overallScore },
      response,
      timestamp,
    };
  });

  const runDuration = Math.max(...results.map((r) => r.metrics.responseTime)) + 0.5;

  return {
    id: runId,
    prompt,
    selectedModels,
    results,
    timestamp,
    runDuration: parseFloat(runDuration.toFixed(2)),
  };
}
