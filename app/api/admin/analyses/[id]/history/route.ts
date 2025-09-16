import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/database.types";

type ReviewRow = Database["public"]["Tables"]["review_history"]["Row"];

type HistoryResponse = {
  data: Array<Pick<ReviewRow, "id" | "created_at" | "action" | "notes" | "snapshot" | "candidate_id" | "analysis_id">>;
  count: number;
};

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = await createClient();
    const analysisId = params.id;

    const { searchParams } = new URL(req.url);
    const limit = Math.min(Math.max(Number(searchParams.get("limit") ?? "50"), 1), 200);
    const page = Math.max(Number(searchParams.get("page") ?? "1"), 1);
    const offset = (page - 1) * limit;

    const { data, error, count } = await supabase
      .from("review_history")
      .select("id, created_at, action, notes, snapshot, candidate_id, analysis_id", { count: "exact" })
      .eq("analysis_id", analysisId)
      .order("created_at", { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    const payload: HistoryResponse = {
      data:
        (data as Array<
          Pick<ReviewRow, "id" | "created_at" | "action" | "notes" | "snapshot" | "candidate_id" | "analysis_id">
        >) ?? [],
      count: count ?? 0,
    };

    return NextResponse.json(payload, { status: 200 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
