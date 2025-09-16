import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/database.types";

type AggregatedReport = {
  overall_score: number;
  weights_applied: Record<string, number>;
  slices: Array<{ label: string; score: number; description: string }>;
  evidence: {
    contact?: unknown | null;
    ai?: unknown | null;
  };
  rationale: string[];
  generated_at: string;
  version: string;
};

type SaveAnalysisBody = {
  candidate: {
    full_name: string;
    email: string;
    phone?: string | null;
  };
  report: AggregatedReport;
};

export async function POST(req: NextRequest) {
  try {
    const payload = (await req.json()) as SaveAnalysisBody;

    if (
      !payload?.candidate?.full_name ||
      !payload?.candidate?.email ||
      typeof payload?.report?.overall_score !== "number"
    ) {
      return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
    }

    const supabase = await createClient();

    // Explicitly type the table rows to avoid `never` inference
    type CandidateRow = Database["public"]["Tables"]["candidates"]["Row"];
    type CandidateInsert = Database["public"]["Tables"]["candidates"]["Insert"];
    type AnalysesRow = Database["public"]["Tables"]["analyses"]["Row"];
    type AnalysesInsert = Database["public"]["Tables"]["analyses"]["Insert"];
    type ReviewInsert = Database["public"]["Tables"]["review_history"]["Insert"];

    // 1) Upsert candidate by email
    const upsertCandidate: CandidateInsert = {
      full_name: payload.candidate.full_name,
      email: payload.candidate.email,
      phone: payload.candidate.phone ?? null,
    };

    const { data: candidateRow, error: candErr } = await supabase
      .from("candidates")
      .upsert(upsertCandidate as CandidateInsert, { onConflict: "email" })
      .select()
      .single<CandidateRow>();

    if (candErr || !candidateRow) {
      return NextResponse.json(
        { error: candErr?.message ?? "Failed to upsert candidate" },
        { status: 500 }
      );
    }

    // 2) Insert analysis row
    const analysisInsert: AnalysesInsert = {
      candidate_id: candidateRow.id,
      overall_score: payload.report.overall_score,
      report: payload.report as AnalysesRow["report"],
      ai_detection: (payload.report.evidence?.ai ?? null) as AnalysesRow["ai_detection"],
      contact_verification: (payload.report.evidence?.contact ?? null) as AnalysesRow["contact_verification"],
    };

    const { data: analysisRow, error: analysisErr } = await supabase
      .from("analyses")
      .insert(analysisInsert as AnalysesInsert)
      .select()
      .single<AnalysesRow>();

    if (analysisErr || !analysisRow) {
      return NextResponse.json(
        { error: analysisErr?.message ?? "Failed to insert analysis" },
        { status: 500 }
      );
    }

    // 3) Audit trail entry
    const historyInsert: ReviewInsert = {
      candidate_id: candidateRow.id,
      analysis_id: analysisRow.id,
      action: "created",
      notes: "Initial analysis saved",
      snapshot: analysisInsert.report,
    };

    const { error: historyErr } = await supabase
      .from("review_history")
      .insert(historyInsert as ReviewInsert);

    if (historyErr) {
      return NextResponse.json(
        {
          ok: true,
          candidate_id: candidateRow.id,
          analysis_id: analysisRow.id,
          warning: `Saved analysis, but failed to write audit history: ${historyErr.message}`,
        },
        { status: 207 }
      );
    }

    return NextResponse.json(
      { ok: true, candidate_id: candidateRow.id, analysis_id: analysisRow.id },
      { status: 200 }
    );
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
