import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import StatusBadge from "../components/StatusBadge";
import Table, { type Column } from "../components/Table";
import { useAuth } from "../hooks/useAuth";
import { attendanceService } from "../services/attendanceService";
import type { Attendance } from "../types";

function formatTime(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function AttendancePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
  const isEmployee = user?.user_role === "EMPLOYEE";

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["attendance", user?.id],
    queryFn: attendanceService.list,
  });

  const today = data?.find((r) => r.attendance_date === new Date().toISOString().slice(0, 10));

  const runAction = async (action: () => Promise<Attendance>) => {
    setActionError(null);
    try {
      await action();
      await queryClient.invalidateQueries({ queryKey: ["attendance"] });
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Could not update attendance.");
    }
  };

  const columns: Column<Attendance>[] = [
    { header: "Date", render: (r) => r.attendance_date },
    { header: "Check in", render: (r) => formatTime(r.check_in) },
    { header: "Check out", render: (r) => formatTime(r.check_out) },
    { header: "Hours", render: (r) => r.work_hours != null ? `${r.work_hours.toFixed(2)}h` : "—" },
    { header: "Status", render: (r) => <StatusBadge status={r.status} /> },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">Workforce operations</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-gray-950">Attendance</h1>
          <p className="mt-1 text-sm text-gray-500">Track daily presence, working hours, and attendance history.</p>
        </div>
        {isEmployee && (
          <div className="flex gap-2">
            <button disabled={!!today?.check_in} onClick={() => runAction(attendanceService.checkIn)} className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50">Check in</button>
            <button disabled={!today?.check_in || !!today?.check_out} onClick={() => runAction(attendanceService.checkOut)} className="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50">Check out</button>
          </div>
        )}
      </div>

      {actionError && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{actionError}</div>}

      {isEmployee && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><p className="text-xs font-medium uppercase tracking-wide text-gray-500">Today</p><p className="mt-2 text-xl font-semibold">{today?.status ?? "Not recorded"}</p></div>
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><p className="text-xs font-medium uppercase tracking-wide text-gray-500">Check in</p><p className="mt-2 text-xl font-semibold">{formatTime(today?.check_in ?? null)}</p></div>
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"><p className="text-xs font-medium uppercase tracking-wide text-gray-500">Hours</p><p className="mt-2 text-xl font-semibold">{today?.work_hours != null ? `${today.work_hours.toFixed(2)}h` : "—"}</p></div>
        </div>
      )}

      {isLoading && <LoadingState label="Loading attendance..." />}
      {isError && <ErrorState message="Could not load attendance." onRetry={refetch} />}
      {data && <Table columns={columns} rows={data} keyExtractor={(r) => r.id} emptyMessage="No attendance records yet." />}
    </div>
  );
}
