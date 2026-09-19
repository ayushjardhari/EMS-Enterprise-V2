import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import EmployeeForm, { type EmployeeFormValues } from "../components/EmployeeForm";
import { employeeService } from "../services/employeeService";

export default function EditEmployeePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: employee, isLoading, isError, refetch } = useQuery({
    queryKey: ["employee", id],
    queryFn: () => employeeService.getById(id!),
    enabled: !!id,
  });

  const handleSubmit = async (values: EmployeeFormValues) => {
    await employeeService.update(id!, values);
    navigate(`/employees/${id}`);
  };

  if (isLoading) return <LoadingState label="Loading employee..." />;
  if (isError || !employee) return <ErrorState message="Could not load this employee." onRetry={refetch} />;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-gray-900">Edit {employee.full_name}</h1>
      <EmployeeForm initial={employee} onSubmit={handleSubmit} submitLabel="Save changes" />
    </div>
  );
}
