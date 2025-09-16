import { NextRequest, NextResponse } from "next/server";

// Python API configuration
const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000";

type DetectRequestBody = {
  text: string;
  model?: string;
};

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as DetectRequestBody;
    if (!body?.text || typeof body.text !== "string") {
      return NextResponse.json({ error: "Missing text" }, { status: 400 });
    }

    // Forward the request to the Python API
    const response = await fetch(`${PYTHON_API_URL}/ai-detect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: body.text,
        model: body.model || "claude-sonnet-4",
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Python API error:", response.status, errorText);
      return NextResponse.json(
        { 
          error: `Python API error: ${response.status}`,
          details: errorText 
        }, 
        { status: response.status }
      );
    }

    const result = await response.json();
    
    // Transform the Python API response to match the expected frontend format
    return NextResponse.json(
      {
        result: result,
        rationale: result.rationale,
        usage: result.usage,
        request_id: result.request_id,
      },
      { status: 200 }
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("AI detect error:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}