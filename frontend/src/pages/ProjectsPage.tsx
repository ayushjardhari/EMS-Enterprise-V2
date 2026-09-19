import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Modal from "../components/Modal";
import StatusBadge from "../components/StatusBadge";
import Table, { type Column } from "../components/Table";
import { useAuth } from "../hooks/useAuth";
import { departmentService } from "../services/departmentService";
import { projectService } from "../services/projectService";
import type { Project } from "../types";

export default function ProjectsPage() {
  const { user } = useAuth();
  const canManage = user?.user_role === "ADMIN" || user?.user_role === "HR" || user?.user_role === "MANAGER";
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ project_name: "", description: "", department_id: "", start_date: "" });

  const { data: departments } = useQuery({ queryKey: ["departments"], queryFn: () => departmentService.list() });
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["projects"], queryFn: () => projectService.list() });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await projectService.create({ ...form, description: form.description || undefined });
    setForm({ project_name: "", description: "", department_id: "", start_date: "" });
    setModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  };

  const columns: Column<Project>[] = [
    {
      header: "Project",
      render: (p) => (
        <Link to={`/projects/${p.id}`} className="font-medium text-brand-600 hover:text-brand-700">
          {p.project_name}
        </Link>
      ),
    },
    { header: "Code", render: (p) => p.project_code },
    { header: "Status", render: (p) => <StatusBadge status={p.status} /> },
    { header: "Start date", render: (p) => p.start_date },
    { header: "End date", render: (p) => p.end_date ?? "—" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Projects</h1>
        {canManage && (
          <button onClick={() => setModalOpen(true)} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Add project
          </button>
        )}
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message="Could not load projects." onRetry={refetch} />}
      {data && <Table columns={columns} rows={data} keyExtractor={(p) => p.id} />}

      <Modal title="Add project" isOpen={isModalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <input
            required
            placeholder="Project name"
            value={form.project_name}
            onChange={(e) => setForm((f) => ({ ...f, project_name: e.target.value }))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          <textarea
            placeholder="Description (optional)"
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          <select
            required
            value={form.department_id}
            onChange={(e) => setForm((f) => ({ ...f, department_id: e.target.value }))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Select department</option>
            {(departments ?? []).map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <input
            required
            type="date"
            value={form.start_date}
            onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          <button type="submit" className="w-fit rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Create
          </button>
        </form>
      </Modal>
    </div>
  );
}
