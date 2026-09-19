import { useNavigate } from "react-router-dom";
import EmployeeForm, { type EmployeeFormValues } from "../components/EmployeeForm";
import { employeeService } from "../services/employeeService";

export default function AddEmployeePage() {
  const navigate = useNavigate();

  const handleSubmit = async (values: EmployeeFormValues) => {
    const created = await employeeService.create(values);
    navigate(`/employees/${created.id}`);
  };

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold text-gray-900">Add employee</h1>
      <EmployeeForm onSubmit={handleSubmit} submitLabel="Create employee" />
    </div>
  );
}
