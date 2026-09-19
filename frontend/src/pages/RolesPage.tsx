import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Modal from "../components/Modal";
import Table, { type Column } from "../components/Table";
import { useAuth } from "../hooks/useAuth";
import { jobRoleService } from "../services/jobRoleService";
import type { JobRole } from "../types";

export default function RolesPage() {
  const { user } = useAuth();
  const canManage = user?.user_role === "ADMIN" || user?.user_role === "HR";
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["job-roles"], queryFn: jobRoleService.list });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await jobRoleService.create({ title, description: description || undefined });
    setTitle("");
    setDescription("");
    setModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ["job-roles"] });
  };

  const columns: Column<JobRole>[] = [
    { header: "Title", render: (r) => <span className="font-medium text-gray-900">{r.title}</span> },
    { header: "Description", render: (r) => r.description ?? "—" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Job Roles</h1>
        {canManage && (
          <button onClick={() => setModalOpen(true)} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Add role
          </button>
        )}
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message="Could not load job roles." onRetry={refetch} />}
      {data && <Table columns={columns} rows={data} keyExtractor={(r) => r.id} />}

      <Modal title="Add job role" isOpen={isModalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <input required placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm" />
          <textarea placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm" />
          <button type="submit" className="w-fit rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Create
          </button>
        </form>
      </Modal>
    </div>
  );
}
