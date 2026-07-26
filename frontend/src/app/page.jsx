"use client";
import { useEffect, useState, useMemo } from "react";
import useSWR from "swr";
import { Activity, AlertTriangle, CheckCircle2, Users, Zap, Shield, TrendingUp, Clock } from "lucide-react";
import Card from "@/components/Card";
import Stat from "@/components/Stat";
import { StatusBadge } from "@/components/Badge";
import { Skeleton, ErrorState, EmptyState } from "@/components/States";
import Sparkline from "@/components/Sparkline";
import { formatPercent, formatRelative } from "@/lib/utils";
import { Table, Thead, Tbody, Tr, Th, Td } from "@/components/ui";
import React, { useState } from "react";
import SortableHeader from "../components/SortableHeader";

export default function Page() {
  const [workers, setWorkers] = useState([
    { id: 1, name: "Alice", role: "Engineer", salary: 60000 },
    { id: 2, name: "Bob", role: "Designer", salary: 50000 },
    { id: 3, name: "Charlie", role: "Manager", salary: 80000 },
  ]);

  const [sortConfig, setSortConfig] = useState({
    key: null,
    direction: "asc",
  });

  const handleSort = (key) => {
    let direction = "asc";

    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }

    const sortedData = [...workers].sort((a, b) => {
      if (a[key] < b[key]) return direction === "asc" ? -1 : 1;
      if (a[key] > b[key]) return direction === "asc" ? 1 : -1;
      return 0;
    });

    setWorkers(sortedData);
    setSortConfig({ key, direction });
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Workers Table</h2>

      <table border="1" cellPadding="10">
        <thead>
          <tr>
            <SortableHeader
              label="Name"
              sortKey="name"
              sortConfig={sortConfig}
              onSort={handleSort}
            />
            <SortableHeader
              label="Role"
              sortKey="role"
              sortConfig={sortConfig}
              onSort={handleSort}
            />
            <SortableHeader
              label="Salary"
              sortKey="salary"
              sortConfig={sortConfig}
              onSort={handleSort}
            />
          </tr>
        </thead>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card title="Completed sessions" description={`Last ${MAX_SAMPLES} samples`}>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-semibold text-zinc-50">{stats.data?.completed_sessions ?? "—"}</div>
            <Sparkline data={completedHist} color="#10b981" width={140} height={40} />
          </div>
        </Card>
        <Card title="Failed sessions" description={`Last ${MAX_SAMPLES} samples`}>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-semibold text-zinc-50">{stats.data?.failed_sessions ?? "—"}</div>
            <Sparkline data={failedHist} color="#ef4444" width={140} height={40} />
          </div>
        </Card>
        <Card title="Average risk" description={`Last ${MAX_SAMPLES} samples`}>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-semibold text-zinc-50">
              {stats.data?.risk_score_stats.average_risk_score.toFixed(3) ?? "—"}
            </div>
            <Sparkline data={riskHist} color="#f59e0b" width={140} height={40} />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Component health" description="Live status of each dependency.">
          {health.error ? (
            <ErrorState error={health.error} onRetry={() => health.mutate()} />
          ) : !health.data ? (
            <Skeleton className="h-32 w-full" />
          ) : (
            <ul className="space-y-2 text-sm">
              {Object.entries(health.data.components).map(([k, v]) => (
                <li
                  key={k}
                  className="flex items-center justify-between rounded-md border border-border bg-bg-card px-3 py-2 hover:border-accent/30 transition-colors"
                >
                  <span className="capitalize text-zinc-300">{k}</span>
                  <StatusBadge status={v?.status || "unknown"} />
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Active sessions" description="In-flight interviews across the cluster.">
          {active.error ? (
            <ErrorState error={active.error} onRetry={() => active.mutate()} />
          ) : !active.data ? (
            <Skeleton className="h-32 w-full" />
          ) : active.data.sessions.length === 0 ? (
            <EmptyState title="No active sessions" description="Start a new interview to see it here." />
          ) : (
            <ul className="space-y-2 text-sm">
              {active.data.sessions.slice(0, 6).map((s) => (
                <li
                  key={s.session_id}
                  className="flex items-center justify-between rounded-md border border-border bg-bg-card px-3 py-2 hover:border-accent/30 transition-colors"
                >
                  <div>
                    <div className="font-mono text-xs text-zinc-300">{s.session_id}</div>
                    <div className="text-xs text-muted">{s.candidate_id}</div>
                  </div>
                  <StatusBadge status={s.status} />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card title="Workers" description="Currently registered worker nodes.">
        {workers.error ? (
          <ErrorState error={workers.error} onRetry={() => workers.mutate()} />
        ) : !workers.data ? (
          <Skeleton className="h-24 w-full" />
        ) : workers.data.workers.length === 0 ? (
          <EmptyState title="No workers registered" description="Workers self-register via the worker_agent on startup." />
        ) : (
          <Table>
            <Thead>
              <Tr>
                <Th>Worker</Th>
                <Th>Status</Th>
                <Th>Load</Th>
                <Th>Last heartbeat</Th>
              </Tr>
            </Thead>
            <Tbody>
              {workers.data.workers.map((w) => (
                <Tr key={w.worker_id}>
                  <Td className="font-mono text-xs text-zinc-200">{w.worker_id}</Td>
                  <Td><StatusBadge status={w.health_status} /></Td>
                  <Td>{w.active_tasks}/{w.capacity}</Td>
                  <Td className="text-muted">{formatRelative(w.last_heartbeat)}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Card>
        <tbody>
          {workers.map((worker) => (
            <tr key={worker.id}>
              <td>{worker.name}</td>
              <td>{worker.role}</td>
              <td>{worker.salary}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}