export type LLMProvider =
  | 'openai'
  | 'google'
  | 'anthropic'
  | 'meta'
  | 'mistral';

export interface LLMModel {
  id: LLMProvider;
  name: string;
  version: string;
  logo: string;
  color: string;
  bgColor: string;
  description: string;
}

export interface BenchmarkMetrics {
  responseQuality: number;      // Score out of 10
  responseTime: number;         // Latency in seconds
  tokenUsage: number;           // Total tokens used
  estimatedCost: number;        // Cost in INR (₹)
  overallScore: number;         // Weighted overall score
  completeness: number;         // 0-100
  coherence: number;            // 0-100
  creativity: number;           // 0-100
  accuracy: number;             // 0-100
}

export interface BenchmarkResult {
  modelId: LLMProvider;
  modelName: string;
  modelVersion: string;
  metrics: BenchmarkMetrics;
  response: string;
  timestamp: string;
}

export interface BenchmarkRun {
  id: string;
  prompt: string;
  selectedModels: LLMProvider[];
  results: BenchmarkResult[];
  timestamp: string;
  runDuration: number; // total seconds to run
}

export interface DashboardStats {
  totalBenchmarks: number;
  fastestModel: string;
  highestQualityModel: string;
  lowestCostModel: string;
  averageLatency: number;
  totalTokensUsed: number;
}

export type Theme = 'light' | 'dark';

export type SortField = keyof BenchmarkMetrics;
export type SortDirection = 'asc' | 'desc';
