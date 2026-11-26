import type { AvailabilityStatus } from "./index";

export type ExplainMode = "none" | "template" | "llm";

export interface MatchRequestPayload {
  requirement: string;
  top_k: number;
  filters: {
    availability?: AvailabilityStatus[];
    department_ids?: string[];
    job_role_ids?: string[];
  };
  explain: ExplainMode;
  explain_top_n: number;
}

export interface EvidenceChunk {
  document_id: string;
  section: string;
  content: string;
  similarity: number;
}

export interface MatchedSkill {
  name: string;
  proficiency: string;
  years: number;
  relevance: number;
}

export interface ScoreBreakdown {
  semantic: number;
  skill: number;
  experience: number;
  availability: number;
}

export interface CandidateExplanation {
  text: string;
  source: "llm" | "template";
  model: string | null;
  fallback_reason: string | null;
}

export interface CandidateMatch {
  rank: number;
  employee_id: string;
  employee_code: string;
  full_name: string;
  job_role: string;
  department: string;
  availability_status: AvailabilityStatus;
  score: number;
  breakdown: ScoreBreakdown;
  matched_skills: MatchedSkill[];
  evidence: EvidenceChunk[];
  explanation: CandidateExplanation | null;
}

export interface MatchResponse {
  requirement: string;
  candidates_considered: number;
  results: CandidateMatch[];
}
