import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import StatusBadge from "../components/StatusBadge";
import { ApiError } from "../services/api";
import { departmentService } from "../services/departmentService";
import { jobRoleService } from "../services/jobRoleService";
import { matchingService } from "../services/matchingService";
import type { AvailabilityStatus } from "../types";
import type { CandidateMatch, ExplainMode, MatchRequestPayload } from "../types/matching";

const EXAMPLES = [
  "We need engineers to run production workloads on Kubernetes clusters and manage infrastructure as code.",
  "Build an assistant that answers employee questions from policy documents using large language models.",
  "Create executive dashboards and KPI reports for revenue and churn.",
  "Cross-platform mobile app for field technicians that keeps working without network.",
];

const AVAILABILITY_OPTIONS: Record<string, AvailabilityStatus[] | undefined> = {
  any: undefined,
  available: ["AVAILABLE"],
  can_start: ["AVAILABLE", "PARTIALLY_AVAILABLE"],
};

const BREAKDOWN_LABELS: [keyof CandidateMatch["breakdown"], string][] = [
  ["semantic", "Resume match"],
  ["skill", "Skills"],
  ["experience", "Experience"],
  ["availability", "Availability"],
];

function Bar({ value }: { value: number }) {
  return (
    <div className="track" aria-hidden="true">
      <i style={{ width: `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%` }} />
    </div>
  );
}

function CandidateCard({ candidate }: { candidate: CandidateMatch }) {
  const { explanation } = candidate;
  return (
    <article className="card staffing-card">
      <div className="staffing-card-head">
        <div className="staffing-rank">{candidate.rank}</div>
        <div className="staffing-who">
          <Link to={`/employees/${candidate.employee_id}`}>{candidate.full_name}</Link>
          <span>
            {candidate.job_role} · {candidate.department} · {candidate.employee_code}
          </span>
        </div>
        <StatusBadge status={candidate.availability_status} />
        <div className="staffing-score" title="Relative to the people compared in this search, not an absolute probability">
          <b>{Math.round(candidate.score * 100)}</b>
          <small>match score</small>
        </div>
      </div>

      <div className="staffing-breakdown">
        {BREAKDOWN_LABELS.map(([key, label]) => (
          <div key={key}>
            <div className="staffing-breakdown-row">
              <span>{label}</span>
              <b>{Math.round(candidate.breakdown[key] * 100)}</b>
            </div>
            <Bar value={candidate.breakdown[key]} />
          </div>
        ))}
      </div>

      {candidate.matched_skills.length > 0 && (
        <div className="staffing-skills">
          {candidate.matched_skills.map((s) => (
            <span key={s.name}>
              {s.name}
              <small>
                {s.proficiency.toLowerCase()} · {s.years} yrs
              </small>
            </span>
          ))}
        </div>
      )}

      {explanation && (
        <div className="staffing-explain">
          <div className="staffing-explain-head">
            <b>Why this match</b>
            <span className={`staffing-source ${explanation.source}`}>
              {explanation.source === "llm" ? "AI-written" : "Generated from record"}
            </span>
          </div>
          <p>{explanation.text}</p>
          {explanation.fallback_reason && (
            <small className="staffing-note">AI explanation unavailable ({explanation.fallback_reason}); showing the record-based summary.</small>
          )}
        </div>
      )}

      {candidate.evidence.length > 0 && (
        <details className="staffing-evidence">
          <summary>Resume evidence ({candidate.evidence.length})</summary>
          {candidate.evidence.map((e, i) => (
            <blockquote key={`${e.document_id}-${i}`}>
              <small>
                [E{i + 1}] {e.section} section · similarity {e.similarity.toFixed(2)}
              </small>
              <p>{e.content}</p>
            </blockquote>
          ))}
        </details>
      )}
    </article>
  );
}

