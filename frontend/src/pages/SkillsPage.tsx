import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Modal from "../components/Modal";
import Table, { type Column } from "../components/Table";
import { useAuth } from "../hooks/useAuth";
import { skillService } from "../services/skillService";
import type { Skill } from "../types";

export default function SkillsPage() {
  const { user } = useAuth();
  const canManage = user?.user_role === "ADMIN" || user?.user_role === "HR";
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["skills"], queryFn: skillService.list });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await skillService.create({ name, category: category || undefined });
    setName("");
    setCategory("");
    setModalOpen(false);
    queryClient.invalidateQueries({ queryKey: ["skills"] });
  };

  const columns: Column<Skill>[] = [
    { header: "Name", render: (s) => <span className="font-medium text-gray-900">{s.name}</span> },
    { header: "Category", render: (s) => s.category ?? "—" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Skills</h1>
        {canManage && (
          <button onClick={() => setModalOpen(true)} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Add skill
          </button>
        )}
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState message="Could not load skills." onRetry={refetch} />}
      {data && <Table columns={columns} rows={data} keyExtractor={(s) => s.id} />}

      <Modal title="Add skill" isOpen={isModalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <input required placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm" />
          <input placeholder="Category (optional)" value={category} onChange={(e) => setCategory(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm" />
          <button type="submit" className="w-fit rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Create
          </button>
        </form>
      </Modal>
    </div>
  );
}
