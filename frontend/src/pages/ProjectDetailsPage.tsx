import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import StatusBadge from "../components/StatusBadge";
import { projectService } from "../services/projectService";

export default function ProjectDetailsPage() {
  const { id } = useParams<{ id: string }>();

  const { data: project, isLoading, isError, refetch } = useQuery({
    queryKey: ["project", id],
    queryFn: () => projectService.getById(id!),
    enabled: !!id,
  });

  if (isLoading) return <LoadingState label="Loading project..." />;
  if (isError || !project) return <ErrorState message="Could not load this project." onRetry={refetch} />;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">{project.project_name}</h1>
        <p className="text-sm text-gray-500">{project.project_code}</p>
      </div>

      <section className="rounded-lg border border-gray-200 bg-white p-5">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm md:grid-cols-3">
          <div><dt className="text-gray-500">Status</dt><dd><StatusBadge status={project.status} /></dd></div>
          <div><dt className="text-gray-500">Start date</dt><dd className="text-gray-900">{project.start_date}</dd></div>
          <div><dt className="text-gray-500">End date</dt><dd className="text-gray-900">{project.end_date ?? "Ongoing"}</dd></div>
        </dl>
        {project.description && <p className="mt-4 text-sm text-gray-600">{project.description}</p>}
      </section>
    </div>
  );
}
