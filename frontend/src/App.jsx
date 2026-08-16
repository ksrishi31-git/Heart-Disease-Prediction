import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import AppLayout from "./layouts/AppLayout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import History from "./pages/History.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import ModelInsights from "./pages/ModelInsights.jsx";
import Predict from "./pages/Predict.jsx";
import Register from "./pages/Register.jsx";
import Security from "./pages/Security.jsx";
import { useAuth } from "./hooks/useAuth.jsx";

function RedirectIfAuthed({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route
        path="/login"
        element={
          <RedirectIfAuthed>
            <Login />
          </RedirectIfAuthed>
        }
      />
      <Route
        path="/register"
        element={
          <RedirectIfAuthed>
            <Register />
          </RedirectIfAuthed>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/predict" element={<Predict />} />
        <Route path="/history" element={<History />} />
        <Route path="/model-insights" element={<ModelInsights />} />
        <Route path="/security" element={<Security />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