export default function StaffingPage() {
  const [requirement, setRequirement] = useState("");
  const [availability, setAvailability] = useState("any");
  const [departmentId, setDepartmentId] = useState("");
  const [roleId, setRoleId] = useState("");
  const [topK, setTopK] = useState(5);
  const [explain, setExplain] = useState<ExplainMode>("template");

  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: () => departmentService.list() });
  const { data: roles } = useQuery({ queryKey: ["job-roles"], queryFn: () => jobRoleService.list() });

  const search = useMutation({ mutationFn: matchingService.search });

  const tooShort = requirement.trim().length < 10;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (tooShort) return;
    const payload: MatchRequestPayload = {
      requirement: requirement.trim(),
      top_k: topK,
      filters: {
        availability: AVAILABILITY_OPTIONS[availability],
        department_ids: departmentId ? [departmentId] : undefined,
        job_role_ids: roleId ? [roleId] : undefined,
      },
      explain,
      explain_top_n: Math.min(3, topK),
    };
    search.mutate(payload);
  };

  const errorMessage =
    search.error instanceof ApiError
      ? search.error.status === 403
        ? "You do not have permission to search for candidates."
        : search.error.message
      : search.error
        ? "Could not reach the server."
        : "";

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="eyebrow">TALENT MATCHING</div>
          <h1>Find the right people for a project</h1>
          <p>Describe what the project needs. Candidates are ranked using resume evidence, recorded skills, experience and availability.</p>
        </div>
      </div>

      <form className="card section staffing-form" onSubmit={submit}>
        <label htmlFor="requirement">Project requirement</label>
        <textarea
          id="requirement"
          rows={4}
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          placeholder="e.g. We need engineers who have run production workloads on Kubernetes clusters…"
          maxLength={4000}
        />
        <div className="staffing-examples">
          <span>Try:</span>
          {EXAMPLES.map((text) => (
            <button type="button" key={text} onClick={() => setRequirement(text)}>
              {text.length > 54 ? `${text.slice(0, 54)}…` : text}
            </button>
          ))}
        </div>

        <div className="filters">
          <select aria-label="Availability" value={availability} onChange={(e) => setAvailability(e.target.value)}>
            <option value="any">Any availability</option>
            <option value="available">Available only</option>
            <option value="can_start">Available or partly available</option>
          </select>
          <select aria-label="Department" value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">All departments</option>
            {departments?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select aria-label="Job role" value={roleId} onChange={(e) => setRoleId(e.target.value)}>
            <option value="">All job roles</option>
            {roles?.map((r) => (
              <option key={r.id} value={r.id}>
                {r.title}
              </option>
            ))}
          </select>
          <select aria-label="Number of candidates" value={topK} onChange={(e) => setTopK(Number(e.target.value))}>
            {[3, 5, 10].map((n) => (
              <option key={n} value={n}>
                Top {n}
              </option>
            ))}
          </select>
          <select aria-label="Explanations" value={explain} onChange={(e) => setExplain(e.target.value as ExplainMode)}>
            <option value="none">No explanations</option>
            <option value="template">Explanations from record</option>
            <option value="llm">AI-written explanations</option>
          </select>
          <button type="submit" className="btn primary" disabled={tooShort || search.isPending}>
            {search.isPending ? "Searching…" : "Find candidates"}
          </button>
        </div>
        {requirement.length > 0 && tooShort && <small className="staffing-note">Describe the requirement in at least 10 characters.</small>}
      </form>

      {search.isPending && <LoadingState label="Ranking candidates…" />}
      {search.isError && <ErrorState message={errorMessage} onRetry={() => search.mutate(search.variables!)} />}

      {search.data && !search.isPending && (
        <section className="staffing-results">
          <div className="section-head">
            <div>
              <h2>
                {search.data.results.length === 0
                  ? "No candidates found"
                  : `Top ${search.data.results.length} of ${search.data.candidates_considered} people considered`}
              </h2>
              <p>Scores are relative to the people compared in this search. They help order candidates and are not absolute probabilities.</p>
            </div>
          </div>
          {search.data.results.length === 0 ? (
            <div className="empty-panel">No active employees match these filters. Try widening the availability, department or role filter.</div>
          ) : (
            <div className="staffing-list">
              {search.data.results.map((c) => (
                <CandidateCard key={c.employee_id} candidate={c} />
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
