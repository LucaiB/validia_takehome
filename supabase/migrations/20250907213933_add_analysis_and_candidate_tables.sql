BEGIN;

-- Candidates table
CREATE TABLE IF NOT EXISTS public.candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  full_name text NOT NULL,
  email text NOT NULL,
  phone text,
  UNIQUE(email)
);

-- Analyses table stores each analysis run for a candidate
CREATE TABLE IF NOT EXISTS public.analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  candidate_id uuid NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
  overall_score integer NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
  report jsonb NOT NULL,
  ai_detection jsonb,
  contact_verification jsonb
);

-- Review history table for audit trail per candidate/analysis
CREATE TABLE IF NOT EXISTS public.review_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  candidate_id uuid NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
  analysis_id uuid REFERENCES public.analyses(id) ON DELETE SET NULL,
  action text NOT NULL, -- e.g., "created", "updated", "approved", "rejected"
  notes text,
  snapshot jsonb -- optional snapshot of report at time of action
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_analyses_candidate_id ON public.analyses(candidate_id);
CREATE INDEX IF NOT EXISTS idx_review_history_candidate_id ON public.review_history(candidate_id);
CREATE INDEX IF NOT EXISTS idx_review_history_analysis_id ON public.review_history(analysis_id);

-- Trigger to keep updated_at fresh
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_candidates_updated_at ON public.candidates;
CREATE TRIGGER trg_candidates_updated_at
BEFORE UPDATE ON public.candidates
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

COMMIT;