"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { JobStatusResponse } from "@/types";

export function useJobPolling(jobId: string | null, enabled: boolean) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);

  useEffect(() => {
    if (!jobId || !enabled) return;

    let cancelled = false;
    const tick = async () => {
      try {
        const next = await api.getJobStatus(jobId);
        if (!cancelled) setJob(next);
      } catch {
        // Keep last known job state on transient poll errors.
      }
    };

    tick();
    const interval = setInterval(tick, 1500);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [jobId, enabled]);

  const terminal =
    job?.status === "completed" ||
    job?.status === "completed_with_limitations" ||
    job?.status === "failed" ||
    job?.status === "cancelled";

  return { job, stage: job?.stage ?? null, status: job?.status ?? null, terminal };
}
