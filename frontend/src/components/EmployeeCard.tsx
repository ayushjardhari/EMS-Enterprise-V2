import { Link } from "react-router-dom";
import type { EmployeeListItem } from "../types";
import StatusBadge from "./StatusBadge";

export default function EmployeeCard({ employee }: { employee: EmployeeListItem }) {
  return (
    <Link
      to={`/employees/${employee.id}`}
      className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 transition hover:border-brand-300 hover:shadow-sm"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 font-semibold text-brand-700">
          {employee.full_name
            .split(" ")
            .map((n) => n[0])
            .slice(0, 2)
            .join("")}
        </div>
        <div>
          <p className="font-medium text-gray-900">{employee.full_name}</p>
          <p className="text-xs text-gray-500">
            {employee.employee_code} · {employee.job_role.title} · {employee.department.name}
          </p>
        </div>
      </div>
      <StatusBadge status={employee.employment_status} />
    </Link>
  );
}
