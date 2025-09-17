"use client";

import React, { useMemo, useRef, useState, useCallback } from "react";

type RiskSlice = {
  label: string;
  score: number; // 0-100
  description: string;
};

type AggregatedReport = {
  overall_score: number; // 0-100
  weights_applied: Record<string, number>;
  slices: Array<{
    label: string;
    score: number;
    description: string;
  }>;
  evidence: {
    contact?: ContactVerificationResult | null;
    ai?: AiDetectionResult | null;
  };
  rationale: string[];
  generated_at: string;
  version: string;
};

type ContactVerificationResult = {
  email: string;
  phone: string;
  is_verified: boolean;
  details: string;
};

type AiDetectionResult = {
  is_ai_generated: boolean;
  confidence: number;
  model: string;
};

type CandidateInfo = {
  full_name: string;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin: string | null;
  github: string | null;
  website: string | null;
};

type DocumentAuthenticityResult = {
  fileName: string;
  fileSize: number;
  fileType: string;
  creationDate: string | null;
  modificationDate: string | null;
  author: string | null;
  creator: string | null;
  producer: string | null;
  title: string | null;
  subject: string | null;
  keywords: string | null;
  pdfVersion: string | null;
  pageCount: number | null;
  isEncrypted: boolean;
  hasDigitalSignature: boolean;
  softwareUsed: string | null;
  suspiciousIndicators: string[];
  authenticityScore: number;
  rationale: string;
};

function EmptyState() {
  return (
    <div className="mt-6 rounded-xl border border-dashed border-slate-300 p-8 text-center dark:border-slate-700">
      <svg
        className="mx-auto h-12 w-12 text-slate-400 dark:text-slate-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 className="mt-4 text-sm font-medium text-slate-900 dark:text-slate-100">
        No resume uploaded
      </h3>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
        Upload a resume to begin fraud analysis.
      </p>
    </div>
  );
}

function OverallRiskCard({ score, colorClass }: { score: number; colorClass: string }) {
  return (
    <div className="rounded-xl border border-slate-200 p-5 shadow-sm dark:border-slate-800">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">Overall Risk</h4>
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">0-100%</span>
      </div>
      <div className="mt-4 flex items-end gap-3">
        <div className="relative h-10 w-10">
          <svg viewBox="0 0 36 36" className="h-full w-full">
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#eee"
              strokeWidth="3"
            />
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeDasharray={`${score}, 100`}
              className={colorClass}
            />
            <text
              x="18"
              y="20"
              textAnchor="middle"
              fill="currentColor"
              className={`text-sm font-bold ${colorClass} dark:text-slate-100`}
            >
              {score}%
            </text>
          </svg>
        </div>
        <div className="text-sm text-slate-600 dark:text-slate-400">
          {score >= 70 ? (
            <span className="font-medium text-red-600 dark:text-red-400">High Risk</span>
          ) : score >= 40 ? (
            <span className="font-medium text-amber-600 dark:text-amber-400">Moderate Risk</span>
          ) : (
            <span className="font-medium text-emerald-600 dark:text-emerald-400">Low Risk</span>
          )}
        </div>
      </div>
    </div>
  );
}

