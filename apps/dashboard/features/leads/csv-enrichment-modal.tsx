"use client";

import { useMutation } from "@tanstack/react-query";
import { Download, FileSpreadsheet, Loader2, Upload, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

type JobStatus = {
  job_id: string;
  status: string;
  total: number;
  processed: number;
  summary: Record<string, number | string> | null;
  error: string | null;
  current_company: string | null;
  elapsed_seconds: number | null;
};

type Props = {
  open: boolean;
  onClose: () => void;
};

const SAMPLE_HEADERS =
  "founder_name,company_name,job_title,location,industry,company_size";

export function CsvEnrichmentModal({ open, onClose }: Props) {
  const [fileName, setFileName] = useState<string>("");
  const [csvText, setCsvText] = useState<string>("");
  const [rowHint, setRowHint] = useState<number | null>(null);
  const [limit, setLimit] = useState<number>(50);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const clearPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const reset = useCallback(() => {
    clearPoll();
    setFileName("");
    setCsvText("");
    setRowHint(null);
    setJobId(null);
    setStatus(null);
    setLocalError(null);
    if (fileRef.current) fileRef.current.value = "";
  }, []);

  useEffect(() => {
    if (!open) {
      clearPoll();
    }
    return () => clearPoll();
  }, [open]);

  const onFile = async (file: File | null) => {
    setLocalError(null);
    setJobId(null);
    setStatus(null);
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setLocalError("Please upload a .csv file.");
      return;
    }
    const text = await file.text();
    const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
    setFileName(file.name);
    setCsvText(text);
    setRowHint(Math.max(0, lines.length - 1));
  };

  const startMutation = useMutation({
    mutationFn: () =>
      beaconApi.enrichmentCsvStart({
        csv_data: csvText,
        limit: Math.min(Math.max(1, limit), 100),
      }),
    onSuccess: (res) => {
      setJobId(res.job_id);
      setStatus({
        job_id: res.job_id,
        status: res.status,
        total: res.total,
        processed: 0,
        summary: null,
        error: null,
        current_company: null,
        elapsed_seconds: 0,
      });
      clearPoll();
      pollRef.current = setInterval(async () => {
        try {
          const s = await beaconApi.enrichmentCsvStatus(res.job_id);
          setStatus(s);
          if (s.status === "completed" || s.status === "failed") {
            clearPoll();
          }
        } catch (err) {
          setLocalError(err instanceof Error ? err.message : "Status poll failed");
          clearPoll();
        }
      }, 2500);
    },
    onError: (err) => {
      setLocalError(err instanceof Error ? err.message : "Failed to start enrichment");
    },
  });

  if (!open) return null;

  const progress =
    status && status.total > 0
      ? Math.round((status.processed / status.total) * 100)
      : 0;
  const done = status?.status === "completed";
  const failed = status?.status === "failed";

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div>
            <h3 className="font-semibold text-lg">CSV Lead Enrichment</h3>
            <p className="text-sm text-muted-foreground">
              Upload founder + company rows → domain crawl → public profiles → download CSV
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              reset();
              onClose();
            }}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4 px-5 py-4">
          <div
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 transition",
              csvText ? "border-emerald-400 bg-emerald-50/50" : "border-muted-foreground/30 hover:border-muted-foreground/50",
            )}
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              void onFile(e.dataTransfer.files?.[0] || null);
            }}
          >
            <FileSpreadsheet className="mb-2 h-8 w-8 text-muted-foreground" />
            {fileName ? (
              <p className="text-sm font-medium">
                {fileName}
                {rowHint != null ? ` · ~${rowHint} rows` : ""}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">Drop CSV here or click to browse</p>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => void onFile(e.target.files?.[0] || null)}
            />
          </div>

          <div className="rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
            <p className="mb-1 font-medium text-foreground">Expected columns (flexible names OK)</p>
            <code className="break-all">{SAMPLE_HEADERS}</code>
            <p className="mt-2">
              Aliases accepted: Name / Founder, Company, Title / Role, Location, Industry
            </p>
          </div>

          <div className="flex items-center gap-3">
            <label className="text-sm text-muted-foreground" htmlFor="enrich-limit">
              Max rows
            </label>
            <input
              id="enrich-limit"
              type="number"
              min={1}
              max={100}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value) || 50)}
              className="w-24 rounded-md border px-2 py-1.5 text-sm"
              disabled={Boolean(jobId) && !done && !failed}
            />
          </div>

          {localError && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{localError}</p>
          )}

          {status && (
            <div className="space-y-2 rounded-lg border p-3">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium capitalize">{status.status}</span>
                <span className="text-muted-foreground">
                  {status.processed}/{status.total}
                  {status.elapsed_seconds != null ? ` · ${status.elapsed_seconds}s` : ""}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className={cn(
                    "h-full transition-all",
                    failed ? "bg-red-500" : done ? "bg-emerald-500" : "bg-violet-500",
                  )}
                  style={{ width: `${Math.min(100, progress)}%` }}
                />
              </div>
              {status.current_company && status.status === "running" && (
                <p className="truncate text-xs text-muted-foreground">
                  Enriching: {status.current_company}
                </p>
              )}
              {status.error && (
                <p className="text-sm text-red-600">{status.error}</p>
              )}
              {done && status.summary && (
                <p className="text-xs text-muted-foreground">
                  Domains {String(status.summary.domain_found)} · Emails{" "}
                  {String(status.summary.with_email)} · Phones{" "}
                  {String(status.summary.with_phone)} · LinkedIn co{" "}
                  {String(status.summary.linkedin_company)}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 border-t px-5 py-4">
          <Button
            variant="outline"
            onClick={() => {
              reset();
              onClose();
            }}
          >
            Close
          </Button>
          {!done && (
            <Button
              onClick={() => startMutation.mutate()}
              disabled={!csvText || startMutation.isPending || (Boolean(jobId) && !failed)}
              className="bg-violet-600 hover:bg-violet-700"
            >
              {startMutation.isPending || (jobId && !failed && !done) ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Enriching…
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Start enrichment
                </>
              )}
            </Button>
          )}
          {done && jobId && (
            <Button
              className="bg-emerald-600 hover:bg-emerald-700"
              onClick={() => {
                const url = beaconApi.enrichmentCsvDownloadUrl(jobId);
                const a = document.createElement("a");
                a.href = url;
                a.download = `enriched_leads_${jobId.slice(0, 8)}.csv`;
                a.click();
              }}
            >
              <Download className="mr-2 h-4 w-4" />
              Download enriched CSV
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
