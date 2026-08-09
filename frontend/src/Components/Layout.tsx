import { useState } from "react";
import { NavLink, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useSessions, type Session } from "../hooks/useSessions";
import { useRoadmaps } from "../hooks/useRoadmaps";
import {
  MessageSquare,
  FolderOpen,
  GraduationCap,
  Map,
  Brain,
  Plus,
  Trash2,
  ChevronDown,
  ChevronsLeft,
  ChevronsRight,
  LogOut,
} from "lucide-react";

interface SubItem {
  id: number;
  title: string;
}

const MAX_VISIBLE_CHATS = 5;

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const currentSessionId = searchParams.get("session")
    ? Number(searchParams.get("session"))
    : null;

  const { sessions, deleteSession } = useSessions();
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem("sidebar-collapsed") === "true",
  );
  const [openSection, setOpenSection] = useState<"study" | "roadmap" | null>(
    null,
  );
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [studySets] = useState<SubItem[]>([]);
  const { roadmaps } = useRoadmaps();
  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      localStorage.setItem("sidebar-collapsed", String(!prev));
      return !prev;
    });
  };

  const newChat = () => navigate("/chat");
  const openSession = (id: number) => navigate(`/chat?session=${id}`);

  const handleDelete = async (id: number) => {
    try {
      await deleteSession(id);
      if (currentSessionId === id) navigate("/chat");
    } finally {
      setConfirmDeleteId(null);
    }
  };

  const toggleSection = (section: "study" | "roadmap") => {
    setOpenSection((prev) => (prev === section ? null : section));
  };

  const iconBtnBase =
    "w-8 h-8 rounded-lg flex items-center justify-center transition-colors cursor-pointer";

  return (
    <div className="flex h-screen bg-[#2d2d2f]">
      <aside
        className={`${collapsed ? "w-16" : "w-56"} bg-[#1c1c1e] border-r border-[#3a3a3c] flex flex-col flex-shrink-0 transition-all duration-200`}
      >
        {collapsed ? (
          <div className="flex flex-col items-center gap-2 py-3">
            <div className="w-7 h-7 bg-[#534AB7] rounded-lg flex items-center justify-center">
              <Brain size={15} color="white" />
            </div>
            <button
              onClick={toggleCollapsed}
              className={`${iconBtnBase} text-[#777] hover:text-white hover:bg-[#2d2d2f]`}
              aria-label="Expand sidebar"
            >
              <ChevronsRight size={15} />
            </button>

            <div className="w-8 border-t border-[#3a3a3c] my-1" />

            <button
              onClick={newChat}
              title="New chat"
              className={`${iconBtnBase} rounded-full bg-[#534AB7] text-white hover:bg-[#3C3489]`}
              aria-label="New chat"
            >
              <Plus size={15} />
            </button>

            <div className="w-8 border-t border-[#3a3a3c] my-1" />

            <NavLink
              to="/documents"
              title="My documents"
              className={({ isActive }) =>
                `${iconBtnBase} ${isActive ? "bg-[#1e1b4b] text-[#7C75D4]" : "text-[#888] hover:text-white hover:bg-[#2d2d2f]"}`
              }
            >
              <FolderOpen size={16} />
            </NavLink>
            <button
              onClick={() => navigate("/study")}
              title="Study mode"
              className={`${iconBtnBase} text-[#888] hover:text-white hover:bg-[#2d2d2f]`}
            >
              <GraduationCap size={16} />
            </button>
            <button
              onClick={() => navigate("/roadmap")}
              title="Roadmap"
              className={`${iconBtnBase} text-[#888] hover:text-white hover:bg-[#2d2d2f]`}
            >
              <Map size={16} />
            </button>

            <div className="flex-1" />

            <div className="w-7 h-7 bg-[#1e1b4b] rounded-full flex items-center justify-center text-xs font-medium text-[#7C75D4] mb-3">
              {user?.name?.[0]?.toUpperCase()}
            </div>
          </div>
        ) : (
          <>
            <div className="px-3 py-4 border-b border-[#3a3a3c] flex items-center justify-between">
              <div className="flex items-center gap-2 overflow-hidden">
                <div className="w-7 h-7 bg-[#534AB7] rounded-lg flex items-center justify-center flex-shrink-0">
                  <Brain size={15} color="white" />
                </div>
                <span className="text-sm font-semibold text-white truncate">
                  ResearchMind
                </span>
              </div>
              <button
                onClick={toggleCollapsed}
                className="text-[#666] hover:text-white transition-colors flex-shrink-0"
                aria-label="Collapse sidebar"
              >
                <ChevronsLeft size={15} />
              </button>
            </div>

            <div className="p-2">
              <button
                onClick={newChat}
                className="w-full flex items-center gap-2 px-3 py-2 bg-[#534AB7] text-white rounded-xl text-xs font-medium hover:bg-[#3C3489] transition-colors"
              >
                <Plus size={14} />
                New chat
              </button>
            </div>

            <div className="px-2 mb-1">
              <p className="text-[10px] uppercase tracking-wide text-[#555] px-2 mb-1">
                Recent
              </p>
              <div
                className="overflow-y-auto"
                style={{ maxHeight: `${MAX_VISIBLE_CHATS * 34}px` }}
              >
                {sessions.length === 0 ? (
                  <p className="text-xs text-[#555] text-center py-3">
                    No chats yet
                  </p>
                ) : (
                  sessions.map((session: Session) => {
                    const isActive = currentSessionId === session.id;
                    const isConfirming = confirmDeleteId === session.id;
                    return (
                      <div
                        key={session.id}
                        className={`group flex items-center justify-between gap-1 px-2 py-1.5 rounded-lg mb-0.5 text-xs cursor-pointer transition-colors ${isActive
                          ? "bg-[#1e1b4b] text-[#7C75D4] font-medium"
                          : "text-[#888] hover:text-white hover:bg-[#2d2d2f]"
                          }`}
                        onClick={() => !isConfirming && openSession(session.id)}
                      >
                        {isConfirming ? (
                          <div className="flex items-center justify-between w-full">
                            <span className="text-[#ccc]">Delete?</span>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDelete(session.id);
                                }}
                                className="text-red-400 hover:text-red-300 font-medium"
                              >
                                Yes
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setConfirmDeleteId(null);
                                }}
                                className="text-[#888] hover:text-white"
                              >
                                No
                              </button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <span
                              className="flex items-center gap-1.5 truncate"
                              title={session.title}
                            >
                              {isActive && (
                                <span className="w-1.5 h-1.5 rounded-full bg-[#7C75D4] flex-shrink-0" />
                              )}
                              <MessageSquare
                                size={12}
                                className="flex-shrink-0"
                              />
                              <span className="truncate">{session.title}</span>
                            </span>
                            <Trash2
                              size={12}
                              className="flex-shrink-0 opacity-0 group-hover:opacity-100 text-[#666] hover:text-red-400 transition-opacity"
                              onClick={(e) => {
                                e.stopPropagation();
                                setConfirmDeleteId(session.id);
                              }}
                            />
                          </>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <nav className="flex-1 overflow-y-auto p-2 border-t border-[#3a3a3c] pt-2">
              <NavLink
                to="/documents"
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm mb-0.5 transition-colors ${isActive
                    ? "bg-[#1e1b4b] text-[#7C75D4] font-medium"
                    : "text-[#888] hover:text-white hover:bg-[#2d2d2f]"
                  }`
                }
              >
                <FolderOpen size={15} />
                My documents
              </NavLink>

              <div>
                <button
                  onClick={() => {
                    navigate("/study");
                    toggleSection("study");
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-sm mb-0.5 transition-colors text-[#888] hover:text-white hover:bg-[#2d2d2f]"
                >
                  <span className="flex items-center gap-2.5">
                    <GraduationCap size={15} />
                    Study mode
                  </span>
                  <ChevronDown
                    size={12}
                    className={`transition-transform ${openSection === "study" ? "rotate-180" : ""}`}
                  />
                </button>
                {openSection === "study" && (
                  <div className="pl-7 mb-1">
                    {studySets.length === 0 ? (
                      <p className="text-[11px] text-[#555] py-1">
                        No saved sets yet
                      </p>
                    ) : (
                      studySets.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between text-[11px] text-[#888] hover:text-white px-2 py-1 rounded-lg group"
                        >
                          <span className="truncate">{item.title}</span>
                          <Trash2
                            size={11}
                            className="opacity-0 group-hover:opacity-100 text-[#666] hover:text-red-400"
                          />
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              <div>
                <button
                  onClick={() => {
                    navigate("/roadmap");
                    toggleSection("roadmap");
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-sm mb-0.5 transition-colors text-[#888] hover:text-white hover:bg-[#2d2d2f]"
                >
                  <span className="flex items-center gap-2.5">
                    <Map size={15} />
                    Roadmap
                  </span>
                  <ChevronDown
                    size={12}
                    className={`transition-transform ${openSection === "roadmap" ? "rotate-180" : ""}`}
                  />
                </button>
                {openSection === "roadmap" && (
                  <div className="pl-7 mb-1">
                    <button
                      onClick={() => navigate("/roadmap?new=true")}
                      className="w-full flex items-center gap-1.5 text-[11px] text-[#7C75D4] hover:text-white px-2 py-1.5 rounded-lg transition-colors"
                    >
                      <Plus size={12} /> New roadmap
                    </button>
                    {roadmaps.length === 0 ? (
                      <p className="text-[11px] text-[#555] py-1 px-2">
                        No roadmaps yet
                      </p>
                    ) : (
                      roadmaps.map((r) => (
                        <button
                          key={r.id}
                          onClick={() => navigate(`/roadmap?id=${r.id}`)}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[#2d2d2f] transition-colors"
                        >
                          <p className="text-[11px] text-[#ccc] truncate">
                            {r.goal}
                          </p>
                          {r.streak > 0 && (
                            <div className="flex items-center gap-1 mt-0.5">
                              <span className="text-[9px] text-orange-400">
                                🔥 {r.streak} day streak
                              </span>
                            </div>
                          )}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            </nav>

            <div className="p-3 border-t border-[#3a3a3c]">
              {user?.plan === 'free' && (
                <button
                  onClick={() => navigate('/pricing')}
                  className="w-full bg-[#7F77DD] text-[#26215C] font-medium px-3 py-2 rounded-lg text-xs mb-3 hover:bg-[#AFA9EC] transition-colors"
                >
                  Upgrade to Pro
                </button>
              )}

              <button
                onClick={() => navigate("/profile")}
                className="w-full flex items-center gap-2.5 py-2 border-t border-b border-[#2a2a2a] hover:bg-[#2d2d2f] transition-colors px-1"
              >
                <div className="w-8 h-8 bg-[#1e1b4b] rounded-full flex items-center justify-center text-xs font-medium text-[#7C75D4] flex-shrink-0">
                  {user?.name?.[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <span className="text-xs font-medium text-white truncate block">
                    {user?.name}
                  </span>
                  <span className="text-[11px] text-[#7F77DD]">
                    {user?.plan === 'pro' ? 'Pro plan' : 'Free plan'}
                  </span>
                </div>
              </button>

              <button
                onClick={logout}
                className="w-full flex items-center gap-2 text-xs text-[#888] hover:text-white transition-colors px-1 py-2"
              >
                <LogOut size={14} /> Sign out
              </button>
            </div>
          </>
        )}
      </aside>

      <main className="flex-1 overflow-hidden flex flex-col">{children}</main>
    </div>
  );
}
