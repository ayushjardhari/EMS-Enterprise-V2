import { Navigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import DashboardPage from "./DashboardPage";
import EnterprisePage from "./EnterprisePage";

export default function RoleDashboardPage() {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  switch (user.user_role) {
    case "EMPLOYEE":
      return <DashboardPage />;

    case "ADMIN":
    case "HR":
      return <EnterprisePage />;

    case "MANAGER":
      return <EnterprisePage module="manager-dashboard" />;

    default:
      return <Navigate to="/login" replace />;
  }
}