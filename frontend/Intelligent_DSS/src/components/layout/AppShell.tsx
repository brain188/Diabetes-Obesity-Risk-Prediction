import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { AppSidebar } from "./AppSidebar";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { useCurrentUser } from "@/hooks/useAuth";

export function AppShell() {
  // Fires GET /auth/profile — if token is invalid, the 401 interceptor logs the user out.
  // Result is intentionally unused here; user data comes from the Zustand persist store set at login.
  useCurrentUser();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <AppSidebar />
      <main className="ml-64 mt-16 min-h-[calc(100vh-64px)] bg-background">
        <div className="p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
