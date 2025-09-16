import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import type { Database } from "@/database.types";

// ... existing code ...
type CandidateRow = Database["public"]["Tables"]["candidates"]["Row"];
type CandidateUpdate = Database["public"]["Tables"]["candidates"]["Update"];

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = await createClient();
    const id = params.id;

    const { data, error } = await supabase.from("candidates").select("*").eq("id", id).single<CandidateRow>();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
    if (!data) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return NextResponse.json({ data }, { status: 200 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = await createClient();
    const id = params.id;
    const body = (await req.json()) as Partial<Pick<CandidateRow, "full_name" | "email" | "phone">> | null;

    if (!body || Object.keys(body).length === 0) {
      return NextResponse.json({ error: "No fields to update" }, { status: 400 });
    }

    const update: CandidateUpdate = {};
    if (typeof body.full_name === "string") {
      const v = body.full_name.trim();
      if (!v) return NextResponse.json({ error: "full_name cannot be empty" }, { status: 400 });
      update.full_name = v;
    }
    if (typeof body.email === "string") {
      const v = body.email.trim().toLowerCase();
      if (!v) return NextResponse.json({ error: "email cannot be empty" }, { status: 400 });
      update.email = v;
    }
    if (body.phone !== undefined) {
      update.phone = body.phone ?? null;
    }

    const { data, error } = await supabase
      .from("candidates")
      .update(update)
      .eq("id", id)
      .select("*")
      .single<CandidateRow>();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
    if (!data) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return NextResponse.json({ data }, { status: 200 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = await createClient();
    const id = params.id;

    const { error } = await supabase.from("candidates").delete().eq("id", id);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ ok: true }, { status: 200 });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
