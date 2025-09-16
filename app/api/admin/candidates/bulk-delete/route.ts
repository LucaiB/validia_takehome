import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/database.types";

type CandidateRow = Database["public"]["Tables"]["candidates"]["Row"];

type BulkDeleteBody = {
  ids: string[];
};

export async function POST(req: NextRequest) {
  try {
    const supabase = await createClient();
    const body = (await req.json()) as Partial<BulkDeleteBody> | null;

    if (!body || !Array.isArray(body.ids) || body.ids.length === 0) {
      return NextResponse.json({ error: "ids array required" }, { status: 400 });
    }

    const { error } = await supabase.from("candidates").delete().in("id", body.ids as string[]);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ ok: true, deleted: body.ids.length }, { status: 200 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
