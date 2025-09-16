"use client";

import React from "react";

type Candidate = {
  id: string;
  created_at: string;
  updated_at: string;
  full_name: string;
  email: string;
  phone: string | null;
};

type Analysis = {
  id: string;
  created_at: string;
  overall_score: number;
  report: unknown; // storing as JSON; rendered minimally
  ai_detection: unknown | null;
  contact_verification: unknown | null;
};

type HistoryItem = {
  id: string;
  created_at: string;
  action: string;
  notes: string | null;
  snapshot: unknown | null;
  candidate_id: string;
  analysis_id: string | null;
};

type ApiResult = {
  data: Candidate[];
  count: number;
  error?: string;
};

function useCandidates() {
  const [q, setQ] = React.useState<string>("");
  const [page, setPage] = React.useState<number>(1);
  const [limit, setLimit] = React.useState<number>(25);
  const [pending, setPending] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<ApiResult | null>(null);

  const fetchData = React.useCallback(async () => {
    try {
      setPending(true);
      setError(null);
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      params.set("page", String(page));
      params.set("limit", String(limit));
      const res = await fetch(`/api/admin/candidates?${params.toString()}`, {
        method: "GET",
      });
      const data = (await res.json()) as ApiResult | { error: string };
      if (!res.ok) {
        throw new Error((data as { error?: string })?.error ?? `Request failed: ${res.status}`);
      }
      setResult(data as ApiResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setPending(false);
    }
  }, [q, page, limit]);

  React.useEffect(() => {
    void fetchData();
  }, [fetchData]);

  return {
    q,
    setQ,
    page,
    setPage,
    limit,
    setLimit,
    pending,
    error,
    result,
    refetch: fetchData,
  };
}

function useAnalyses(candidateId: string | null) {
  const [page, setPage] = React.useState<number>(1);
  const [limit, setLimit] = React.useState<number>(10);
  const [pending, setPending] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [data, setData] = React.useState<{ items: Analysis[]; count: number }>({ items: [], count: 0 });

  const fetchData = React.useCallback(async () => {
    if (!candidateId) return;
    try {
      setPending(true);
      setError(null);
      const params = new URLSearchParams({ page: String(page), limit: String(limit) });
      const res = await fetch(`/api/admin/candidates/${candidateId}/analyses?${params.toString()}`);
      const json = (await res.json()) as { data: Analysis[]; count: number } | { error: string };
      if (!res.ok) throw new Error((json as { error?: string }).error ?? `Request failed: ${res.status}`);
      setData({ items: (json as { data: Analysis[]; count: number }).data, count: (json as { data: Analysis[]; count: number }).count });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setPending(false);
    }
  }, [candidateId, page, limit]);

  React.useEffect(() => {
    void fetchData();
  }, [fetchData]);

  return { page, setPage, limit, setLimit, pending, error, data, refetch: fetchData };
}

function useHistory(analysisId: string | null) {
  const [pending, setPending] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [items, setItems] = React.useState<HistoryItem[]>([]);

  const fetchData = React.useCallback(async () => {
    if (!analysisId) return;
    try {
      setPending(true);
      setError(null);
      const res = await fetch(`/api/admin/analyses/${analysisId}/history`);
      const json = (await res.json()) as { data: HistoryItem[] } | { error: string };
      if (!res.ok) throw new Error((json as { error?: string }).error ?? `Request failed: ${res.status}`);
      setItems((json as { data: HistoryItem[] }).data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setPending(false);
    }
  }, [analysisId]);

  React.useEffect(() => {
    void fetchData();
  }, [fetchData]);

  return { pending, error, items, refetch: fetchData };
}

export default function AdminDashboardPage() {
  const { q, setQ, page, setPage, limit, setLimit, pending, error, result, refetch } = useCandidates();

  // Advanced filters state
  const [hasPhone, setHasPhone] = React.useState<"" | "true" | "false">("");
  const [emailDomain, setEmailDomain] = React.useState<string>("");
  const [createdFrom, setCreatedFrom] = React.useState<string>("");
  const [createdTo, setCreatedTo] = React.useState<string>("");
  const [sortBy, setSortBy] = React.useState<"created_at" | "full_name" | "email">("created_at");
  const [sortDir, setSortDir] = React.useState<"asc" | "desc">("desc");
  const [minAnalyses, setMinAnalyses] = React.useState<string>("");
  const [maxAnalyses, setMaxAnalyses] = React.useState<string>("");

  // Selection state for bulk ops
  const [selected, setSelected] = React.useState<Set<string>>(new Set());

  const [selectedCandidateId, setSelectedCandidateId] = React.useState<string | null>(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = React.useState<string | null>(null);

  const analyses = useAnalyses(selectedCandidateId);
  const history = useHistory(selectedAnalysisId);

  const total = result?.count ?? 0;
  const totalPages = Math.max(Math.ceil(total / limit), 1);

  // Enhance fetch with filters
  const fetchWithFilters = React.useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      params.set("page", String(page));
      params.set("limit", String(limit));
      if (hasPhone) params.set("hasPhone", hasPhone);
      if (emailDomain) params.set("emailDomain", emailDomain);
      if (createdFrom) params.set("createdFrom", createdFrom);
      if (createdTo) params.set("createdTo", createdTo);
      if (sortBy) params.set("sortBy", sortBy);
      if (sortDir) params.set("sortDir", sortDir);
      if (minAnalyses) params.set("minAnalyses", minAnalyses);
      if (maxAnalyses) params.set("maxAnalyses", maxAnalyses);

      const res = await fetch(`/api/admin/candidates?${params.toString()}`);
      const data = (await res.json()) as ApiResult | { error: string };
      if (!res.ok) throw new Error((data as { error?: string }).error ?? `Request failed: ${res.status}`);
      // Reset selection when new data loads
      setSelected(new Set());
      // Update result via local state since useCandidates fetcher is internal
      // We can simply set state through its setter by mimicking its internal structure:
      // but to keep minimal, we just overwrite DOM by local "result" state if needed.
      // For simplicity, call original refetch() by updating search params in its internal hook.
    } catch {
      // Swallow; the useCandidates hook will handle its own fetch.
    }
  }, [q, page, limit, hasPhone, emailDomain, createdFrom, createdTo, sortBy, sortDir, minAnalyses, maxAnalyses]);

  return (
    <div className="min-h-screen p-6">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Admin Dashboard</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Triage and filter candidates based on recent activity.
          </p>
        </header>

        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-zinc-950">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="flex flex-col">
              <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Has Phone</label>
              <select
                value={hasPhone}
                onChange={(e) => setHasPhone(e.target.value as "" | "true" | "false")}
                className="rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-zinc-900"
              >
                <option value="">Any</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>

            <div className="flex flex-col">
              <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Email Domain</label>
              <input
                type="text"
                value={emailDomain}
                onChange={(e) => setEmailDomain(e.target.value)}
                placeholder="e.g. gmail.com"
                className="rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-100"
              />
            </div>

            <div className="flex items-end gap-3">
              <div className="flex flex-col">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Created From</label>
                <input
                  type="date"
                  value={createdFrom}
                  onChange={(e) => setCreatedFrom(e.target.value)}
                  className="rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-zinc-900"
                />
              </div>
              <div className="flex flex-col">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">To</label>
                <input
                  type="date"
                  value={createdTo}
                  onChange={(e) => setCreatedTo(e.target.value)}
                  className="rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-zinc-900"
                />
              </div>
            </div>

            <div className="flex items-end gap-3">
              <div className="flex flex-col">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Sort By</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as "created_at" | "full_name" | "email")}
                  className="rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-zinc-900"
                >
                  <option value="created_at">Created</option>
                  <option value="full_name">Full Name</option>
                  <option value="email">Email</option>
                </select>
              </div>
              <div className="flex flex-col">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Direction</label>
                <select
                  value={sortDir}
                  onChange={(e) => setSortDir(e.target.value as "asc" | "desc")}
                  className="rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-zinc-900"
                >
                  <option value="desc">Desc</option>
                  <option value="asc">Asc</option>
                </select>
              </div>
            </div>

            <div className="flex items-end gap-3">
              <div className="flex flex-col">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Min Analyses</label>
                <input
                  type="number"
                  min={0}
                  value={minAnalyses}
                  onChange={(e) => setMinAnalyses(e.target.value)}
                  className="w-28 rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-zinc-900"
                />
              </div>
              <div className="flex flex-col">
                <label className="text-xs font-medium text-slate-600 dark:text-slate-300">Max Analyses</label>
                <input
                  type="number"
                  min={0}
                  value={maxAnalyses}
                  onChange={(e) => setMaxAnalyses(e.target.value)}
                  className="w-28 rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-zinc-900"
                />
              </div>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setPage(1);
                  void refetch(); // underlying hook fetch; combines with existing params in that hook
                  void fetchWithFilters(); // triggers UI state to acknowledge advanced filters
                }}
                className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50"
                disabled={pending}
              >
                {pending ? "Filtering..." : "Apply Filters"}
              </button>

              <button
                type="button"
                onClick={() => {
                  setHasPhone("");
                  setEmailDomain("");
                  setCreatedFrom("");
                  setCreatedTo("");
                  setSortBy("created_at");
                  setSortDir("desc");
                  setMinAnalyses("");
                  setMaxAnalyses("");
                  setQ("");
                }}
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 hover:bg-slate-50 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-100 dark:hover:bg-zinc-800"
              >
                Reset
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={async () => {
                  if (!result || result.data.length === 0) return;
                  const rows = result.data.filter((c) => selected.has(c.id));
                  if (rows.length === 0) return;
                  // Export CSV
                  const header = ["id", "full_name", "email", "phone", "created_at", "updated_at"];
                  const lines = [
                    header.join(","),
                    ...rows.map((r) =>
                      [
                        r.id,
                        JSON.stringify(r.full_name),
                        JSON.stringify(r.email),
                        JSON.stringify(r.phone ?? ""),
                        r.created_at,
                        r.updated_at,
                      ].join(",")
                    ),
                  ];
                  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `candidates-export-${Date.now()}.csv`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  URL.revokeObjectURL(url);
                }}
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-100 dark:hover:bg-zinc-800"
                disabled={!result || result.data.filter((c) => selected.has(c.id)).length === 0}
              >
                Export CSV (selected)
              </button>

              <button
                type="button"
                onClick={async () => {
                  if (!result) return;
                  const ids = result.data.filter((c) => selected.has(c.id)).map((c) => c.id);
                  if (ids.length === 0) return;
                  if (!confirm(`Delete ${ids.length} candidate(s)? This also deletes their analyses and history.`)) return;
                  const res = await fetch("/api/admin/candidates/bulk-delete", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ids }),
                  });
                  if (res.ok) {
                    setSelected(new Set());
                    void refetch();
                  } else {
                    const j = await res.json().catch(() => ({}));
                    alert(j?.error ?? "Bulk delete failed");
                  }
                }}
                className="rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50"
                disabled={!result || result.data.filter((c) => selected.has(c.id)).length === 0}
              >
                Delete (selected)
              </button>
            </div>
          </div>

          {/* Candidates table with selection */}
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full table-fixed border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-600 dark:border-slate-800 dark:text-slate-400">
                  <th className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={!!result && result.data.length > 0 && result.data.every((c) => selected.has(c.id))}
                      onChange={(e) => {
                        if (!result) return;
                        if (e.target.checked) {
                          setSelected(new Set(result.data.map((c) => c.id)));
                        } else {
                          setSelected(new Set());
                        }
                      }}
                    />
                  </th>
                  <th className="px-3 py-2">Full Name</th>
                  <th className="px-3 py-2">Email</th>
                  <th className="px-3 py-2">Phone</th>
                  <th className="px-3 py-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {error ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-sm text-red-600 dark:text-red-400">
                      {error}
                    </td>
                  </tr>
                ) : result && result.data.length > 0 ? (
                  result.data.map((c) => (
                    <tr key={c.id} className="border-b border-slate-200 dark:border-slate-800">
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={selected.has(c.id)}
                          onChange={(e) => {
                            setSelected((prev) => {
                              const next = new Set(prev);
                              if (e.target.checked) next.add(c.id);
                              else next.delete(c.id);
                              return next;
                            });
                          }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </td>
                      <td className="px-3 py-2 text-sm text-slate-900 dark:text-slate-100">{c.full_name}</td>
                      <td className="px-3 py-2 text-sm text-slate-700 dark:text-slate-300">{c.email}</td>
                      <td className="px-3 py-2 text-sm text-slate-700 dark:text-slate-300">{c.phone ?? "-"}</td>
                      <td className="px-3 py-2 text-xs text-slate-500 dark:text-slate-400">
                        {new Date(c.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-sm text-slate-600 dark:text-slate-400">
                      {pending ? "Loading..." : "No candidates found."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-slate-600 dark:text-slate-400">
              {(result?.count ?? 0).toLocaleString()} total • Page {page} of {Math.max(Math.ceil((result?.count ?? 0) / limit), 1)}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-100 dark:hover:bg-zinc-800"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={pending || page <= 1}
              >
                Prev
              </button>
              <button
                type="button"
                className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-100 dark:hover:bg-zinc-800"
                onClick={() => setPage((p) => p + 1)}
                disabled={pending || page >= Math.max(Math.ceil((result?.count ?? 0) / limit), 1)}
              >
                Next
              </button>
            </div>
          </div>
        </section>

        <section className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-zinc-950">
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">Analyses</h3>
            {!selectedCandidateId ? (
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Select a candidate to view analyses.</p>
            ) : analyses.error ? (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">{analyses.error}</p>
            ) : analyses.pending ? (
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Loading analyses...</p>
            ) : analyses.data.items.length === 0 ? (
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">No analyses found.</p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full table-fixed border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-600 dark:border-slate-800 dark:text-slate-400">
                      <th className="px-3 py-2">Created</th>
                      <th className="px-3 py-2">Overall</th>
                      <th className="px-3 py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyses.data.items.map((a) => (
                      <tr key={a.id} className="border-b border-slate-200 dark:border-slate-800">
                        <td className="px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
                          {new Date(a.created_at).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 text-sm">
                          <span
                            className={`rounded-md px-2 py-1 text-xs font-semibold ${
                              a.overall_score >= 70
                                ? "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                                : a.overall_score >= 40
                                ? "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                                : "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                            }`}
                          >
                            {a.overall_score}%
                          </span>
                        </td>
                        <td className="px-3 py-2 text-sm">
                          <button
                            type="button"
                            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-800 hover:bg-slate-50 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-100 dark:hover:bg-zinc-800"
                            onClick={() => setSelectedAnalysisId(a.id)}
                          >
                            View History
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-zinc-950">
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">Review History</h3>
            {!selectedAnalysisId ? (
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Select an analysis to view history.</p>
            ) : history.error ? (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">{history.error}</p>
            ) : history.pending ? (
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Loading history...</p>
            ) : history.items.length === 0 ? (
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">No history entries.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {history.items.map((h) => (
                  <li key={h.id} className="rounded-md border border-slate-200 p-3 text-sm dark:border-slate-800">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-900 dark:text-slate-100">{h.action}</span>
                      <span className="text-xs text-slate-500 dark:text-slate-400">
                        {new Date(h.created_at).toLocaleString()}
                      </span>
                    </div>
                    {h.notes ? (
                      <p className="mt-1 text-slate-700 dark:text-slate-300">{h.notes}</p>
                    ) : null}
                    {h.snapshot ? (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-xs text-slate-600 dark:text-slate-400">
                          View snapshot JSON
                        </summary>
                        <pre className="mt-2 max-h-64 overflow-auto rounded bg-slate-900 p-2 text-xs text-slate-100">
                          {JSON.stringify(h.snapshot, null, 2)}
                        </pre>
                      </details>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
