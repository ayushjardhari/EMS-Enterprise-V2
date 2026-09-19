import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import FilterSelect from "../components/FilterSelect";
import LoadingState from "../components/LoadingState";
import SearchBar from "../components/SearchBar";
import StatusBadge from "../components/StatusBadge";
import Table, { type Column } from "../components/Table";
import { useAuth } from "../hooks/useAuth";
import { departmentService } from "../services/departmentService";
import { employeeService } from "../services/employeeService";
import type { EmployeeListItem } from "../types";

const EMPLOYMENT_STATUS_OPTIONS = [
  { value: "ACTIVE", label: "Active" },
  { value: "INACTIVE", label: "Inactive" },
  { value: "ON_LEAVE", label: "On leave" },
];

export default function EmployeeListPage() {
  const { user } = useAuth();
  const canManage = user?.user_role === "ADMIN" || user?.user_role === "HR";

  const [search, setSearch] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [employmentStatus, setEmploymentStatus] = useState("");
  const [page, setPage] = useState(1);
  const limit = 10;

  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: () => departmentService.list() });

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["employees", search, departmentId, employmentStatus, page],
    queryFn: () =>
      employeeService.search({
        search: search || undefined,
        department_id: departmentId || undefined,
        employment_status: employmentStatus || undefined,
        page,
        limit,
      }),
  });

  const columns: Column<EmployeeListItem>[] = [
    { header: "Employee", render: (e) => <span className="font-medium text-gray-900">{e.full_name}</span> },
    { header: "Code", render: (e) => e.employee_code },
    { header: "Department", render: (e) => e.department.name },
    { header: "Job role", render: (e) => e.job_role.title },
    { header: "Status", render: (e) => <StatusBadge status={e.employment_status} /> },
    { header: "Availability", render: (e) => <StatusBadge status={e.availability_status} /> },
    {
      header: "",
      render: (e) => (
        <Link to={`/employees/${e.id}`} className="text-brand-600 hover:text-brand-700">
          View
        </Link>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Employees</h1>
        {canManage && (
          <Link to="/employees/new" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Add employee
          </Link>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        <SearchBar placeholder="Search by name, email, or code..." onSearch={(v) => { setSearch(v); setPage(1); }} />
        <FilterSelect
          label="All departments"
          value={departmentId}
          onChange={(v) => { setDepartmentId(v); setPage(1); }}
          options={(departments ?? []).map((d) => ({ value: d.id, label: d.name }))}
        />
        <FilterSelect
          label="All statuses"
          value={employmentStatus}
          onChange={(v) => { setEmploymentStatus(v); setPage(1); }}
          options={EMPLOYMENT_STATUS_OPTIONS}
        />
      </div>

      {isLoading && <LoadingState label="Loading employees..." />}
      {isError && <ErrorState message="Could not load employees." onRetry={refetch} />}
      {data && (
        <>
          <Table columns={columns} rows={data.items} keyExtractor={(e) => e.id} emptyMessage="No employees match your filters." />
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              Showing {(page - 1) * limit + 1}-{Math.min(page * limit, data.total)} of {data.total}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page * limit >= data.total}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
