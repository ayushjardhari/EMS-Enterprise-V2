import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { departmentService } from "../services/departmentService";
import { jobRoleService } from "../services/jobRoleService";
import type { AvailabilityStatus, EmployeeProfile } from "../types";

export interface EmployeeFormValues {
  full_name: string;
  email: string;
  phone: string;
  location: string;
  profile_info: string;
  department_id: string;
  job_role_id: string;
  joining_date: string;
  availability_status: AvailabilityStatus;
}

interface EmployeeFormProps {
  initial?: EmployeeProfile;
  onSubmit: (values: EmployeeFormValues) => Promise<void>;
  submitLabel: string;
}

export default function EmployeeForm({ initial, onSubmit, submitLabel }: EmployeeFormProps) {
  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: () => departmentService.list() });
  const { data: jobRoles } = useQuery({ queryKey: ["job-roles"], queryFn: jobRoleService.list });

  const [values, setValues] = useState<EmployeeFormValues>({
    full_name: initial?.full_name ?? "",
    email: initial?.email ?? "",
    phone: initial?.phone ?? "",
    location: initial?.location ?? "",
    profile_info: initial?.profile_info ?? "",
    department_id: initial?.department.id ?? "",
    job_role_id: initial?.job_role.id ?? "",
    joining_date: initial?.joining_date ?? "",
    availability_status: initial?.availability_status ?? "AVAILABLE",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof EmployeeFormValues>(key: K, value: EmployeeFormValues[K]) =>
    setValues((v) => ({ ...v, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit(values);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    "w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 max-w-xl">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Full name</label>
          <input required className={inputClass} value={values.full_name} onChange={(e) => set("full_name", e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
          <input required type="email" className={inputClass} value={values.email} onChange={(e) => set("email", e.target.value)} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Phone</label>
          <input className={inputClass} value={values.phone} onChange={(e) => set("phone", e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Location</label>
          <input className={inputClass} value={values.location} onChange={(e) => set("location", e.target.value)} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Department</label>
          <select required className={inputClass} value={values.department_id} onChange={(e) => set("department_id", e.target.value)}>
            <option value="">Select a department</option>
            {(departments ?? []).map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Job role</label>
          <select required className={inputClass} value={values.job_role_id} onChange={(e) => set("job_role_id", e.target.value)}>
            <option value="">Select a job role</option>
            {(jobRoles ?? []).map((r) => (
              <option key={r.id} value={r.id}>{r.title}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Joining date</label>
          <input required type="date" className={inputClass} value={values.joining_date} onChange={(e) => set("joining_date", e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Availability</label>
          <select
            className={inputClass}
            value={values.availability_status}
            onChange={(e) => set("availability_status", e.target.value as AvailabilityStatus)}
          >
            <option value="AVAILABLE">Available</option>
            <option value="PARTIALLY_AVAILABLE">Partially available</option>
            <option value="UNAVAILABLE">Unavailable</option>
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">Profile info</label>
        <textarea
          className={inputClass}
          rows={3}
          value={values.profile_info}
          onChange={(e) => set("profile_info", e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-fit rounded-md bg-brand-600 px-5 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
