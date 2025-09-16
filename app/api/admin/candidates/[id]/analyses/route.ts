import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/database.types";

type AnalysisRow = Database["public"]["Tables"]["analyses"]["Row"];

type ListAnalysesResponse = {
  data: Array<
    Pick<AnalysisRow, "id" | "created_at" | "overall_score" | "report" | "ai_detection" | "contact_verification">
  >;
  count: number;
};

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = await createClient();
    const candidateId = params.id;

    const { searchParams } = new URL(req.url);
    const limit = Math.min(Math.max(Number(searchParams.get("limit") ?? "25"), 1), 100);
    const page = Math.max(Number(searchParams.get("page") ?? "1"), 1);
    const offset = (page - 1) * limit;

    const { data, error, count } = await supabase
      .from("analyses")
      .select("id, created_at, overall_score, report, ai_detection, contact_verification", { count: "exact" })
      .eq("candidate_id", candidateId)
      .order("created_at", { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    const payload: ListAnalysesResponse = {
      data:
        (data as Array<
          Pick<AnalysisRow, "id" | "created_at" | "overall_score" | "report" | "ai_detection" | "contact_verification">
        >) ?? [],
      count: count ?? 0,
    };

    return NextResponse.json(payload, { status: 200 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
