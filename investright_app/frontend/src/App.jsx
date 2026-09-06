import { useState, useEffect } from "react";
import "./App.css";
import { api } from "./api/client";

import Auth from "./screens/Auth";
import Chat from "./screens/Chat";
import Dashboard from "./screens/Dashboard";
import Profile from "./screens/Profile";
import Evaluation from "./screens/Evaluation";
import Feedback from "./screens/Feedback";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("token"));
  const [currentUser, setCurrentUser] = useState(null);
  const [screen, setScreen] = useState("dashboard");
  const [mood, setMood] = useState("straight");
  const [dashboardData, setDashboardData] = useState(null);

  async function loadUser() {
    if (!isAuthenticated) return;
    try {
      const user = await api.getUser();
      setCurrentUser(user);
    } catch {
      // ignore
    }
  }

  async function refreshDashboard() {
    if (!isAuthenticated) return;
    try {
      const data = await api.getDashboard();
      setDashboardData(data);
    } catch {
      // no profile yet, ignore
    }
  }

  useEffect(() => {
    refreshDashboard();
    loadUser();
  }, [isAuthenticated]);

  const isAdmin = Boolean(
    currentUser?.is_admin ||
    currentUser?.email?.toLowerCase() === "admin" ||
    currentUser?.email?.toLowerCase() === "admin@investright.com"
  );

  const mainTabs = ["chat", "dashboard", "profile", "feedback", "evaluation"];
  const showTabBar = mainTabs.includes(screen);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("fin_chat_msgs");
    localStorage.removeItem("fin_chat_step");
    localStorage.removeItem("fin_chat_phase");
    localStorage.removeItem("fin_chat_profile");
    localStorage.removeItem("fin_chat_risk");
    setDashboardData(null);
    setCurrentUser(null);
    setIsAuthenticated(false);
  };

  const handleAuthExpired = () => {
    handleLogout();
  };

  const handleAuthenticated = async () => {
    setIsAuthenticated(true);
    setScreen("dashboard");
    loadUser();
  };

  if (!isAuthenticated) {
    return (
      <div className="app-backdrop">
        <div className="web-app entry-app">
          <main className="app-main">
            <Auth onAuthenticated={handleAuthenticated} />
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="app-backdrop">
      <div className={`web-app authenticated-app`}>
        <aside className="sidebar">
          <div className="sidebar-brand">
            <div className="avatar">F</div>
            <div><strong>Fin</strong><span>wealth, made clear</span></div>
          </div>
          <div className="sidebar-label">Workspace</div>
          <nav className="sidebar-nav" aria-label="Main navigation">
            <button className={screen === "dashboard" ? "active" : ""} onClick={async () => { await refreshDashboard(); setScreen("dashboard"); }}>
              <span>▦</span> Overview
            </button>
            <button className={screen === "chat" ? "active" : ""} onClick={() => setScreen("chat")}>
              <span>✦</span> Ask Fin
            </button>
            <button className={screen === "profile" ? "active" : ""} onClick={() => setScreen("profile")}>
              <span>◎</span> Profile & settings
            </button>
            <button className={screen === "feedback" ? "active" : ""} onClick={() => setScreen("feedback")}>
              <span>★</span> Experience & feedback
            </button>
            {isAdmin && (
              <button className={screen === "evaluation" ? "active" : ""} onClick={() => setScreen("evaluation")}>
                <span>◇</span> Evaluation
              </button>
            )}
          </nav>
          <div className="sidebar-footer">
            <div className="advisor-status"><span /> Fin is online</div>
            <button onClick={handleLogout}>Sign out <span>↗</span></button>
          </div>
        </aside>

        <main className="app-main">
          <header className="topbar">
            <div className="mobile-brand">
              <div className="avatar">F</div>
              <div><h1>Fin</h1><div className="status on">your investment advisor</div></div>
            </div>
            <div className="header-context"><span className="header-kicker">INVESTRIGHT WORKSPACE</span><strong>{screen === "chat" ? "Your advisor" : screen === "profile" ? "Your account" : screen === "feedback" ? "User experience survey" : screen === "evaluation" ? "Research evaluation" : "Your financial snapshot"}</strong></div>
            <button className="header-help" onClick={() => setScreen("chat")}>Ask Fin <span>↗</span></button>
          </header>

          <div className="screens">
          <div style={{ display: screen === "chat" ? "flex" : "none", flex: 1, flexDirection: "column", overflow: "hidden", height: "100%" }}>
            <Chat
              mood={mood}
              onProfileComplete={async () => {
                await refreshDashboard();
              }}
              onViewDashboard={() => setScreen("dashboard")}
              onAuthExpired={handleAuthExpired}
            />
          </div>
          {screen === "dashboard" && <Dashboard data={dashboardData} onRefresh={refreshDashboard} />}
          {screen === "profile" && (
            <Profile
              mood={mood}
              setMood={setMood}
              onLogout={handleLogout}
              onRestart={() => setScreen("chat")}
            />
          )}
          {screen === "feedback" && <Feedback isAdmin={isAdmin} currentUser={currentUser} onDone={() => setScreen("dashboard")} />}
          {screen === "evaluation" && (isAdmin ? <Evaluation /> : <Dashboard data={dashboardData} onRefresh={refreshDashboard} />)}
          </div>

        {showTabBar && (
          <div className="tabbar">
            <button
              className={`tab ${screen === "chat" ? "active" : ""}`}
              onClick={() => setScreen("chat")}
            >
              <span className="tab-icon">💬</span>Chat<span className="dot" />
            </button>
            <button
              className={`tab ${screen === "dashboard" ? "active" : ""}`}
              onClick={async () => {
                await refreshDashboard();
                setScreen("dashboard");
              }}
            >
              <span className="tab-icon">📊</span>Dashboard<span className="dot" />
            </button>
            <button
              className={`tab ${screen === "profile" ? "active" : ""}`}
              onClick={() => setScreen("profile")}
            >
              <span className="tab-icon">👤</span>Profile<span className="dot" />
            </button>
            <button
              className={`tab ${screen === "feedback" ? "active" : ""}`}
              onClick={() => setScreen("feedback")}
            >
              <span className="tab-icon">★</span>Review<span className="dot" />
            </button>
          </div>
        )}
        </main>
      </div>
    </div>
  );
}