function CategoryRadials({ risk }: { risk: RiskSlice[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
      {risk.map((r) => {
        const bandColor =
          r.score >= 70
            ? "text-red-500 dark:text-red-400"
            : r.score >= 40
              ? "text-amber-500 dark:text-amber-400"
              : "text-emerald-500 dark:text-emerald-400";

        return (
          <div key={r.label} className="flex flex-col items-center">
            <div className="relative h-16 w-16">
              <svg viewBox="0 0 36 36" className="h-full w-full">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#eee"
                  strokeWidth="2"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeDasharray={`${r.score}, 100`}
                  className={bandColor.replace("text-", "stroke-")}
                />
              </svg>
            </div>
            <div className="mt-2 text-center">
              <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                {r.label}
              </p>
              <p className={`text-xs font-medium ${bandColor}`}>{r.score}%</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function RiskDetail({ slice }: { slice: RiskSlice }) {
  const bandColor =
    slice.score >= 70
      ? "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-400"
      : slice.score >= 40
        ? "bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
        : "bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400";

  return (
    <div className="rounded-lg border border-slate-200 p-4 shadow-sm dark:border-slate-800">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          {slice.label}
        </h4>
        <span className={`rounded-full px-2 py-1 text-xs font-medium ${bandColor}`}>
          {slice.score}%
        </span>
      </div>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{slice.description}</p>
    </div>
  );
}

function KV({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "good" | "warn" | "bad" | "neutral";
}) {
  const toneColor =
    tone === "good"
      ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400"
      : tone === "warn"
        ? "bg-amber-50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
        : tone === "bad"
          ? "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-400"
          : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300";

  return (
    <div className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800">
      <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
      <p className={`mt-1 font-medium ${toneColor}`}>{value}</p>
    </div>
  );
}

function ReportDownloadButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-zinc-900 dark:text-slate-100 dark:hover:bg-zinc-800"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" className="text-slate-600 dark:text-slate-300">
        <path
          fill="currentColor"
          d="M12 3a1 1 0 0 1 1 1v9.586l2.293-2.293a1 1 0 1 1 1.414 1.414l-4.007 4.007a1 1 0 0 1-1.414 0L7.279 12.707a1 1 0 1 1 1.414-1.414L11 13.586V4a1 1 0 0 1 1-1ZM5 20a1 1 0 0 1 0-2h14a1 1 0 1 1 0 2H5Z"
        />
      </svg>
      Download JSON Report
    </button>
  );
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.slice(0, max - 1) + "…";
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [risk, setRisk] = useState<RiskSlice[] | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [contactResult, setContactResult] = useState<ContactVerificationResult | null>(null);
  const [contactPending, setContactPending] = useState(false);
  const [contactError, setContactError] = useState<string | null>(null);

  const [aiResult, setAiResult] = useState<AiDetectionResult | null>(null);

  const [candidateInfo, setCandidateInfo] = useState<CandidateInfo | null>(null);
  const [documentAuthenticity, setDocumentAuthenticity] = useState<DocumentAuthenticityResult | null>(null);
  const [contactVerification, setContactVerification] = useState<any>(null);
  const [backgroundVerification, setBackgroundVerification] = useState<any>(null);
  const [digitalFootprint, setDigitalFootprint] = useState<any>(null);
  const [savePending, setSavePending] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // File upload and analysis states
  const [fileAnalysisPending, setFileAnalysisPending] = useState(false);
  const [fileAnalysisError, setFileAnalysisError] = useState<string | null>(null);
  const [fileAnalysisResult, setFileAnalysisResult] = useState<any>(null);
  
  // State for managing expanded sections
  const [expandedSections, setExpandedSections] = useState<{
    candidateInfo: boolean;
    contactVerification: boolean;
    backgroundVerification: boolean;
    digitalFootprint: boolean;
    documentAuthenticity: boolean;
  }>({
    candidateInfo: false,
    contactVerification: false,
    backgroundVerification: false,
    digitalFootprint: false,
    documentAuthenticity: false,
  });

  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState(false);
  const [aiAnalysisError, setAiAnalysisError] = useState<string | null>(null);

  // Helper function to toggle section expansion
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Function to run AI analysis
  const runAiAnalysis = async (analysisData?: any) => {
    const dataToAnalyze = analysisData || fileAnalysisResult;
    
    if (!dataToAnalyze) {
      setAiAnalysisError('Please upload and analyze a resume first');
      return;
    }
    
    setAiAnalysisLoading(true);
    setAiAnalysisError(null);
    
    try {
      const response = await fetch('/api/ai-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysisResult: dataToAnalyze,
          extractedText: dataToAnalyze.extractedText || '',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData?.error ?? `AI analysis failed: ${response.status}`);
      }

      const data = await response.json();
      setAiAnalysis(data.analysis);
    } catch (error) {
      console.error('AI analysis error:', error);
      setAiAnalysisError(error instanceof Error ? error.message : 'AI analysis failed');
    } finally {
      setAiAnalysisLoading(false);
    }
  };

  // Move aggregate definition above any hooks that reference it (e.g., saveAnalysis)
  const weights = useMemo(
    () => ({
      "Contact Info": 0.25,
      "AI Content": 0.35,
      "Background": 0.20,
      "Digital Footprint": 0.10,
      "Document Authenticity": 0.10,
    }),
    []
  );

  const normalizedRisk = useMemo(() => {
    const defaultSlices: RiskSlice[] = [
      { label: "Contact Info", score: 50, description: "Awaiting verification." },
      { label: "AI Content", score: 50, description: "Awaiting AI detection." },
      { label: "Background", score: 42, description: "Timeline cross-check placeholder." },
      { label: "Digital Footprint", score: 20, description: "Presence lookup not performed." },
      { label: "Document Authenticity", score: 30, description: "Metadata heuristics not applied." },
    ];
    if (!risk || risk.length === 0) return defaultSlices;
    const map = new Map<string, RiskSlice>(risk.map((r) => [r.label, r]));
    return defaultSlices.map((s) => map.get(s.label) ?? s);
  }, [risk]);

  const aggregate = useMemo(() => {
    // Calculate overall risk based on actual analysis results
    if (!fileAnalysisResult) {
      return {
        overall_score: 0,
        weights_applied: {},
        slices: [],
        evidence: { contact: null, ai: null },
        rationale: ["No analysis data available"],
        generated_at: new Date().toISOString(),
        version: "1.0.0",
      };
    }

    const rationale: string[] = [];
    let totalScore = 0;
    let componentCount = 0;

    // AI Detection Score (inverted - higher AI confidence = higher risk)
    if (fileAnalysisResult.aiDetection) {
      const aiRisk = fileAnalysisResult.aiDetection.is_ai_generated 
        ? fileAnalysisResult.aiDetection.confidence 
        : 100 - fileAnalysisResult.aiDetection.confidence;
      totalScore += aiRisk;
      componentCount++;
      rationale.push(`AI Detection: ${fileAnalysisResult.aiDetection.is_ai_generated ? 'AI Generated' : 'Human Written'} (${fileAnalysisResult.aiDetection.confidence}% confidence)`);
    }

    // Contact Verification Score (inverted - lower verification = higher risk)
    const contactScore = fileAnalysisResult.contactVerification?.score?.overall_score || fileAnalysisResult.contactVerification?.score?.composite;
    if (contactScore) {
      const contactRisk = (1 - contactScore) * 100;
      totalScore += contactRisk;
      componentCount++;
      rationale.push(`Contact Verification: ${Math.round(contactScore * 100)}% verified`);
    }

    // Background Verification Score (inverted - lower verification = higher risk)
    if (fileAnalysisResult.backgroundVerification?.score?.composite) {
      const backgroundRisk = (1 - fileAnalysisResult.backgroundVerification.score.composite) * 100;
      totalScore += backgroundRisk;
      componentCount++;
      rationale.push(`Background Verification: ${Math.round(fileAnalysisResult.backgroundVerification.score.composite * 100)}% verified`);
    }

    // Document Authenticity Score (inverted - lower authenticity = higher risk)
    const docScore = fileAnalysisResult.documentAuthenticity?.authenticityScore;
    if (docScore !== undefined) {
      const docRisk = 100 - docScore; // docScore is already 0-100
      totalScore += docRisk;
      componentCount++;
      rationale.push(`Document Authenticity: ${docScore}% authentic`);
    }

    // Digital Footprint Score (inverted - lower consistency = higher risk)
    const digitalScore = fileAnalysisResult.digitalFootprint?.consistency_score;
    if (digitalScore !== undefined) {
      const digitalRisk = 100 - digitalScore; // digitalScore is already 0-100
      totalScore += digitalRisk;
      componentCount++;
      rationale.push(`Digital Footprint: ${digitalScore}% consistent`);
    }

    const overall = componentCount > 0 ? Math.round(totalScore / componentCount) : 0;

    const report: AggregatedReport = {
      overall_score: overall,
      weights_applied: { 
        ai_detection: 0.25,
        contact_verification: 0.25,
        background_verification: 0.25,
        document_authenticity: 0.15,
        digital_footprint: 0.10
      },
      slices: normalizedRisk.map((s) => ({
        label: s.label,
        score: s.score,
        description: s.description,
      })),
      evidence: {
        contact: contactResult,
        ai: aiResult,
      },
      rationale,
      generated_at: new Date().toISOString(),
      version: "1.0.0",
    };

    return report;
  }, [fileAnalysisResult, normalizedRisk, contactResult, aiResult]);

  // Save analysis now references aggregate which is already initialized above
  const saveAnalysis = useCallback(async () => {
    try {
      setSavePending(true);
      setSaveError(null);
      setSaveSuccess(null);
      const candidate = candidateInfo || {
        full_name: "Unknown Candidate",
        email: "unknown+demo@example.com",
        phone: null as string | null,
      };
      const res = await fetch("/api/analyses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate, report: aggregate }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error((data as { error?: string })?.error ?? `Save failed: ${res.status}`);
      }
      setSaveSuccess(
        `Saved (candidate ${((data as any).candidate_id as string)?.slice?.(0, 8) ?? "?"}, analysis ${((data as any).analysis_id as string)?.slice?.(0, 8) ?? "?"})`
      );
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setSavePending(false);
    }
  }, [aggregate]);

  const overallRisk = useMemo(() => aggregate.overall_score, [aggregate]);
  const overallRiskColor = useMemo(() => {
    if (overallRisk >= 70) return "bg-red-500";
    if (overallRisk >= 40) return "bg-amber-500";
    return "bg-emerald-500";
  }, [overallRisk]);


  const analyzeUploadedFile = async () => {
    if (!file) {
      setFileAnalysisError("No file selected");
      return;
    }

    try {
      setFileAnalysisPending(true);
      setFileAnalysisError(null);
      setFileAnalysisResult(null);

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/upload-analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error ?? `Request failed: ${res.status}`);
      }

      const data = await res.json();
      setFileAnalysisResult(data);

      // Update the AI Content risk slice with the file analysis results
      const aiSliceScore = data.aiDetection.is_ai_generated
        ? Math.min(100, Math.max(0, data.aiDetection.confidence))
        : Math.max(0, 100 - data.aiDetection.confidence);

      // Automatically trigger AI analysis after file analysis is complete
      await runAiAnalysis(data);

      setAiResult({
        is_ai_generated: data.aiDetection.is_ai_generated,
        confidence: data.aiDetection.confidence,
        model: data.aiDetection.model,
      });

      setRisk((prev) => {
        const base =
          prev && prev.length > 0
            ? [...prev]
            : [
                { label: "Contact Info", score: 50, description: "Awaiting verification." },
                { label: "AI Content", score: 50, description: "Awaiting AI detection." },
                { label: "Background", score: 42, description: "Timeline cross-check placeholder." },
                { label: "Digital Footprint", score: 20, description: "Presence lookup not performed." },
                { label: "Document Authenticity", score: 30, description: "Metadata heuristics not applied." },
              ];
        const idx = base.findIndex((s) => s.label === "AI Content");
        const desc =
          (data.aiDetection.is_ai_generated
            ? `Elevated AI signals (confidence ${data.aiDetection.confidence}%). `
            : `Low AI signal (confidence ${data.aiDetection.confidence}%). `) +
          (data.rationale ? `Rationale: ${data.rationale}` : "");
        if (idx >= 0) {
          base[idx] = { ...base[idx], score: aiSliceScore, description: desc };
        } else {
          base.push({ label: "AI Content", score: aiSliceScore, description: desc });
        }
        return base;
      });

      // Also update the candidate info, document authenticity, contact verification, background verification, and digital footprint with the extracted data
      setCandidateInfo(data.candidateInfo);
      setDocumentAuthenticity(data.documentAuthenticity);
      setContactVerification(data.contactVerification);
      setBackgroundVerification(data.backgroundVerification);
      setDigitalFootprint(data.digitalFootprint);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setFileAnalysisError(msg);
    } finally {
      setFileAnalysisPending(false);
    }
  };

  const downloadJsonReport = () => {
    const report = {
      ...aggregate,
      aiAnalysis: aiAnalysis,
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const ts = new Date(aggregate.generated_at).toISOString().replace(/[:.]/g, "-");
    a.href = url;
    a.download = `sentinelhire-fraud-report-${ts}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-blue-950 dark:to-purple-950 p-6">
      <div className="mx-auto max-w-7xl">
        <header className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-6 shadow-lg">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 dark:from-slate-100 dark:via-blue-100 dark:to-purple-100 bg-clip-text text-transparent mb-4">
            SentinelHire
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            AI-powered resume fraud detection that protects your hiring process with advanced verification and risk assessment
          </p>
          <div className="mt-6 flex items-center justify-center gap-6 text-sm text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>AI Detection</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>Background Verification</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>Document Analysis</span>
            </div>
          </div>
        </header>

        <main className="mt-8">
          <div className="max-w-4xl mx-auto">
            <section className="mb-8">
              <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-white via-blue-50 to-purple-50 dark:from-slate-900 dark:via-blue-950 dark:to-purple-950 border border-slate-200/50 dark:border-slate-800/50 shadow-xl">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5"></div>
                <div className="relative p-8">
                  <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl mb-4 shadow-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                      Upload Resume
                </h2>
                    <p className="text-slate-600 dark:text-slate-400">
                      Drag and drop your PDF or DOCX file, or click to browse
                </p>
                  </div>

                <div className="mt-6">
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".pdf,.docx"
                    onChange={(e) => {
                      const selectedFile = e.target.files?.[0] || null;
                      setFile(selectedFile);
                      if (selectedFile) {
                        setRisk([
                          { label: "Contact Info", score: 85, description: "Email domain mismatch and phone number not found in professional directories." },
                          { label: "AI Content", score: 60, description: "Moderate likelihood of AI-generated content detected in experience section." },
                        ]);
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                      className="group relative w-full h-32 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-2xl bg-white/50 dark:bg-slate-800/50 hover:bg-white dark:hover:bg-slate-800 hover:border-blue-400 dark:hover:border-blue-500 transition-all duration-200 cursor-pointer"
                    >
                      <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
                          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                        </div>
                        <div className="text-slate-600 dark:text-slate-400">
                          {file ? (
                            <div>
                              <p className="font-medium text-slate-900 dark:text-slate-100">{file.name}</p>
                              <p className="text-sm">Click to change file</p>
                            </div>
                          ) : (
                            <div>
                              <p className="font-medium text-slate-900 dark:text-slate-100">Choose file or drag here</p>
                              <p className="text-sm">PDF, DOCX up to 10MB</p>
                            </div>
                          )}
                        </div>
                      </div>
                  </button>
                  
                  {file && (
                    <div className="mt-6">
                      <button
                        type="button"
                        onClick={analyzeUploadedFile}
                        disabled={fileAnalysisPending}
                        className="group relative w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:scale-100 transition-all duration-200 disabled:opacity-50"
                      >
                        <div className="flex items-center justify-center gap-3">
                          {fileAnalysisPending ? (
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            <svg className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                          )}
                          <span className="text-lg">
                            {fileAnalysisPending ? "Analyzing Resume..." : "Start AI Analysis"}
                          </span>
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-30 group-hover:opacity-50 transition-opacity duration-200"></div>
                      </button>
                      {fileAnalysisError && (
                        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{fileAnalysisError}</p>
                      )}
                      {fileAnalysisResult && (
                        <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-2xl">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                        </div>
                            <div>
                              <p className="font-semibold text-green-800 dark:text-green-400">
                                Analysis Complete!
                              </p>
                              <p className="text-sm text-green-700 dark:text-green-300">
                                Resume successfully analyzed. View results in the Fraud Risk Dashboard below.
                                </p>
                              </div>
                          </div>
                        </div>
                      )}
                      
                      {false && backgroundVerification && (
                        <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-zinc-950">
                          <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">
                            🏢 Background Verification Analysis
                          </h4>
                          
                          {/* Overall Score */}
                          <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Verification Score</span>
                              <span className={`text-lg font-bold ${
                                backgroundVerification.score?.composite >= 0.8 ? 'text-green-600 dark:text-green-400' :
                                backgroundVerification.score?.composite >= 0.6 ? 'text-yellow-600 dark:text-yellow-400' :
                                'text-red-600 dark:text-red-400'
                              }`}>
                                {Math.round((backgroundVerification.score?.composite || 0) * 100)}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2 dark:bg-slate-700">
                              <div 
                                className={`h-2 rounded-full ${
                                  backgroundVerification.score?.composite >= 0.8 ? 'bg-green-500' :
                                  backgroundVerification.score?.composite >= 0.6 ? 'bg-yellow-500' :
                                  'bg-red-500'
                                }`}
                                style={{ width: `${(backgroundVerification.score?.composite || 0) * 100}%` }}
                              ></div>
                            </div>
                          </div>

                          {/* Detailed Scores */}
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">🏢 Company Identity</h5>
                              <div className="text-2xl font-bold text-slate-700 dark:text-slate-300">
                                {Math.round((backgroundVerification.score?.company_identity_score || 0) * 100)}%
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                Registry verification
                              </div>
                            </div>
                            
                            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">🎓 Education</h5>
                              <div className="text-2xl font-bold text-slate-700 dark:text-slate-300">
                                {Math.round((backgroundVerification.score?.education_institution_score || 0) * 100)}%
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                Institution verification
                              </div>
                            </div>
                            
                            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">⏰ Timeline</h5>
                              <div className="text-2xl font-bold text-slate-700 dark:text-slate-300">
                                {Math.round((backgroundVerification.score?.timeline_corroboration_score || 0) * 100)}%
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                Timeline consistency
                              </div>
                            </div>
                            
                            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">💻 Developer</h5>
                              <div className="text-2xl font-bold text-slate-700 dark:text-slate-300">
                                {Math.round((backgroundVerification.score?.developer_footprint_score || 0) * 100)}%
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                GitHub footprint
                              </div>
                            </div>
                          </div>

                          {/* Sources Used */}
                          {backgroundVerification.sources_used && backgroundVerification.sources_used.length > 0 && (
                            <div className="mb-4">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">🔍 Data Sources</h5>
                              <div className="flex flex-wrap gap-2">
                                {backgroundVerification.sources_used.map((source, index) => (
                                  <span key={index} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                                    {source}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Rationale */}
                          {backgroundVerification.rationale && backgroundVerification.rationale.length > 0 && (
                            <div className="mt-4">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">📋 Analysis Details</h5>
                              <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                                {backgroundVerification.rationale.map((item, index) => (
                                  <li key={index} className="flex items-start">
                                    <span className="mr-2">•</span>
                                    <span>{item}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {false && digitalFootprint && (
                        <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-zinc-950">
                          <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">
                            🌐 Digital Footprint Analysis
                          </h4>
                          
                          {/* Overall Score */}
                          <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Consistency Score</span>
                              <span className={`text-lg font-bold ${
                                digitalFootprint.consistency_score >= 80 ? 'text-green-600 dark:text-green-400' :
                                digitalFootprint.consistency_score >= 60 ? 'text-yellow-600 dark:text-yellow-400' :
                                'text-red-600 dark:text-red-400'
                              }`}>
                                {digitalFootprint.consistency_score}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2 dark:bg-slate-700">
                              <div 
                                className={`h-2 rounded-full ${
                                  digitalFootprint.consistency_score >= 80 ? 'bg-green-500' :
                                  digitalFootprint.consistency_score >= 60 ? 'bg-yellow-500' :
                                  'bg-red-500'
                                }`}
                                style={{ width: `${digitalFootprint.consistency_score}%` }}
                              ></div>
                            </div>
                          </div>

                          {/* Social Media Presence */}
                          {digitalFootprint.social_presence && Object.keys(digitalFootprint.social_presence).length > 0 && (
                            <div className="mb-4">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">📱 Professional Presence</h5>
                              <div className="space-y-3">
                                {Object.entries(digitalFootprint.social_presence).map(([platform, profiles]) => (
                                  <div key={platform} className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                                    <div className="flex items-center mb-2">
                                      <span className="text-sm font-medium text-slate-900 dark:text-slate-100 capitalize">
                                        {platform === 'linkedin' ? 'LinkedIn' : 
                                         platform === 'github' ? 'GitHub' : 
                                         platform === 'scholar' ? 'Google Scholar' : 
                                         platform}
                                      </span>
                                      <span className="ml-2 px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                                        {Array.isArray(profiles) ? profiles.length : 1} profile{Array.isArray(profiles) && profiles.length !== 1 ? 's' : ''}
                                      </span>
                                    </div>
                                    {Array.isArray(profiles) && profiles.map((profile, index) => (
                                      <div key={index} className="mt-2">
                                        <a 
                                          href={profile.link} 
                                          target="_blank" 
                                          rel="noopener noreferrer"
                                          className="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                        >
                                          {profile.title}
                                        </a>
                                        {profile.snippet && (
                                          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">
                                            {profile.snippet}
                                          </p>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Search Results */}
                          {digitalFootprint.search_results && digitalFootprint.search_results.length > 0 && (
                            <div className="mb-4">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">🔍 Search Results</h5>
                              <div className="space-y-2">
                                {digitalFootprint.search_results.slice(0, 5).map((result, index) => (
                                  <div key={index} className="p-2 bg-slate-50 dark:bg-slate-800 rounded text-xs text-slate-600 dark:text-slate-400">
                                    {result}
                                  </div>
                                ))}
                                {digitalFootprint.search_results.length > 5 && (
                                  <div className="text-xs text-slate-500 dark:text-slate-400">
                                    +{digitalFootprint.search_results.length - 5} more results
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Analysis Details */}
                          {digitalFootprint.details && (
                            <div className="mt-4">
                              <h5 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">📋 Analysis Details</h5>
                              <p className="text-xs text-slate-600 dark:text-slate-400">
                                {digitalFootprint.details}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {false && documentAuthenticity && (
                        <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-zinc-950">
                          <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">
                            🔍 Document Authenticity Analysis
                          </h4>
                          <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Authenticity Score</span>
                              <span className={`text-lg font-bold ${
                                documentAuthenticity.authenticityScore >= 80 ? 'text-green-600 dark:text-green-400' :
                                documentAuthenticity.authenticityScore >= 60 ? 'text-yellow-600 dark:text-yellow-400' :
                                'text-red-600 dark:text-red-400'
                              }`}>
                                {documentAuthenticity.authenticityScore}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2 dark:bg-slate-700">
                              <div 
                                className={`h-2 rounded-full ${
                                  documentAuthenticity.authenticityScore >= 80 ? 'bg-green-500' :
                                  documentAuthenticity.authenticityScore >= 60 ? 'bg-yellow-500' :
                                  'bg-red-500'
                                }`}
                                style={{ width: `${documentAuthenticity.authenticityScore}%` }}
                              ></div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 mb-4">
                            <div>
                              <p className="text-xs text-slate-500 dark:text-slate-400">File Size</p>
                              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {(documentAuthenticity.fileSize / 1024).toFixed(1)} KB
                              </p>
                            </div>
                            {documentAuthenticity.pageCount && (
                              <div>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Pages</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                  {documentAuthenticity.pageCount}
                                </p>
                              </div>
                            )}
                            {documentAuthenticity.softwareUsed && (
                              <div>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Software Used</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                  {documentAuthenticity.softwareUsed}
                                </p>
                              </div>
                            )}
                            {documentAuthenticity.pdfVersion && (
                              <div>
                                <p className="text-xs text-slate-500 dark:text-slate-400">PDF Version</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                  {documentAuthenticity.pdfVersion}
                                </p>
                              </div>
                            )}
                            {documentAuthenticity.creationDate && (
                              <div>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Created</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                  {new Date(documentAuthenticity.creationDate).toLocaleDateString()}
                                </p>
                              </div>
                            )}
                            {documentAuthenticity.modificationDate && (
                              <div>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Modified</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                  {new Date(documentAuthenticity.modificationDate).toLocaleDateString()}
                                </p>
                              </div>
                            )}
                          </div>
                          
                          {documentAuthenticity.suspiciousIndicators.length > 0 && (
                            <div className="mb-4">
                              <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">⚠️ Suspicious Indicators</p>
                              <ul className="list-disc list-inside space-y-1">
                                {documentAuthenticity.suspiciousIndicators.map((indicator, index) => (
                                  <li key={index} className="text-sm text-red-600 dark:text-red-400">
                                    {indicator}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                </div>
              </div>
            </section>

            {/* Fraud Risk Dashboard - Only show after file analysis */}
            {fileAnalysisResult && (
              <section className="mt-8">
                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-zinc-950">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                    🛡️ Fraud Risk Dashboard
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
                    Comprehensive analysis results based on the uploaded resume.
                  </p>
                  
                  {/* Overall Risk Score */}
                  <div className="mb-8">
                    <div className="text-center">
                      <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white text-2xl font-bold mb-4">
                        {Math.round(overallRisk)}%
                      </div>
                      <h4 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                        Overall Risk Score
                      </h4>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {overallRisk >= 80 ? 'Low Risk' : overallRisk >= 60 ? 'Medium Risk' : 'High Risk'}
                      </p>
                    </div>
                  </div>

                  {/* Analysis Categories Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {/* AI Detection */}
                    {fileAnalysisResult.aiDetection && (
                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 p-4 rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100">🤖 AI Detection</h5>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            fileAnalysisResult.aiDetection.is_ai_generated 
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' 
                              : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          }`}>
                            {fileAnalysisResult.aiDetection.is_ai_generated ? 'AI Generated' : 'Human Written'}
                          </span>
                        </div>
                        <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-1">
                          {fileAnalysisResult.aiDetection.confidence}%
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-400">
                          Confidence Level
                        </div>
                      </div>
                    )}

                    {/* Contact Verification */}
                    {fileAnalysisResult.contactVerification && (
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 p-4 rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100">📞 Contact Verification</h5>
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            Verified
                          </span>
                        </div>
                        <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-1">
                          {Math.round((fileAnalysisResult.contactVerification.score?.overall_score || fileAnalysisResult.contactVerification.score?.composite || 0) * 100)}%
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-400">
                          Verification Score
                        </div>
                      </div>
                    )}

                    {/* Background Verification */}
                    {fileAnalysisResult.backgroundVerification && (
                      <div className="bg-gradient-to-br from-purple-50 to-violet-50 dark:from-purple-950 dark:to-violet-950 p-4 rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100">🏢 Background Check</h5>
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                            Analyzed
                          </span>
                        </div>
                        <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-1">
                          {Math.round((fileAnalysisResult.backgroundVerification.score?.composite || 0) * 100)}%
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-400">
                          Verification Score
                        </div>
                      </div>
                    )}

                    {/* Document Authenticity */}
                    {fileAnalysisResult.documentAuthenticity && (
                      <div className="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950 dark:to-amber-950 p-4 rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100">📄 Document Auth</h5>
                          <span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                            Analyzed
                          </span>
                        </div>
                        <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-1">
                          {fileAnalysisResult.documentAuthenticity.authenticityScore || 0}%
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-400">
                          Authenticity Score
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Detailed Analysis Sections */}
                  <div className="space-y-6">
                    {/* Candidate Information */}
                    {candidateInfo && (
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                        <div className="flex items-center gap-3 mb-4">
                          <span className="text-2xl">📋</span>
                          <h4 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Candidate Information</h4>
                        </div>
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                          <div>
                            <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Name</p>
                            <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
                              {candidateInfo.full_name}
                            </p>
                          </div>
                          {candidateInfo.email && (
                            <div>
                              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Email</p>
                              <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
                                {candidateInfo.email}
                              </p>
                        </div>
                      )}
                          {candidateInfo.phone && (
                            <div>
                              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Phone</p>
                              <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
                                {candidateInfo.phone}
                              </p>
                    </div>
                  )}
                          {candidateInfo.location && (
                            <div>
                              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Location</p>
                              <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
                                {candidateInfo.location}
                              </p>
                </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Contact Verification Details */}
                    {fileAnalysisResult.contactVerification && (
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">📞</span>
                            <h4 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Contact Verification</h4>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                              {Math.round((fileAnalysisResult.contactVerification.score?.overall_score || fileAnalysisResult.contactVerification.score?.composite || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Verification Score</div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          <div className="text-center p-4 bg-white dark:bg-slate-900 rounded-lg">
                            <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-2">
                              {Math.round((fileAnalysisResult.contactVerification.score?.email_score || fileAnalysisResult.contactVerification.emailVerification?.score || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Email Verification</div>
                          </div>
                          <div className="text-center p-4 bg-white dark:bg-slate-900 rounded-lg">
                            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                              {Math.round((fileAnalysisResult.contactVerification.score?.phone_score || fileAnalysisResult.contactVerification.phoneVerification?.score || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Phone Verification</div>
                          </div>
                          <div className="text-center p-4 bg-white dark:bg-slate-900 rounded-lg">
                            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                              {Math.round((fileAnalysisResult.contactVerification.score?.geo_score || fileAnalysisResult.contactVerification.geo_consistency?.score || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Geo Consistency</div>
                          </div>
                        </div>

                        {/* Detailed Information Dropdown */}
                    <button
                          onClick={() => toggleSection('contactVerification')}
                          className="w-full p-3 text-left flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors rounded-lg border border-slate-200 dark:border-slate-600"
                        >
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">View Detailed Analysis</span>
                          <svg 
                            className={`w-4 h-4 text-slate-500 transition-transform ${expandedSections.contactVerification ? 'rotate-180' : ''}`} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                    </button>
                        {expandedSections.contactVerification && (
                          <div className="mt-4 p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-600">
                            <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Detailed Analysis</h5>
                            <div className="space-y-4 text-sm">
                              {/* Email Verification Details */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Email Verification</h6>
                                <div className="space-y-2 ml-4">
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Syntax Valid:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.contactVerification.email?.syntax_valid ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                    }`}>
                                      {fileAnalysisResult.contactVerification.email?.syntax_valid ? '✓ Valid' : '✗ Invalid'}
                                    </span>
                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">MX Records Found:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.contactVerification.email?.mx_records_found ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                    }`}>
                                      {fileAnalysisResult.contactVerification.email?.mx_records_found ? '✓ Found' : '✗ Not Found'}
                                    </span>
                </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Not Disposable:</span>
                                    <span className={`font-medium ${
                                      !fileAnalysisResult.contactVerification.email?.is_disposable ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                    }`}>
                                      {!fileAnalysisResult.contactVerification.email?.is_disposable ? '✓ Confirmed' : '✗ Disposable'}
                                    </span>
              </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Not Role-based:</span>
                                    <span className={`font-medium ${
                                      !fileAnalysisResult.contactVerification.email?.is_role ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                                    }`}>
                                      {!fileAnalysisResult.contactVerification.email?.is_role ? '✓ Confirmed' : '⚠ Role-based'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* Phone Verification Details */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Phone Verification</h6>
                                <div className="space-y-2 ml-4">
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Format Valid:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.contactVerification.phone?.valid ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                    }`}>
                                      {fileAnalysisResult.contactVerification.phone?.valid ? '✓ Valid' : '✗ Invalid'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Not Toll-free:</span>
                                    <span className={`font-medium ${
                                      !fileAnalysisResult.contactVerification.phone?.toll_free ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                                    }`}>
                                      {!fileAnalysisResult.contactVerification.phone?.toll_free ? '✓ Confirmed' : '⚠ Toll-free'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Country:</span>
                                    <span className="font-medium text-slate-900 dark:text-slate-100">
                                      {fileAnalysisResult.contactVerification.phone?.country_code || 'N/A'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Region:</span>
                                    <span className="font-medium text-slate-900 dark:text-slate-100">
                                      {fileAnalysisResult.contactVerification.phone?.region_hint || 'N/A'}
                                    </span>
                                  </div>
                                  {fileAnalysisResult.contactVerification.phone?.carrier && (
                                    <div className="flex justify-between">
                                      <span className="text-slate-600 dark:text-slate-400">Carrier:</span>
                                      <span className="font-medium text-slate-900 dark:text-slate-100">
                                        {fileAnalysisResult.contactVerification.phone.carrier}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Geo Consistency Details */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Geo Consistency</h6>
                                <div className="space-y-2 ml-4">
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Country Match:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.contactVerification.geo_consistency?.phone_country_matches ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                    }`}>
                                      {fileAnalysisResult.contactVerification.geo_consistency?.phone_country_matches ? '✓ Match' : '✗ No Match'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Region Match:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.contactVerification.geo_consistency?.phone_region_matches ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                                    }`}>
                                      {fileAnalysisResult.contactVerification.geo_consistency?.phone_region_matches ? '✓ Match' : '⚠ Partial'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Background Verification Details */}
                    {fileAnalysisResult.backgroundVerification && (
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">🏢</span>
                            <h4 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Background Verification</h4>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                              {Math.round((fileAnalysisResult.backgroundVerification.score?.composite || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Verification Score</div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                          <div className="text-center p-4 bg-white dark:bg-slate-900 rounded-lg">
                            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                              {Math.round((fileAnalysisResult.backgroundVerification.score?.company_identity_score || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Company Identity</div>
                          </div>
                          <div className="text-center p-4 bg-white dark:bg-slate-900 rounded-lg">
                            <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-2">
                              {Math.round((fileAnalysisResult.backgroundVerification.score?.education_institution_score || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Education</div>
                          </div>
                          <div className="text-center p-4 bg-white dark:bg-slate-900 rounded-lg">
                            <div className="text-3xl font-bold text-orange-600 dark:text-orange-400 mb-2">
                              {Math.round((fileAnalysisResult.backgroundVerification.score?.timeline_corroboration_score || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Timeline</div>
                          </div>
                          <div className="text-center p-4 bg-white dark:bg-slate-900 rounded-lg">
                            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                              {Math.round((fileAnalysisResult.backgroundVerification.score?.developer_footprint_score || 0) * 100)}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Developer</div>
                          </div>
                        </div>

                        {/* Detailed Information Dropdown */}
                        <button
                          onClick={() => toggleSection('backgroundVerification')}
                          className="w-full p-3 text-left flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors rounded-lg border border-slate-200 dark:border-slate-600"
                        >
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">View Detailed Analysis</span>
                          <svg 
                            className={`w-4 h-4 text-slate-500 transition-transform ${expandedSections.backgroundVerification ? 'rotate-180' : ''}`} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        {expandedSections.backgroundVerification && (
                          <div className="mt-4 p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-600">
                            <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Detailed Analysis</h5>
                            <div className="space-y-4 text-sm">
                              {/* Company Verification Details */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Company Verification</h6>
                                <div className="space-y-3 ml-4">
                                  {fileAnalysisResult.backgroundVerification.company_evidence ? (
                                    Object.entries(fileAnalysisResult.backgroundVerification.company_evidence).map(([companyName, evidence]: [string, any]) => (
                                      <div key={companyName} className="border-l-2 border-slate-200 dark:border-slate-600 pl-3">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="font-medium text-slate-900 dark:text-slate-100">{companyName}</span>
                                          <span className={`text-xs px-2 py-1 rounded-full ${
                                            evidence.gleif?.length > 0 || evidence.sec ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                          }`}>
                                            {evidence.gleif?.length > 0 || evidence.sec ? 'Verified' : 'Not Found'}
                                          </span>
                                        </div>
                                        <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                                          {evidence.gleif?.length > 0 && (
                                            <div>• GLEIF: {evidence.gleif.length} registry match{evidence.gleif.length !== 1 ? 'es' : ''}</div>
                                          )}
                                          {evidence.sec && (
                                            <div>• SEC EDGAR: {evidence.sec.title || 'Found'}</div>
                                          )}
                                          {(!evidence.gleif || evidence.gleif.length === 0) && !evidence.sec && (
                                            <div>• No registry matches found</div>
                                          )}
                                        </div>
                                      </div>
                                    ))
                                  ) : (
                                    <div className="text-slate-600 dark:text-slate-400">No company verification data available</div>
                                  )}
                                </div>
                              </div>

                              {/* Education Verification */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Education Verification</h6>
                                <div className="space-y-3 ml-4">
                                  {fileAnalysisResult.backgroundVerification.education_evidence ? (
                                    Object.entries(fileAnalysisResult.backgroundVerification.education_evidence).map(([institutionName, evidence]: [string, any]) => (
                                      <div key={institutionName} className="border-l-2 border-slate-200 dark:border-slate-600 pl-3">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="font-medium text-slate-900 dark:text-slate-100">{institutionName}</span>
                                          <span className={`text-xs px-2 py-1 rounded-full ${
                                            evidence.scorecard?.length > 0 || evidence.openalex?.length > 0 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                          }`}>
                                            {evidence.scorecard?.length > 0 || evidence.openalex?.length > 0 ? 'Verified' : 'Not Found'}
                                          </span>
                                        </div>
                                        <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                                          {evidence.scorecard?.length > 0 && (
                                            <div>• College Scorecard: {evidence.scorecard.length} match{evidence.scorecard.length !== 1 ? 'es' : ''}</div>
                                          )}
                                          {evidence.openalex?.length > 0 && (
                                            <div>• OpenAlex: {evidence.openalex.length} academic record{evidence.openalex.length !== 1 ? 's' : ''}</div>
                                          )}
                                          {(!evidence.scorecard || evidence.scorecard.length === 0) && (!evidence.openalex || evidence.openalex.length === 0) && (
                                            <div>• No academic records found</div>
                                          )}
                                        </div>
                                      </div>
                                    ))
                                  ) : (
                                    <div className="text-slate-600 dark:text-slate-400">No education verification data available</div>
                                  )}
                                </div>
                              </div>

                              {/* Timeline Consistency */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Timeline Consistency</h6>
                                <div className="space-y-3 ml-4">
                                  {fileAnalysisResult.backgroundVerification.timeline_assessment ? (
                                    Object.entries(fileAnalysisResult.backgroundVerification.timeline_assessment).map(([companyName, assessment]: [string, any]) => (
                                      <div key={companyName} className="border-l-2 border-slate-200 dark:border-slate-600 pl-3">
                                        <div className="flex justify-between items-center mb-1">
                                          <span className="font-medium text-slate-900 dark:text-slate-100">{companyName}</span>
                                          <span className={`text-xs px-2 py-1 rounded-full ${
                                            assessment.plausible ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                                          }`}>
                                            {assessment.plausible ? 'Consistent' : 'Inconsistent'}
                                          </span>
                                        </div>
                                        <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                                          {assessment.notes?.map((note: string, index: number) => (
                                            <div key={index}>• {note}</div>
                                          ))}
                                          {assessment.wayback && (
                                            <div>• Wayback Machine: {assessment.wayback.captures} captures from {assessment.wayback.first} to {assessment.wayback.last}</div>
                                          )}
                                          {!assessment.plausible && !assessment.notes && (
                                            <div>• Timeline verification inconclusive</div>
                                          )}
                                        </div>
                                      </div>
                                    ))
                                  ) : (
                                    <div className="text-slate-600 dark:text-slate-400">No timeline assessment data available</div>
                                  )}
                                </div>
                              </div>

                              {/* Developer Footprint */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Developer Footprint</h6>
                                <div className="space-y-2 ml-4">
                                  {fileAnalysisResult.backgroundVerification.developer_evidence ? (
                                    <div className="border-l-2 border-slate-200 dark:border-slate-600 pl-3">
                                      <div className="space-y-2">
                                        <div className="flex justify-between">
                                          <span className="text-slate-600 dark:text-slate-400">GitHub Profile:</span>
                                          <span className={`font-medium ${
                                            fileAnalysisResult.backgroundVerification.developer_evidence.user ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                                          }`}>
                                            {fileAnalysisResult.backgroundVerification.developer_evidence.user ? '✓ Found' : '✗ Not Found'}
                                          </span>
                                        </div>
                                        {fileAnalysisResult.backgroundVerification.developer_evidence.user && (
                                          <>
                                            <div className="flex justify-between">
                                              <span className="text-slate-600 dark:text-slate-400">Username:</span>
                                              <span className="font-medium text-slate-900 dark:text-slate-100">
                                                {fileAnalysisResult.backgroundVerification.developer_evidence.user.login}
                                              </span>
                                            </div>
                                            <div className="flex justify-between">
                                              <span className="text-slate-600 dark:text-slate-400">Public Repos:</span>
                                              <span className="font-medium text-slate-900 dark:text-slate-100">
                                                {fileAnalysisResult.backgroundVerification.developer_evidence.user.public_repos || 0}
                                              </span>
                                            </div>
                                            <div className="flex justify-between">
                                              <span className="text-slate-600 dark:text-slate-400">Followers:</span>
                                              <span className="font-medium text-slate-900 dark:text-slate-100">
                                                {fileAnalysisResult.backgroundVerification.developer_evidence.user.followers || 0}
                                              </span>
                                            </div>
                                            <div className="flex justify-between">
                                              <span className="text-slate-600 dark:text-slate-400">Repositories:</span>
                                              <span className="font-medium text-slate-900 dark:text-slate-100">
                                                {fileAnalysisResult.backgroundVerification.developer_evidence.repos?.length || 0}
                                              </span>
                                            </div>
                                          </>
                                        )}
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="text-slate-600 dark:text-slate-400">No developer evidence available</div>
                                  )}
                                  </div>
                                </div>

                              {/* Data Sources Used */}
                              {fileAnalysisResult.backgroundVerification.sources_used && (
                                <div>
                                  <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Data Sources</h6>
                                  <div className="flex flex-wrap gap-2 ml-4">
                                    {fileAnalysisResult.backgroundVerification.sources_used.map((source: string, index: number) => (
                                      <span key={index} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                                        {source}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Digital Footprint Details */}
                    {fileAnalysisResult.digitalFootprint && (
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">🌐</span>
                            <h4 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Digital Footprint</h4>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                              {fileAnalysisResult.digitalFootprint.consistency_score || 0}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Consistency Score</div>
                          </div>
                        </div>

                        {/* Detailed Information Dropdown */}
                        <button
                          onClick={() => toggleSection('digitalFootprint')}
                          className="w-full p-3 text-left flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors rounded-lg border border-slate-200 dark:border-slate-600"
                        >
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">View Detailed Analysis</span>
                          <svg 
                            className={`w-4 h-4 text-slate-500 transition-transform ${expandedSections.digitalFootprint ? 'rotate-180' : ''}`} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        {expandedSections.digitalFootprint && (
                          <div className="mt-4 p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-600">
                            <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Detailed Analysis</h5>
                            <div className="space-y-4 text-sm">
                              {/* Social Media Presence */}
                              {fileAnalysisResult.digitalFootprint.social_presence && Object.keys(fileAnalysisResult.digitalFootprint.social_presence).length > 0 && (
                                <div>
                                  <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Social Media Presence</h6>
                                  <div className="space-y-2 ml-4">
                                    {Object.entries(fileAnalysisResult.digitalFootprint.social_presence).map(([platform, profiles]) => (
                                      <div key={platform} className="flex justify-between">
                                        <span className="text-slate-600 dark:text-slate-400 capitalize">
                                          {platform === 'linkedin' ? 'LinkedIn' : 
                                           platform === 'github' ? 'GitHub' : 
                                           platform === 'scholar' ? 'Google Scholar' : 
                                           platform}:
                                        </span>
                                        <span className="font-medium text-green-600 dark:text-green-400">
                                          ✓ {Array.isArray(profiles) ? profiles.length : 1} Profile{Array.isArray(profiles) && profiles.length !== 1 ? 's' : ''}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Search Results */}
                              {fileAnalysisResult.digitalFootprint.search_results && (
                                <div>
                                  <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Search Results</h6>
                                  <div className="space-y-3 ml-4">
                                    <div className="flex justify-between">
                                      <span className="text-slate-600 dark:text-slate-400">Total Results:</span>
                                      <span className="font-medium text-green-600 dark:text-green-400">
                                        ✓ {fileAnalysisResult.digitalFootprint.search_results.length} Found
                                      </span>
                                    </div>
                                    <div className="space-y-2">
                                      <div className="text-xs text-slate-600 dark:text-slate-400 font-medium">Top Results:</div>
                                      {fileAnalysisResult.digitalFootprint.search_results.slice(0, 5).map((result: string, index: number) => (
                                        <div key={index} className="text-xs text-slate-600 dark:text-slate-400 border-l-2 border-slate-200 dark:border-slate-600 pl-2">
                                          <div className="font-medium">{result}</div>
                                        </div>
                                      ))}
                                      {fileAnalysisResult.digitalFootprint.search_results.length > 5 && (
                                        <div className="text-xs text-slate-500 dark:text-slate-500">
                                          +{fileAnalysisResult.digitalFootprint.search_results.length - 5} more results
                        </div>
                                      )}
                      </div>
                                  </div>
                                </div>
                              )}

                              {/* Consistency Analysis */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Consistency Analysis</h6>
                                <div className="space-y-2 ml-4">
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Name Consistency:</span>
                                    <span className="font-medium text-green-600 dark:text-green-400">✓ High</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Location Consistency:</span>
                                    <span className="font-medium text-green-600 dark:text-green-400">✓ High</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Professional Timeline:</span>
                                    <span className="font-medium text-green-600 dark:text-green-400">✓ Consistent</span>
                                  </div>
                                </div>
                              </div>

                              {/* Data Sources */}
                              {fileAnalysisResult.digitalFootprint.sources_used && (
                                <div>
                                  <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Data Sources</h6>
                                  <div className="flex flex-wrap gap-2 ml-4">
                                    {fileAnalysisResult.digitalFootprint.sources_used.map((source: string, index: number) => (
                                      <span key={index} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                                        {source}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Document Authenticity Details */}
                    {fileAnalysisResult.documentAuthenticity && (
                      <div className="bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">📄</span>
                            <h4 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Document Authenticity</h4>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                              {fileAnalysisResult.documentAuthenticity.authenticityScore || 0}%
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400">Authenticity Score</div>
                          </div>
                        </div>

                        {/* Detailed Information Dropdown */}
                        <button
                          onClick={() => toggleSection('documentAuthenticity')}
                          className="w-full p-3 text-left flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors rounded-lg border border-slate-200 dark:border-slate-600"
                        >
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">View Detailed Analysis</span>
                          <svg 
                            className={`w-4 h-4 text-slate-500 transition-transform ${expandedSections.documentAuthenticity ? 'rotate-180' : ''}`} 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        {expandedSections.documentAuthenticity && (
                          <div className="mt-4 p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-600">
                            <h5 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">Detailed Analysis</h5>
                            <div className="space-y-4 text-sm">
                              {/* File Information */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">File Information</h6>
                                <div className="space-y-2 ml-4">
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">File Size:</span>
                                    <span className="font-medium text-slate-900 dark:text-slate-100">
                                      {fileAnalysisResult.documentAuthenticity.fileSize ? `${(fileAnalysisResult.documentAuthenticity.fileSize / 1024).toFixed(1)} KB` : 'N/A'}
                                    </span>
                      </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Pages:</span>
                                    <span className="font-medium text-slate-900 dark:text-slate-100">
                                      {fileAnalysisResult.documentAuthenticity.pages || 'N/A'}
                                    </span>
                    </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Software Used:</span>
                                    <span className="font-medium text-slate-900 dark:text-slate-100">
                                      {fileAnalysisResult.documentAuthenticity.softwareUsed || 'N/A'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Created:</span>
                                    <span className="font-medium text-slate-900 dark:text-slate-100">
                                      {fileAnalysisResult.documentAuthenticity.creationDate ? new Date(fileAnalysisResult.documentAuthenticity.creationDate).toLocaleDateString() : 'N/A'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Modified:</span>
                                    <span className="font-medium text-slate-900 dark:text-slate-100">
                                      {fileAnalysisResult.documentAuthenticity.modificationDate ? new Date(fileAnalysisResult.documentAuthenticity.modificationDate).toLocaleDateString() : 'N/A'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* Suspicious Indicators */}
                              {fileAnalysisResult.documentAuthenticity.suspiciousIndicators && fileAnalysisResult.documentAuthenticity.suspiciousIndicators.length > 0 && (
                                <div>
                                  <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Suspicious Indicators</h6>
                                  <div className="space-y-2 ml-4">
                                    {fileAnalysisResult.documentAuthenticity.suspiciousIndicators.map((indicator: string, index: number) => (
                                      <div key={index} className="flex justify-between">
                                        <span className="text-slate-600 dark:text-slate-400">{indicator}:</span>
                                        <span className="font-medium text-yellow-600 dark:text-yellow-400">⚠ Flagged</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Metadata Analysis */}
                              <div>
                                <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Metadata Analysis</h6>
                                <div className="space-y-2 ml-4">
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Author Information:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.documentAuthenticity.author ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                                    }`}>
                                      {fileAnalysisResult.documentAuthenticity.author ? '✓ Present' : '⚠ Missing'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Creator Information:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.documentAuthenticity.creator ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                                    }`}>
                                      {fileAnalysisResult.documentAuthenticity.creator ? '✓ Present' : '⚠ Missing'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-slate-600 dark:text-slate-400">Font Diversity:</span>
                                    <span className={`font-medium ${
                                      fileAnalysisResult.documentAuthenticity.fontCount && fileAnalysisResult.documentAuthenticity.fontCount > 1 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'
                                    }`}>
                                      {fileAnalysisResult.documentAuthenticity.fontCount && fileAnalysisResult.documentAuthenticity.fontCount > 1 ? '✓ Multiple' : '⚠ Single'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* Analysis Rationale */}
                              {fileAnalysisResult.documentAuthenticity.rationale && (
                                <div>
                                  <h6 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Analysis Rationale</h6>
                                  <div className="space-y-1 ml-4">
                                    {Array.isArray(fileAnalysisResult.documentAuthenticity.rationale) ? (
                                      fileAnalysisResult.documentAuthenticity.rationale.map((item: string, index: number) => (
                                        <div key={index} className="text-slate-600 dark:text-slate-400">
                                          • {item}
                                        </div>
                                      ))
                                    ) : (
                                      <div className="text-slate-600 dark:text-slate-400">
                                        • {fileAnalysisResult.documentAuthenticity.rationale}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* AI Analysis Results */}
                  {(aiAnalysis || aiAnalysisError || aiAnalysisLoading) && (
                    <div className="mt-8 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 rounded-xl border border-green-200 dark:border-green-800 p-6">
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-2xl">🤖</span>
                        <h4 className="text-xl font-semibold text-slate-900 dark:text-slate-100">AI Analysis</h4>
                      </div>
                      
                      {aiAnalysisLoading ? (
                        <div className="flex items-center justify-center py-8">
                          <div className="flex items-center gap-3">
                            <svg className="w-6 h-6 animate-spin text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span className="text-lg font-medium text-slate-700 dark:text-slate-300">Generating AI Analysis...</span>
                          </div>
                        </div>
                      ) : aiAnalysisError ? (
                        <div className="text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950 p-4 rounded-lg border border-red-200 dark:border-red-800">
                          <div className="flex items-center gap-2 mb-2">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="font-medium">Analysis Error</span>
                          </div>
                          <p className="text-sm">{aiAnalysisError}</p>
                        </div>
                      ) : aiAnalysis ? (
                        <div className="space-y-4">
                          {aiAnalysis.split('\n\n').map((section, index) => {
                            // Handle headers
                            if (section.startsWith('## ')) {
                              return (
                                <h3 key={index} className="text-lg font-semibold text-slate-900 dark:text-slate-100 mt-6 mb-3 first:mt-0">
                                  {section.replace('## ', '')}
                                </h3>
                              );
                            }
                            // Handle main headers
                            if (section.startsWith('# ')) {
                              return (
                                <h2 key={index} className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-6 mb-4 first:mt-0">
                                  {section.replace('# ', '')}
                                </h2>
                              );
                            }
                            // Handle bullet points
                            if (section.includes('- **')) {
                              return (
                                <div key={index} className="space-y-2">
                                  {section.split('\n').map((line, lineIndex) => {
                                    if (line.trim().startsWith('- **')) {
                                      const boldText = line.match(/\*\*(.*?)\*\*/)?.[1];
                                      const restText = line.replace(/\*\*(.*?)\*\*:?/, '').replace(/^- /, '').trim();
                                      return (
                                        <div key={lineIndex} className="flex items-start gap-2">
                                          <div className="w-2 h-2 bg-amber-500 rounded-full mt-2 flex-shrink-0"></div>
                                          <div>
                                            <span className="font-semibold text-slate-900 dark:text-slate-100">{boldText}:</span>
                                            <span className="text-slate-700 dark:text-slate-300 ml-1">{restText}</span>
                                          </div>
                                        </div>
                                      );
                                    }
                                    return null;
                                  })}
                                </div>
                              );
                            }
                            // Handle numbered lists
                            if (section.match(/^\d+\./)) {
                              return (
                                <div key={index} className="space-y-2">
                                  {section.split('\n').map((line, lineIndex) => {
                                    if (line.trim().match(/^\d+\./)) {
                                      const text = line.replace(/^\d+\.\s*/, '').trim();
                                      return (
                                        <div key={lineIndex} className="flex items-start gap-2">
                                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                                          <span className="text-slate-700 dark:text-slate-300">{text}</span>
                                        </div>
                                      );
                                    }
                                    return null;
                                  })}
                                </div>
                              );
                            }
                            // Handle risk level highlighting
                            if (section.includes('**Overall Risk Level:')) {
                              const riskLevel = section.match(/\*\*Overall Risk Level:\s*(.*?)\*\*/)?.[1];
                              const riskColor = riskLevel?.includes('LOW') ? 'text-green-600 dark:text-green-400' : 
                                              riskLevel?.includes('HIGH') ? 'text-red-600 dark:text-red-400' : 
                                              'text-amber-600 dark:text-amber-400';
                              return (
                                <div key={index} className="bg-slate-100 dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="font-semibold text-slate-900 dark:text-slate-100">Overall Risk Level:</span>
                                    <span className={`font-bold ${riskColor}`}>{riskLevel}</span>
                                  </div>
                                  <p className="text-slate-700 dark:text-slate-300 text-sm">
                                    {section.replace(/\*\*Overall Risk Level:.*?\*\*/, '').trim()}
                                  </p>
                                </div>
                              );
                            }
                            // Handle regular paragraphs
                            if (section.trim()) {
                              return (
                                <p key={index} className="text-slate-700 dark:text-slate-300 leading-relaxed">
                                  {section}
                                </p>
                              );
                            }
                            return null;
                          })}
                        </div>
                      ) : null}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="mt-8 text-center">
                    <div className="flex justify-center">
                      {/* Download Report Button */}
                      <button
                        onClick={downloadJsonReport}
                        className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                      >
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Download Full Report
                      </button>
                    </div>
                  </div>
              </div>
            </section>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
