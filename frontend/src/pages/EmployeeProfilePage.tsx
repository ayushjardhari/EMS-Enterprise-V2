import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { type ReactNode } from "react";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../hooks/useAuth";
import { attendanceService } from "../services/attendanceService";
import { ApiError } from "../services/api";
import { employeeService } from "../services/employeeService";

import type {
  Attendance,
  EmployeeActivity,
  EmployeeLeave,
  EmployeePayroll,
} from "../types";

const tabs = [
  ["overview", "Overview"],
  ["attendance", "Attendance"],
  ["leave", "Leave"],
  ["payroll", "Payroll"],
  ["projects", "Projects"],
  ["skills", "Skills"],
  ["documents", "Documents"],
  ["activity", "Activity"],
] as const;

type Tab = (typeof tabs)[number][0];

const money = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);

const formatDate = (value: string) =>
  new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

const formatDateTime = (value: string | null) =>
  value
    ? new Date(value).toLocaleString(undefined, {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";

const initials = (name: string) =>
  name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

function Section({
  title,
  subtitle,
  meta,
  children,
}: {
  title: string;
  subtitle?: string;
  meta?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card section">
      <div className="section-head">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>

        {meta && <span className="section-meta">{meta}</span>}
      </div>

      {children}
    </section>
  );
}

function ActivityTimeline({
  rows,
  compact = false,
}: {
  rows: EmployeeActivity[];
  compact?: boolean;
}) {
  if (!rows.length) {
    return (
      <div className="empty-panel">
        No audit activity recorded for this employee yet.
      </div>
    );
  }

  const visibleRows = compact ? rows.slice(0, 5) : rows;

  return (
    <div className="timeline">
      {visibleRows.map((item) => (
        <div className="timeline-item" key={item.id}>
          <div className="timeline-dot" />

          <div className="timeline-content">
            <div>
              <b>
                {item.action} · {item.entity_type.replaceAll("_", " ")}
              </b>

              <time>
                {new Date(item.created_at).toLocaleDateString(undefined, {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                })}
              </time>
            </div>

            <p>{item.details || "System event recorded."}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function AttendancePanel({ rows }: { rows: Attendance[] }) {
  const present = rows.filter((x) => x.status === "PRESENT").length;
  const late = rows.filter((x) => x.status === "LATE").length;
  const wfh = rows.filter((x) => x.status === "WORK_FROM_HOME").length;
  const absent = rows.filter((x) => x.status === "ABSENT").length;

  const total = rows.length;

  const attendanceRate = total
    ? Math.round(((present + late + wfh) / total) * 100)
    : 0;

  const sorted = [...rows].sort((a, b) =>
    b.attendance_date.localeCompare(a.attendance_date)
  );

  return (
    <div className="profile-grid profile-grid-wide">
      <Section
        title="Attendance overview"
        subtitle="Recorded attendance for this employee."
        meta={`${total} records`}
      >
        <div className="profile-kpis">
          <div>
            <b>{attendanceRate}%</b>
            <span>Attendance rate</span>
          </div>

          <div>
            <b>{present}</b>
            <span>Present</span>
          </div>

          <div>
            <b>{late}</b>
            <span>Late</span>
          </div>

          <div>
            <b>{wfh}</b>
            <span>WFH</span>
          </div>

          <div>
            <b>{absent}</b>
            <span>Absent</span>
          </div>
        </div>

        <div className="profile-progress">
          <div>
            <span>Presence rate</span>
            <b>{attendanceRate}%</b>
          </div>

          <div className="track">
            <i style={{ width: `${attendanceRate}%` }} />
          </div>
        </div>
      </Section>

      <Section
        title="Attendance history"
        subtitle="Latest recorded working days."
      >
        {!sorted.length ? (
          <div className="empty-panel">No attendance records.</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Check in</th>
                  <th>Check out</th>
                  <th>Hours</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {sorted.slice(0, 31).map((item) => (
                  <tr key={item.id}>
                    <td>
                      <b>{formatDate(item.attendance_date)}</b>
                    </td>

                    <td>{formatDateTime(item.check_in)}</td>
                    <td>{formatDateTime(item.check_out)}</td>

                    <td>
                      {item.work_hours == null
                        ? "—"
                        : `${item.work_hours.toFixed(1)}h`}
                    </td>

                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

function LeavePanel({
  data,
  employeeId,
}: {
  data: EmployeeLeave;
  employeeId: string;
}) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [leaveTypeId, setLeaveTypeId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const leaveTypesQuery = useQuery({
    queryKey: ["leave-types"],
    queryFn: () => employeeService.listLeaveTypes(),
  });

  async function submitRequest() {
    if (!leaveTypeId || !startDate || !endDate) {
      setError("Leave type, start date and end date are required.");
      return;
    }

    if (endDate < startDate) {
      setError("End date cannot be before start date.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      await employeeService.createLeaveRequest({
        leave_type_id: leaveTypeId,
        start_date: startDate,
        end_date: endDate,
        reason: reason || undefined,
      });

      await queryClient.invalidateQueries({
        queryKey: ["employee-leave", employeeId],
      });

      setShowForm(false);
      setLeaveTypeId("");
      setStartDate("");
      setEndDate("");
      setReason("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to submit leave request."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">
            Leave balances
          </h3>

          <button
            type="button"
            onClick={() => setShowForm((value) => !value)}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            {showForm ? "Close" : "Request leave"}
          </button>
        </div>
      

      <Section title="Leave balances">
        <div className="grid gap-4 md:grid-cols-3">
          {data.balances.map((balance) => (
            <div
              key={balance.id}
              className="rounded-xl border border-slate-200 bg-white p-5"
            >
              <div className="text-sm font-medium text-slate-500">
                {balance.type}
              </div>

              <div className="mt-2 text-2xl font-semibold text-slate-900">
                {balance.remaining_days}
              </div>

              <div className="mt-1 text-xs text-slate-500">
                {balance.used_days} used · {balance.allocated_days} allocated
              </div>

              <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-slate-900"
                  style={{
                    width: `${
                      balance.allocated_days > 0
                        ? Math.min(
                            (balance.used_days / balance.allocated_days) * 100,
                            100
                          )
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </Section>
    </div>

      {showForm && (
        <Section title="New leave request">
          <div className="grid gap-5 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">
                Leave type
              </span>

              <select
                value={leaveTypeId}
                onChange={(event) => setLeaveTypeId(event.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-slate-500"
              >
                <option value="">Select leave type</option>

                {leaveTypesQuery.data?.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            </label>

            <div />

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">
                Start date
              </span>

              <input
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">
                End date
              </span>

              <input
                type="date"
                value={endDate}
                min={startDate || undefined}
                onChange={(event) => setEndDate(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500"
              />
            </label>

            <label className="block md:col-span-2">
              <span className="mb-2 block text-sm font-medium text-slate-700">
                Reason
              </span>

              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={4}
                placeholder="Enter the reason for your leave..."
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500"
              />
            </label>
          </div>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mt-5 flex justify-end">
            <button
              type="button"
              disabled={submitting}
              onClick={submitRequest}
              className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Submit request"}
            </button>
          </div>
        </Section>
      )}

      <Section title="Leave request history">
        {data.requests.length === 0 ? (
          <div className="py-8 text-center text-sm text-slate-500">
            No leave requests found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Dates</th>
                  <th className="px-4 py-3">Days</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>

              <tbody>
                {data.requests.map((request) => (
                  <tr
                    key={request.id}
                    className="border-b border-slate-100 last:border-0"
                  >
                    <td className="px-4 py-4 font-medium text-slate-900">
                      {request.type}
                    </td>

                    <td className="px-4 py-4 text-slate-600">
                      {request.start_date} → {request.end_date}
                    </td>

                    <td className="px-4 py-4 text-slate-600">
                      {request.days}
                    </td>

                    <td className="max-w-xs px-4 py-4 text-slate-600">
                      {request.reason || "—"}
                    </td>

                    <td className="px-4 py-4">
                      <StatusBadge status={request.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

function PayrollPanel({
  data,
  allowed,
}: {
  data: EmployeePayroll | undefined;
  allowed: boolean;
}) {
  if (!allowed) {
    return (
      <Section
        title="Payroll"
        subtitle="Restricted compensation information."
      >
        <div className="empty-panel">
          Payroll details are restricted to authorized roles and the
          employee themselves.
        </div>
      </Section>
    );
  }

  if (!data) {
    return <LoadingState label="Loading payroll..." />;
  }

  const salary = data.salary;
  const latest = data.records[0];

  return (
    <div className="profile-grid">
      <Section
        title="Current salary structure"
        subtitle="Effective compensation profile."
      >
        {!salary ? (
          <div className="empty-panel">
            No salary profile recorded.
          </div>
        ) : (
          <div className="profile-info-grid">
            <div>
              <span>Basic salary</span>
              <b>{money(salary.basic_salary)}</b>
            </div>

            <div>
              <span>Housing allowance</span>
              <b>{money(salary.housing_allowance)}</b>
            </div>

            <div>
              <span>Transport allowance</span>
              <b>{money(salary.transport_allowance)}</b>
            </div>

            <div>
              <span>Other allowance</span>
              <b>{money(salary.other_allowance)}</b>
            </div>

            <div>
              <span>Effective from</span>
              <b>{formatDate(salary.effective_from)}</b>
            </div>

            <div>
              <span>Monthly gross</span>
              <b>
                {money(
                  salary.basic_salary +
                    salary.housing_allowance +
                    salary.transport_allowance +
                    salary.other_allowance
                )}
              </b>
            </div>
          </div>
        )}
      </Section>

      <Section
        title="Latest payroll"
        subtitle={
          latest
            ? `Latest processed period · ${latest.period}`
            : "No payroll history."
        }
      >
        {!latest ? (
          <div className="empty-panel">
            No payroll records.
          </div>
        ) : (
          <div className="profile-kpis">
            <div>
              <b>{money(latest.gross)}</b>
              <span>Gross</span>
            </div>

            <div>
              <b>{money(latest.deductions)}</b>
              <span>Deductions</span>
            </div>

            <div>
              <b>{money(latest.net)}</b>
              <span>Net pay</span>
            </div>
          </div>
        )}
      </Section>

      <Section
        title="Payroll history"
        subtitle="Processed payroll records."
        meta={`${data.records.length} periods`}
      >
        {!data.records.length ? (
          <div className="empty-panel">
            No payroll records.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Gross</th>
                  <th>Bonus</th>
                  <th>Deductions</th>
                  <th>Net</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {data.records.map((record) => (
                  <tr key={record.id}>
                    <td>
                      <b>{record.period}</b>
                    </td>

                    <td>{money(record.gross)}</td>
                    <td>{money(record.bonus)}</td>
                    <td>{money(record.deductions)}</td>

                    <td>
                      <b>{money(record.net)}</b>
                    </td>

                    <td>
                      <StatusBadge status={record.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

export default function EmployeeProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploadError, setUploadError] = useState<string | null>(null);

  const rawTab = searchParams.get("tab") as Tab | null;

  const activeTab: Tab = tabs.some(([value]) => value === rawTab)
    ? rawTab!
    : "overview";

  const isAdminOrHr =
    user?.user_role === "ADMIN" || user?.user_role === "HR";

  const isOwnProfile = user?.employee_id === id;

  const canViewPayroll = isAdminOrHr || isOwnProfile;

  const employeeQuery = useQuery({
    queryKey: ["employee", id],
    queryFn: () => employeeService.getById(id!),
    enabled: !!id,
  });

  const documentsQuery = useQuery({
    queryKey: ["employee-documents", id],
    queryFn: () => employeeService.listDocuments(id!),
    enabled: !!id,
  });

  const attendanceQuery = useQuery({
    queryKey: ["employee-attendance", id],
    queryFn: () => attendanceService.listForEmployee(id!),
    enabled: !!id,
  });

  const leaveQuery = useQuery({
    queryKey: ["employee-leave", id],
    queryFn: () => employeeService.getLeave(id!),
    enabled: !!id,
  });

  const payrollQuery = useQuery({
    queryKey: ["employee-payroll", id],
    queryFn: () => employeeService.getPayroll(id!),
    enabled: !!id && canViewPayroll,
  });

  const activityQuery = useQuery({
    queryKey: ["employee-activity", id],
    queryFn: () => employeeService.getActivity(id!),
    enabled: !!id,
  });

  if (employeeQuery.isLoading) {
    return <LoadingState label="Loading employee workspace..." />;
  }

  if (employeeQuery.isError || !employeeQuery.data) {
    return (
      <ErrorState
        message="Could not load this employee."
        onRetry={employeeQuery.refetch}
      />
    );
  }

  const employee = employeeQuery.data;

  const selectTab = (tab: Tab) => {
    setSearchParams({ tab });
  };

  const handleUpload = async (file: File) => {
    setUploadError(null);

    try {
      await employeeService.uploadDocument(id!, file);
      await documentsQuery.refetch();
    } catch (error) {
      setUploadError(
        error instanceof ApiError
          ? error.message
          : "Document upload failed."
      );
    }
  };

  const handleDeactivate = async () => {
    await employeeService.setStatus(id!, "INACTIVE");

    await queryClient.invalidateQueries({
      queryKey: ["employee", id],
    });
  };

  return (
    <div className="employee-workspace">
      <div className="profile-hero card">
        <div className="profile-identity">
          <div className="profile-avatar">
            {initials(employee.full_name)}
          </div>

          <div>
            <div className="eyebrow">EMPLOYEE 360</div>

            <h1>{employee.full_name}</h1>

            <p>
              {employee.job_role.title} · {employee.department.name} ·{" "}
              {employee.employee_code}
            </p>

            <div className="profile-statuses">
              <StatusBadge status={employee.employment_status} />
              <StatusBadge status={employee.availability_status} />
            </div>
          </div>
        </div>

        {isAdminOrHr && (
          <div className="head-actions">
            <Link
              to={`/employees/${employee.id}/edit`}
              className="btn"
            >
              Edit profile
            </Link>

            {employee.employment_status !== "INACTIVE" && (
              <button
                onClick={handleDeactivate}
                className="btn danger"
              >
                Deactivate
              </button>
            )}
          </div>
        )}
      </div>

      <nav className="profile-tabs" aria-label="Employee sections">
        {tabs.map(([value, label]) => (
          <button
            key={value}
            className={
              activeTab === value
                ? "profile-tab active"
                : "profile-tab"
            }
            onClick={() => selectTab(value)}
          >
            {label}

            {value === "documents" &&
              documentsQuery.data?.length ? (
              <span>{documentsQuery.data.length}</span>
            ) : null}
          </button>
        ))}
      </nav>

      {activeTab === "overview" && (
        <div className="profile-grid">
          <Section
            title="Employment overview"
            subtitle="Core identity and employment information."
          >
            <div className="profile-info-grid">
              <div>
                <span>Email</span>
                <b>{employee.email}</b>
              </div>

              <div>
                <span>Phone</span>
                <b>{employee.phone || "Not provided"}</b>
              </div>

              <div>
                <span>Location</span>
                <b>{employee.location || "Not provided"}</b>
              </div>

              <div>
                <span>Department</span>
                <b>{employee.department.name}</b>
              </div>

              <div>
                <span>Job role</span>
                <b>{employee.job_role.title}</b>
              </div>

              <div>
                <span>Joined</span>
                <b>{formatDate(employee.joining_date)}</b>
              </div>
            </div>

            {employee.profile_info && (
              <div className="profile-bio">
                <span>Profile</span>
                <p>{employee.profile_info}</p>
              </div>
            )}
          </Section>

          <Section
            title="Workforce snapshot"
            subtitle="Current employee state."
          >
            <div className="snapshot-list">
              <div>
                <span>Employment</span>
                <b>
                  <StatusBadge status={employee.employment_status} />
                </b>
              </div>

              <div>
                <span>Availability</span>
                <b>
                  <StatusBadge status={employee.availability_status} />
                </b>
              </div>

              <div>
                <span>Projects</span>
                <b>{employee.projects.length}</b>
              </div>

              <div>
                <span>Skills</span>
                <b>{employee.skills.length}</b>
              </div>

              <div>
                <span>Documents</span>
                <b>{documentsQuery.data?.length ?? 0}</b>
              </div>
            </div>
          </Section>

          <Section
            title="Capabilities"
            subtitle="Structured skills for staffing and future matching."
            meta={`${employee.skills.length} skills`}
          >
            {!employee.skills.length ? (
              <div className="empty-panel">
                No skills recorded.
              </div>
            ) : (
              <div className="skill-list">
                {employee.skills.slice(0, 8).map((skill) => (
                  <span key={skill.id}>
                    {skill.skill.name}

                    <small>
                      {skill.proficiency_level.toLowerCase()} ·{" "}
                      {skill.years_of_experience}y
                    </small>
                  </span>
                ))}
              </div>
            )}
          </Section>

          <Section
            title="Recent activity"
            subtitle="Auditable employee events."
          >
            <ActivityTimeline
              rows={activityQuery.data ?? []}
              compact
            />
          </Section>
        </div>
      )}

      {activeTab === "attendance" &&
        (attendanceQuery.isLoading ? (
          <LoadingState label="Loading attendance..." />
        ) : (
          <AttendancePanel rows={attendanceQuery.data ?? []} />
        ))}

      {activeTab === "leave" && (
        leaveQuery.data ? (
          <LeavePanel data={leaveQuery.data} employeeId={id!} />
        ) : (
          <Section title="Leave">
            <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
              Loading leave information...
            </div>
          </Section>
        )
      )}

      {activeTab === "payroll" && (
        <PayrollPanel
          data={payrollQuery.data}
          allowed={canViewPayroll}
        />
      )}

      {activeTab === "projects" && (
        <Section
          title="Project assignments"
          subtitle="Current and historical project associations."
          meta={`${employee.projects.length} assignments`}
        >
          {!employee.projects.length ? (
            <div className="empty-panel">
              No project assignments yet.
            </div>
          ) : (
            <div className="project-list">
              {employee.projects.map((project) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.project.id}`}
                >
                  <div>
                    <b>{project.project.project_name}</b>
                    <span>{project.project_role}</span>
                  </div>

                  <div className="project-meta">
                    <StatusBadge
                      status={project.project.status}
                    />

                    <small>
                      {formatDate(project.start_date)} →{" "}
                      {project.end_date
                        ? formatDate(project.end_date)
                        : "Ongoing"}
                    </small>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Section>
      )}

      {activeTab === "skills" && (
        <Section
          title="Skills & capabilities"
          subtitle="Structured capability inventory."
          meta={`${employee.skills.length} skills`}
        >
          {!employee.skills.length ? (
            <div className="empty-panel">
              No skills recorded.
            </div>
          ) : (
            <div className="skill-detail-grid">
              {employee.skills.map((skill) => (
                <div key={skill.id}>
                  <div className="skill-title">
                    <b>{skill.skill.name}</b>
                    <StatusBadge
                      status={skill.proficiency_level}
                    />
                  </div>

                  <span>
                    {skill.skill.category ||
                      "General capability"}
                  </span>

                  <strong>
                    {skill.years_of_experience.toFixed(1)} years
                    experience
                  </strong>
                </div>
              ))}
            </div>
          )}
        </Section>
      )}

      {activeTab === "documents" && (
        <Section
          title="Documents"
          subtitle="Employee records stored in secure document storage."
          meta={`${documentsQuery.data?.length ?? 0} documents`}
        >
          <div
            className="section-head"
            style={{ marginBottom: 12 }}
          >
            <div />

            <div>
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(event) => {
                  const file = event.target.files?.[0];

                  if (file) {
                    handleUpload(file);
                  }
                }}
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn primary"
              >
                Upload document
              </button>
            </div>
          </div>

          {uploadError && (
            <p className="upload-error">{uploadError}</p>
          )}

          {!documentsQuery.data?.length ? (
            <div className="empty-panel">
              No documents uploaded yet.
            </div>
          ) : (
            <div className="document-list">
              {documentsQuery.data.map((document) => (
                <div key={document.id}>
                  <div className="doc-icon">
                    {document.file_type
                      .slice(0, 4)
                      .toUpperCase()}
                  </div>

                  <div>
                    <b>{document.filename}</b>

                    <span>
                      {document.file_type.toUpperCase()} ·{" "}
                      {new Date(
                        document.uploaded_at
                      ).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="doc-actions">
                    <StatusBadge
                      status={document.extraction_status}
                    />

                    {isAdminOrHr && (
                      <button
                        onClick={async () => {
                          await employeeService.deleteDocument(
                            document.id
                          );

                          await documentsQuery.refetch();
                        }}
                        className="text-danger"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>
      )}

      {activeTab === "activity" && (
        <Section
          title="Activity timeline"
          subtitle="Auditable employee events."
          meta={`${activityQuery.data?.length ?? 0} events`}
        >
          <ActivityTimeline rows={activityQuery.data ?? []} />
        </Section>
      )}
    </div>
  );
}