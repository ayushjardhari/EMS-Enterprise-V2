import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import StatusBadge from "../components/StatusBadge";
import { useAuth } from "../hooks/useAuth";
import { attendanceService } from "../services/attendanceService";
import { employeeService } from "../services/employeeService";

const formatDate = (value: string) =>
  new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

const money = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);

function Card({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <p className="text-sm text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      {subtitle && (
        <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();

  const employeeId = user?.employee_id;

  const employeeQuery = useQuery({
    queryKey: ["employee-dashboard", employeeId],
    queryFn: () => employeeService.getById(employeeId!),
    enabled: !!employeeId,
  });

  const attendanceQuery = useQuery({
    queryKey: ["employee-dashboard-attendance", employeeId],
    queryFn: () => attendanceService.listForEmployee(employeeId!),
    enabled: !!employeeId,
  });

  const leaveQuery = useQuery({
    queryKey: ["employee-dashboard-leave", employeeId],
    queryFn: () => employeeService.getLeave(employeeId!),
    enabled: !!employeeId,
  });

  if (!employeeId) {
    return (
      <ErrorState
        message="Your account is not linked to an employee profile."
        onRetry={() => window.location.reload()}
      />
    );
  }

  if (employeeQuery.isLoading) {
    return <LoadingState label="Loading your workspace..." />;
  }

  if (employeeQuery.isError || !employeeQuery.data) {
    return (
      <ErrorState
        message="Could not load your employee profile."
        onRetry={employeeQuery.refetch}
      />
    );
  }

  const employee = employeeQuery.data;
  const attendance = attendanceQuery.data ?? [];
  const leave = leaveQuery.data;

  const recentAttendance = [...attendance]
    .sort((a, b) =>
      b.attendance_date.localeCompare(a.attendance_date)
    )
    .slice(0, 5);

  const presentDays = attendance.filter(
    (item) =>
      item.status === "PRESENT" ||
      item.status === "LATE" ||
      item.status === "WORK_FROM_HOME"
  ).length;

  const attendanceRate = attendance.length
    ? Math.round((presentDays / attendance.length) * 100)
    : 0;

  const totalRemainingLeave =
    leave?.balances.reduce(
      (total, balance) => total + balance.remaining_days,
      0
    ) ?? 0;

  const pendingRequests =
    leave?.requests.filter((request) => request.status === "PENDING")
      .length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              My Workspace
            </p>

            <h1 className="mt-2 text-2xl font-semibold text-slate-900">
              Welcome back, {employee.full_name}
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              {employee.job_role.title} · {employee.department.name}
            </p>

            <div className="mt-3 flex flex-wrap gap-2">
              <StatusBadge status={employee.employment_status} />
              <StatusBadge status={employee.availability_status} />
            </div>
          </div>

          <Link
            to={`/employees/${employee.id}`}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            View my profile
          </Link>
        </div>
      </div>

      {/* Personal KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card
          title="Attendance"
          value={`${attendanceRate}%`}
          subtitle="Recorded attendance"
        />

        <Card
          title="Leave remaining"
          value={`${totalRemainingLeave} days`}
          subtitle="Across available leave types"
        />

        <Card
          title="Projects"
          value={employee.projects.length}
          subtitle="Current assignments"
        />

        <Card
          title="Pending leave"
          value={pendingRequests}
          subtitle="Requests awaiting review"
        />
      </div>

      {/* Main workspace */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Attendance */}
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">
                My attendance
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Your latest attendance records.
              </p>
            </div>

            <Link
              to={`/employees/${employee.id}?tab=attendance`}
              className="text-sm font-medium text-slate-700 hover:underline"
            >
              View all
            </Link>
          </div>

          <div className="mt-5 overflow-x-auto">
            {recentAttendance.length === 0 ? (
              <p className="py-6 text-sm text-slate-500">
                No attendance records found.
              </p>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="pb-3">Date</th>
                    <th className="pb-3">Hours</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>

                <tbody>
                  {recentAttendance.map((item) => (
                    <tr
                      key={item.id}
                      className="border-b border-slate-100 last:border-0"
                    >
                      <td className="py-3 font-medium text-slate-900">
                        {formatDate(item.attendance_date)}
                      </td>

                      <td className="py-3 text-slate-600">
                        {item.work_hours == null
                          ? "—"
                          : `${item.work_hours.toFixed(1)}h`}
                      </td>

                      <td className="py-3">
                        <StatusBadge status={item.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* Leave */}
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-slate-900">
                My leave
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Your leave balances and requests.
              </p>
            </div>

            <Link
              to={`/employees/${employee.id}?tab=leave`}
              className="text-sm font-medium text-slate-700 hover:underline"
            >
              Manage
            </Link>
          </div>

          <div className="mt-5 space-y-3">
            {leave?.balances.slice(0, 4).map((balance) => (
              <div
                key={balance.id}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    {balance.type}
                  </p>
                  <p className="text-xs text-slate-500">
                    {balance.used_days} used of {balance.allocated_days}
                  </p>
                </div>

                <strong className="text-sm text-slate-900">
                  {balance.remaining_days} left
                </strong>
              </div>
            ))}

            {!leave?.balances.length && (
              <p className="py-6 text-sm text-slate-500">
                No leave balances found.
              </p>
            )}
          </div>
        </section>
      </div>

      {/* Projects */}
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-slate-900">
              My projects
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Projects you are currently assigned to.
            </p>
          </div>

          <Link
            to="/projects"
            className="text-sm font-medium text-slate-700 hover:underline"
          >
            View projects
          </Link>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {employee.projects.slice(0, 6).map((assignment) => (
            <Link
              key={assignment.id}
              to={`/projects/${assignment.project.id}`}
              className="rounded-lg border border-slate-200 p-4 hover:bg-slate-50"
            >
              <p className="font-medium text-slate-900">
                {assignment.project.project_name}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                {assignment.project_role}
              </p>

              <div className="mt-3">
                <StatusBadge status={assignment.project.status} />
              </div>
            </Link>
          ))}

          {!employee.projects.length && (
            <p className="py-6 text-sm text-slate-500">
              You are not currently assigned to a project.
            </p>
          )}
        </div>
      </section>

      {/* Profile / Skills */}
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-slate-900">
            My skills
          </h2>

          <div className="mt-4 flex flex-wrap gap-2">
            {employee.skills.slice(0, 12).map((skill) => (
              <span
                key={skill.id}
                className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700"
              >
                {skill.skill.name}
              </span>
            ))}

            {!employee.skills.length && (
              <p className="text-sm text-slate-500">
                No skills recorded.
              </p>
            )}
          </div>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-slate-900">
            Employee information
          </h2>

          <div className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-slate-500">Employee ID</span>
              <strong className="text-slate-900">
                {employee.employee_code}
              </strong>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-slate-500">Department</span>
              <strong className="text-slate-900">
                {employee.department.name}
              </strong>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-slate-500">Role</span>
              <strong className="text-slate-900">
                {employee.job_role.title}
              </strong>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-slate-500">Joined</span>
              <strong className="text-slate-900">
                {formatDate(employee.joining_date)}
              </strong>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}