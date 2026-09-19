import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { UserRole } from "../types";
import LoadingState from "../components/LoadingState";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
}

/**
 * Two jobs: redirect to /login if nobody's authenticated, and (optionally)
 * redirect to /dashboard if the logged-in user's role isn't allowed here.
 * This is the frontend's authorization check — a courtesy for UX, not a
 * security boundary; the backend enforces the real rules independently.
 */
export default function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <LoadingState label="Checking your session..." />;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.user_role)) return <Navigate to="/dashboard" replace />;

  return <Outlet />;
}
