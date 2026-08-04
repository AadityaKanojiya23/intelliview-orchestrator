import type { BenchmarkRun } from '../types';
import { getModelById } from '../data/models';

export function exportToCsv(runs: BenchmarkRun[]): void {
  const headers = [
    'Benchmark ID',
    'Prompt',
    'Timestamp',
    'Model',
    'Version',
    'Response Quality',
    'Response Time (s)',
    'Token Usage',
    'Estimated Cost (₹)',
    'Overall Score',
    'Completeness',
    'Coherence',
    'Creativity',
    'Accuracy',
  ];

  const rows: string[][] = [];

  runs.forEach((run) => {
    run.results.forEach((result) => {
      rows.push([
        run.id,
        `"${run.prompt.replace(/"/g, '""')}"`,
        new Date(run.timestamp).toLocaleString(),
        result.modelName,
        result.modelVersion,
        result.metrics.responseQuality.toString(),
        result.metrics.responseTime.toString(),
        result.metrics.tokenUsage.toString(),
        result.metrics.estimatedCost.toFixed(2),
        result.metrics.overallScore.toString(),
        result.metrics.completeness.toString(),
        result.metrics.coherence.toString(),
        result.metrics.creativity.toString(),
        result.metrics.accuracy.toString(),
      ]);
    });
  });

  const csvContent =
    [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `llm-benchmarks-${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportSingleRun(run: BenchmarkRun): void {
  exportToCsv([run]);
}

export function getDashboardStats(runs: BenchmarkRun[]) {
  if (runs.length === 0) {
    return {
      totalBenchmarks: 0,
      fastestModel: 'N/A',
      highestQualityModel: 'N/A',
      lowestCostModel: 'N/A',
      averageLatency: 0,
      totalTokensUsed: 0,
    };
  }

  const allResults = runs.flatMap((r) => r.results);

  // Fastest: lowest avg responseTime
  const modelTimeMap: Record<string, number[]> = {};
  const modelQualityMap: Record<string, number[]> = {};
  const modelCostMap: Record<string, number[]> = {};

  allResults.forEach((result) => {
    const key = result.modelId;
    if (!modelTimeMap[key]) modelTimeMap[key] = [];
    if (!modelQualityMap[key]) modelQualityMap[key] = [];
    if (!modelCostMap[key]) modelCostMap[key] = [];
    modelTimeMap[key].push(result.metrics.responseTime);
    modelQualityMap[key].push(result.metrics.responseQuality);
    modelCostMap[key].push(result.metrics.estimatedCost);
  });

  const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;

  const fastestModelId = Object.entries(modelTimeMap).sort(
    ([, a], [, b]) => avg(a) - avg(b)
  )[0]?.[0];

  const highestQualityModelId = Object.entries(modelQualityMap).sort(
    ([, a], [, b]) => avg(b) - avg(a)
  )[0]?.[0];

  const lowestCostModelId = Object.entries(modelCostMap).sort(
    ([, a], [, b]) => avg(a) - avg(b)
  )[0]?.[0];

  const totalTokensUsed = allResults.reduce(
    (sum, r) => sum + r.metrics.tokenUsage,
    0
  );

  const averageLatency =
    allResults.reduce((sum, r) => sum + r.metrics.responseTime, 0) /
    allResults.length;

  const getModelName = (id: string) => getModelById(id)?.name ?? id;

  return {
    totalBenchmarks: runs.length,
    fastestModel: getModelName(fastestModelId),
    highestQualityModel: getModelName(highestQualityModelId),
    lowestCostModel: getModelName(lowestCostModelId),
    averageLatency: parseFloat(averageLatency.toFixed(2)),
    totalTokensUsed,
  };
}
