import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";

import LoginPage from "@/pages/auth/LoginPage";
import RegisterPage from "@/pages/auth/RegisterPage";
import VerifyEmailPage from "@/pages/auth/VerifyEmailPage";
import AdminSetupPage from "@/pages/setup/AdminSetupPage";

import DashboardPage from "@/pages/dashboard/DashboardPage";
import AdminDashboardPage from "@/pages/admin/AdminDashboardPage";
import UserManagementPage from "@/pages/admin/UserManagementPage";
import FacilityManagementPage from "@/pages/admin/FacilityManagementPage";
import FacilitySettingsPage from "@/pages/admin/FacilitySettingsPage";
import SystemLogsPage from "@/pages/admin/SystemLogsPage";
import AuditTrailPage from "@/pages/admin/AuditTrailPage";
import AIPredictionReportPage from "@/pages/admin/AIPredictionReportPage";

import PatientManagementPage from "@/pages/patients/PatientManagementPage";
import PatientProfilePage from "@/pages/patients/PatientProfilePage";
import ScreeningDataEntryPage from "@/pages/screening/ScreeningDataEntryPage";
import ScreeningsPage from "@/pages/screenings/ScreeningsPage";
import PredictionsListPage from "@/pages/predictions/PredictionsListPage";
import PredictionResultsPage from "@/pages/predictions/PredictionResultsPage";
import PredictionReportPage from "@/pages/predictions/PredictionReportPage";
import ReportsManagementPage from "@/pages/reports/ReportsManagementPage";
import AnalyticsDashboardPage from "@/pages/analytics/AnalyticsDashboardPage";
import UserSettingsPage from "@/pages/settings/UserSettingsPage";
import HelpCenterPage from "@/pages/help/HelpCenterPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  { path: "/register/verify", element: <VerifyEmailPage /> },
  { path: "/setup", element: <AdminSetupPage /> },
  {
    path: "/",
    element: <RequireAuth><AppShell /></RequireAuth>,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "patients", element: <PatientManagementPage /> },
      { path: "patients/:id", element: <PatientProfilePage /> },
      { path: "patients/:id/screening", element: <ScreeningDataEntryPage /> },
      { path: "patients/:id/prediction", element: <PredictionResultsPage /> },
      { path: "patients/:id/report", element: <PredictionReportPage /> },
      { path: "screenings", element: <ScreeningsPage /> },
      { path: "predictions", element: <PredictionsListPage /> },
      { path: "reports", element: <ReportsManagementPage /> },
      { path: "reports/:id", element: <PredictionReportPage /> },
      { path: "analytics", element: <AnalyticsDashboardPage /> },
      { path: "settings", element: <UserSettingsPage /> },
      { path: "help", element: <HelpCenterPage /> },
      { path: "admin", element: <Navigate to="/admin/dashboard" replace /> },
      { path: "admin/dashboard", element: <AdminDashboardPage /> },
      { path: "admin/users", element: <UserManagementPage /> },
      { path: "admin/facilities", element: <FacilityManagementPage /> },
      { path: "admin/facilities/:id/settings", element: <FacilitySettingsPage /> },
      { path: "admin/config", element: <FacilitySettingsPage /> },
      { path: "admin/logs", element: <SystemLogsPage /> },
      { path: "admin/audit", element: <AuditTrailPage /> },
      { path: "admin/ai-report", element: <AIPredictionReportPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
