import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Lock,
  Bell,
  Trash2,
  ChevronRight,
  FileText,
  MessageSquare,
  X,
} from "lucide-react";
import Layout from "../Components/Layout";
import Button from "../Components/ui/button";
import Input from "../Components/ui/input";
import client from "../Api/client";
import { useAuth } from "../context/AuthContext";
import { useDocuments } from "../hooks/useDocuments";
import { useSessions } from "../hooks/useSessions";
import UpgradeButton from "../Components/UpgradeButton";
export default function Profile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { documents } = useDocuments();
  const { sessions } = useSessions();

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);
  const [passwordError, setPasswordError] = useState("");

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);

  const userInitial = user?.name?.[0]?.toUpperCase() || "U";

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) return;
    setPasswordSubmitting(true);
    setPasswordError("");
    try {
      await client.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setShowPasswordForm(false);
      setCurrentPassword("");
      setNewPassword("");
    } catch {
      setPasswordError(
        "Could not update password. Check your current password and try again.",
      );
    } finally {
      setPasswordSubmitting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") return;
    setDeleting(true);
    try {
      await client.delete("/auth/account");
      logout();
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Layout>
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-5 py-3 border-b border-[#3a3a3c] bg-[#2d2d2f] flex-shrink-0 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-white">Profile</h1>
          <button
            onClick={() => navigate("/chat")}
            className="text-[#888] hover:text-white transition-colors"
            aria-label="Close profile"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 bg-[#2d2d2f]">
          <div className="max-w-lg mx-auto flex flex-col gap-5">
            <div className="flex items-center gap-4 bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-5">
              <div className="w-14 h-14 rounded-full bg-[#534AB7] flex items-center justify-center text-xl font-medium text-white flex-shrink-0">
                {userInitial}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user?.name}
                </p>
                <p className="text-xs text-[#888] truncate">{user?.email}</p>
              </div>
            </div>

            <div>
              <p className="text-[11px] uppercase tracking-wide text-[#666] mb-2">
                Usage
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-xl p-4 text-center">
                  <FileText
                    size={16}
                    className="text-[#7C75D4] mx-auto mb-1.5"
                  />
                  <p className="text-base font-semibold text-white">
                    {documents.length}
                  </p>
                  <p className="text-xs text-[#666]">Documents</p>
                </div>
                <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-xl p-4 text-center">
                  <MessageSquare
                    size={16}
                    className="text-[#7C75D4] mx-auto mb-1.5"
                  />
                  <p className="text-base font-semibold text-white">
                    {sessions.length}
                  </p>
                  <p className="text-xs text-[#666]">Chats</p>
                </div>
              </div>
            </div>


            <div>
              <p className="text-[11px] uppercase tracking-wide text-[#666] mb-2">Plan</p>
              <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-white font-medium">
                    {user?.plan === 'pro' ? 'Pro' : 'Free'}
                  </span>
                  {user?.plan === 'pro' && (
                    <span className="text-[10px] px-2 py-0.5 bg-[#3C3489] text-[#CECBF6] rounded-full">Active</span>
                  )}
                </div>
                {user?.plan === 'free' ? (
                  <>
                    <p className="text-xs text-[#888] mb-3">
                      Upgrade for unlimited search, quizzes, roadmaps, and document uploads.
                    </p>
                    <UpgradeButton />
                  </>
                ) : (
                  <p className="text-xs text-[#5DCAA5]">Unlimited access to everything.</p>
                )}
              </div>
            </div>

            <div>
              <p className="text-[11px] uppercase tracking-wide text-[#666] mb-2">
                Account
              </p>
              <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-xl overflow-hidden">
                <button
                  onClick={() => setShowPasswordForm((prev) => !prev)}
                  className="w-full flex items-center justify-between px-4 py-3 border-b border-[#2a2a2a] hover:bg-[#232325] transition-colors"
                >
                  <span className="text-sm text-[#ccc] flex items-center gap-2">
                    <Lock size={14} className="text-[#888]" /> Change password
                  </span>
                  <ChevronRight
                    size={14}
                    className={`text-[#666] transition-transform ${showPasswordForm ? "rotate-90" : ""}`}
                  />
                </button>

                {showPasswordForm && (
                  <div className="px-4 py-4 border-b border-[#2a2a2a] flex flex-col gap-3 bg-[#191919]">
                    <Input
                      label="Current password"
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                    />
                    <Input
                      label="New password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                    {passwordError && (
                      <p className="text-xs text-red-400">{passwordError}</p>
                    )}
                    <div className="flex gap-2">
                      <Button
                        onClick={handleChangePassword}
                        disabled={
                          !currentPassword || !newPassword || passwordSubmitting
                        }
                        size="sm"
                      >
                        {passwordSubmitting ? "Updating..." : "Update password"}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowPasswordForm(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                <button className="w-full flex items-center justify-between px-4 py-3 border-b border-[#2a2a2a] hover:bg-[#232325] transition-colors">
                  <span className="text-sm text-[#ccc] flex items-center gap-2">
                    <Bell size={14} className="text-[#888]" /> Notification
                    preferences
                  </span>
                  <ChevronRight size={14} className="text-[#666]" />
                </button>

                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#232325] transition-colors"
                >
                  <span className="text-sm text-red-400 flex items-center gap-2">
                    <Trash2 size={14} /> Delete account
                  </span>
                  <ChevronRight size={14} className="text-[#666]" />
                </button>
              </div>
            </div>

            <button
              onClick={logout}
              className="text-xs text-[#666] hover:text-white transition-colors self-start"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-[#1c1c1e] border border-[#3a3a3c] rounded-2xl p-6 w-full max-w-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white">
                Delete account
              </h3>
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeleteConfirmText("");
                }}
              >
                <X size={16} className="text-[#888]" />
              </button>
            </div>
            <p className="text-xs text-[#999] mb-4 leading-relaxed">
              This permanently deletes your account, documents, and chat
              history. This cannot be undone. Type{" "}
              <span className="text-white font-medium">DELETE</span> to confirm.
            </p>
            <input
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="DELETE"
              className="w-full bg-[#2d2d2f] border border-[#3a3a3c] rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-red-500 mb-4"
            />
            <div className="flex gap-2">
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirmText !== "DELETE" || deleting}
                className="flex-1 bg-red-600 text-white text-sm rounded-lg py-2 disabled:opacity-40 hover:bg-red-500 transition-colors"
              >
                {deleting ? "Deleting..." : "Delete permanently"}
              </button>
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeleteConfirmText("");
                }}
                className="flex-1 border border-[#3a3a3c] text-[#999] text-sm rounded-lg py-2"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
