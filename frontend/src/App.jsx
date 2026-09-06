import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import ProtectedRoute from "./components/ProtectedRoute";

import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import CitizenDashboard from "./pages/citizen/CitizenDashboard";
import SubmitComplaint from "./pages/citizen/SubmitComplaint";
import ComplaintDetail from "./pages/citizen/ComplaintDetail";
import Profile from "./pages/citizen/Profile";
import AdminDashboard from "./pages/admin/AdminDashboard";
import ComplaintsManagement from "./pages/admin/ComplaintsManagement";
import AdminComplaintDetail from "./pages/admin/AdminComplaintDetail";
import Departments from "./pages/admin/Departments";
import Users from "./pages/admin/Users";
import AuditLogs from "./pages/admin/AuditLogs";
import GISMap from "./pages/admin/GISMap";
import OfficerDashboard from "./pages/officer/OfficerDashboard";
import OfficerComplaintDetail from "./pages/officer/OfficerComplaintDetail";

export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute allowedRoles={["CITIZEN"]}>
                  <CitizenDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/complaints/new"
              element={
                <ProtectedRoute allowedRoles={["CITIZEN"]}>
                  <SubmitComplaint />
                </ProtectedRoute>
              }
            />
            <Route
              path="/complaints/:id"
              element={
                <ProtectedRoute allowedRoles={["CITIZEN"]}>
                  <ComplaintDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />

            {/* Admin */}
            <Route
              path="/admin/dashboard"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/complaints"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <ComplaintsManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/complaints/:id"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <AdminComplaintDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/gis-map"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <GISMap />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/departments"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <Departments />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <Users />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/audit-logs"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <AuditLogs />
                </ProtectedRoute>
              }
            />

            {/* Officer */}
            <Route
              path="/officer/dashboard"
              element={
                <ProtectedRoute allowedRoles={["OFFICER"]}>
                  <OfficerDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/officer/complaints/:id"
              element={
                <ProtectedRoute allowedRoles={["OFFICER"]}>
                  <OfficerComplaintDetail />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}
