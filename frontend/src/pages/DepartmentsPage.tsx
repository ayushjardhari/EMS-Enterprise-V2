import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Modal from "../components/Modal";
import Table, { type Column } from "../components/Table";
import { useAuth } from "../hooks/useAuth";
import { departmentService } from "../services/departmentService";
import type { Department } from "../types";

export default function DepartmentsPage() {
  const { user } = useAuth();
  const canManage = user?.user_role === "ADMIN" || user?.user_role === "HR";
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["departments-all"], queryFn: () => departmentService.list(true) });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await departmentService.create({ name, description: description || undefined });
    setName("");
    setDescription("");
    setModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ["departments-all"] });
    queryClient.invalidateQueries({ queryKey: ["departments"] });
  };

  const handleDeactivate = async (id: string) => {
    await departmentService.deactivate(id);
    queryClient.invalidateQueries({ queryKey: ["departments-all"] });
  };

  const columns: Column<Department>[] = [
    { header: "Name", render: (d) => <span className="font-medium text-gray-900">{d.name}</span> },
    { header: "Description", render: (d) => d.description ?? "—" },
    { header: "Status", render: (d) => (d.is_active ? "Active" : "Inactive") },
    {
      header: "",
      render: (d) =>
        canManage && d.is_active ? (
          <button onClick={() => handleDeactivate(d.id)} className="text-red-600 hover:text-red-700">
            Deactivate
          </button>
        ) : null,
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Departments</h1>
        {canManage && (
          <button onClick={() => setModalOpen(true)} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Add department
          </button>
        )}
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message="Could not load departments." onRetry={refetch} />}
      {data && <Table columns={columns} rows={data} keyExtractor={(d) => d.id} />}

      <Modal title="Add department" isOpen={isModalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <input required placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm" />
          <textarea placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm" />
          <button type="submit" className="w-fit rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Create
          </button>
        </form>
      </Modal>
    </div>
  );
}
