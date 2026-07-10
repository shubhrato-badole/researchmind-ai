import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Landing from "./pages/Landing";
import Enterprise from "./pages/Enterprise";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import StudyMode from "./pages/StudyMode";
import Roadmap from "./pages/Roadmap";
import Profile from "./pages/Profile";
import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

type LayoutProps = {
  children: ReactNode;
};

function ProtectedRoute({ children }: LayoutProps) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="flex items-center justify-center h-screen">
        Loading...
      </div>
    );
  if (!user) return <Navigate to="/login" />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/enterprise" element={<Enterprise />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
          
      <Route path="/chat" element={<ProtectedRoute><Chat /> </ProtectedRoute>} /> 
     <Route path="/documents" element={<ProtectedRoute><Documents /></ProtectedRoute> }/>
      <Route path="/study" element={<ProtectedRoute><StudyMode /></ProtectedRoute>} />
      <Route path="/roadmap" element={<ProtectedRoute><Roadmap /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

<QueryClientProvider client={queryClient}>
  <App />
</QueryClientProvider>;
