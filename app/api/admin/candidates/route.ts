import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/database.types";

type CandidateRow = Database["public"]["Tables"]["candidates"]["Row"];

type ListResponse = {
  data: CandidateRow[];
  count: number;
};

export async function GET(req: NextRequest) {
  try {
    const supabase = await createClient();

    const { searchParams } = new URL(req.url);
    const q = (searchParams.get("q") ?? "").trim();
    const limit = Math.min(Math.max(Number(searchParams.get("limit") ?? "25"), 1), 100);
    const page = Math.max(Number(searchParams.get("page") ?? "1"), 1);
    const offset = (page - 1) * limit;

    const hasPhone = searchParams.get("hasPhone"); // "true" | "false" | null
    const emailDomain = (searchParams.get("emailDomain") ?? "").trim(); // e.g. "gmail.com"
    const createdFrom = searchParams.get("createdFrom"); // ISO date
    const createdTo = searchParams.get("createdTo"); // ISO date
    const sortBy = (searchParams.get("sortBy") ?? "created_at") as "created_at" | "full_name" | "email";
    const sortDir = (searchParams.get("sortDir") ?? "desc") as "asc" | "desc";
    const minAnalyses = Number.isNaN(Number(searchParams.get("minAnalyses"))) ? null : Number(searchParams.get("minAnalyses"));
    const maxAnalyses = Number.isNaN(Number(searchParams.get("maxAnalyses"))) ? null : Number(searchParams.get("maxAnalyses"));

    // Base query
    let query = supabase
      .from("candidates")
      .select("*", { count: "exact" })
      .order(sortBy, { ascending: sortDir === "asc" });

    if (q) {
      query = query.or(`full_name.ilike.%${q}%,email.ilike.%${q}%`);
    }
    if (hasPhone === "true") {
      query = query.not("phone", "is", null);
    } else if (hasPhone === "false") {
      query = query.is("phone", null);
    }
    if (emailDomain) {
      query = query.ilike("email", `%${emailDomain}`);
    }
    if (createdFrom) {
      query = query.gte("created_at", createdFrom);
    }
    if (createdTo) {
      query = query.lte("created_at", createdTo);
    }

    // Apply pagination to base set first
    const { data: pageData, error: baseErr, count } = await query.range(offset, offset + limit - 1);

    if (baseErr) {
      return NextResponse.json({ error: baseErr.message }, { status: 500 });
    }

    // If analyses count filter is requested, fetch counts for the current page and filter in-memory
    let data = (pageData ?? []) as CandidateRow[];

    if (minAnalyses !== null || maxAnalyses !== null) {
      const ids = data.map((c) => c.id);
      if (ids.length > 0) {
        const { data: counts, error: cntErr } = await supabase
          .from("analyses")
          .select("candidate_id, id");

        if (cntErr) {
          return NextResponse.json({ error: cntErr.message }, { status: 500 });
        }

        const map = new Map<string, number>();
        (counts ?? []).forEach((row) => {
          const cid = (row as { candidate_id: string }).candidate_id;
          map.set(cid, (map.get(cid) ?? 0) + 1);
        });

        data = data.filter((c) => {
          const n = map.get(c.id) ?? 0;
          if (minAnalyses !== null && n < minAnalyses) return false;
          if (maxAnalyses !== null && n > maxAnalyses) return false;
          return true;
        });
      }
    }

    const payload: ListResponse = {
      data,
      count: count ?? 0,
    };

    return NextResponse.json(payload, { status: 200 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
