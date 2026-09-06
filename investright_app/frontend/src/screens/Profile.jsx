import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Profile({ mood, setMood, onLogout, onRestart }) {
  const [profile, setProfile] = useState(null);
  const [user, setUser] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [notifOn, setNotifOn] = useState(true);

  useEffect(() => {
    // Fetch independently so a missing profile doesn't hide user details
    api.getUser().then(setUser).catch(() => setUser(null));
    api.getProfile().then(setProfile).catch(() => setProfile(null));
    api.getEvidence().then(setEvidence).catch(() => setEvidence([]));
  }, []);

  return (
    <div className="profile-screen">
      <div className="dash-title">Profile</div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div className="prof-row"><span className="k">Name</span><span className="v">{user?.full_name || "Not provided"}</span></div>
        <div className="prof-row"><span className="k">Email</span><span className="v">{user?.email || "Not available"}</span></div>
        <div className="prof-row"><span className="k">Age</span><span className="v">{user?.age ? `${user.age} years` : "Not provided"}</span></div>
        <div className="prof-row"><span className="k">Member since</span><span className="v">{user?.created_at ? new Date(user.created_at).toLocaleDateString("en-IN") : "Not available"}</span></div>
      </div>

      <div className="card evidence-ledger">
        <div className="section-heading">
          <h3>Evidence ledger</h3>
          <span className="planner-badge">{evidence.filter((item) => item.confirmed).length} confirmed</span>
        </div>
        {evidence.length ? evidence.slice(0, 8).map((item) => (
          <div className="evidence-ledger-row" key={item.id}>
            <div><strong>{item.field_name.replaceAll("_", " ")}</strong><span>{item.filename} · {Math.round(item.confidence * 100)}% extraction confidence</span></div>
            <div className={item.confirmed ? "evidence-confirmed" : "evidence-pending"}>{item.confirmed ? "Confirmed" : "Review"}</div>
          </div>
        )) : <p className="portfolio-empty">Upload a payslip or statement in Ask Fin to create your first evidence record.</p>}
      </div>

      {profile && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="prof-row"><span className="k">Monthly income</span><span className="v">₹{profile.income.toLocaleString("en-IN")}</span></div>
          <div className="prof-row"><span className="k">Monthly expenses</span><span className="v">₹{profile.expenses.toLocaleString("en-IN")}</span></div>
          <div className="prof-row"><span className="k">Current savings</span><span className="v">₹{profile.savings.toLocaleString("en-IN")}</span></div>
          <div className="prof-row"><span className="k">Planned investment</span><span className="v">₹{profile.planned_investment.toLocaleString("en-IN")}</span></div>
          <div className="prof-row"><span className="k">Goal</span><span className="v">{profile.goal}</span></div>
          <div className="prof-row"><span className="k">Horizon</span><span className="v">{profile.horizon_years} yrs</span></div>
        </div>
      )}

      <div className="card">
        <h3>Advisor tone</h3>
        <div className="mood-opts">
          <button
            className={`mood-btn ${mood === "straight" ? "selected" : ""}`}
            onClick={() => setMood("straight")}
          >
            Straightforward
          </button>
          <button
            className={`mood-btn ${mood === "encourage" ? "selected" : ""}`}
            onClick={() => setMood("encourage")}
          >
            Encouraging
          </button>
        </div>
      </div>

      <div className="card" style={{ paddingBottom: 4 }}>
        <h3>Support & legal</h3>
        <div className="settings-link"><span>Help & FAQ</span><span className="chev">›</span></div>
        <div className="settings-link"><span>Contact support</span><span className="chev">›</span></div>
        <div className="settings-link"><span>Privacy policy</span><span className="chev">›</span></div>
        <div className="settings-link"><span>Terms of service</span><span className="chev">›</span></div>
        <div className="settings-link"><span>Data and evidence</span><span className="chev">›</span></div>
      </div>

      <div className="card">
        <h3>Reset</h3>
        <p className="rec-text" style={{ marginBottom: 12 }}>
          Start over and chat through your profile again.
        </p>
        <button className="btn btn-block" onClick={onRestart}>Restart conversation</button>
      </div>

      <div className="card" style={{ paddingBottom: 4 }}>
        <div className="settings-link" onClick={onLogout}><span>Log out</span><span className="chev">›</span></div>
        <div className="settings-link danger"><span>Delete account & data</span><span className="chev">›</span></div>
      </div>
    </div>
  );
}
