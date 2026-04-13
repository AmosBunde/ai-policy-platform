import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  if (!isAuthenticated) {
    // Preserve return URL so user is redirected back after login
    const returnUrl = location.pathname + location.search;
    return <Navigate to={`/login?returnUrl=${encodeURIComponent(returnUrl)}`} replace />;
  }

  // Role-based access check
  if (requiredRoles && user && !requiredRoles.includes(user.role)) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-50 dark:bg-navy-900">
        <Card className="max-w-md text-center">
          <h1 className="text-4xl font-bold text-danger mb-2">403</h1>
          <p className="text-slate-600 dark:text-slate-400 mb-4">
            You do not have permission to access this page.
          </p>
          <Button variant="secondary" onClick={() => window.history.back()}>
            Go Back
          </Button>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
