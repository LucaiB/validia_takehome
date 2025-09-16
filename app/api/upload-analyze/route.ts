import { NextRequest, NextResponse } from "next/server";

// Python API configuration
const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    // Get the form data from the request
    const formData = await req.formData();
    
    // Forward the request to the Python API
    const response = await fetch(`${PYTHON_API_URL}/analyze`, {
      method: "POST",
      body: formData,
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
    const transformedResult = {
      extractedText: result.extractedText,
      candidateInfo: result.candidateInfo,
      aiDetection: result.aiDetection,
      documentAuthenticity: result.documentAuthenticity,
      contactVerification: result.contactVerification,
      backgroundVerification: result.backgroundVerification,
      digitalFootprint: result.digitalFootprint,
      aggregatedReport: result.aggregatedReport,
      rationale: result.rationale,
      usage: result.usage,
      request_id: result.request_id,
    };

    return NextResponse.json(transformedResult, { status: 200 });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("Upload analyze error:", message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}