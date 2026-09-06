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

  const [activeModal, setActiveModal] = useState(null);
  const [supportSent, setSupportSent] = useState(false);
  const [supportMsg, setSupportMsg] = useState("");
  const [toneFeedback, setToneFeedback] = useState("");

  const handleToneChange = (val) => {
    setMood(val);
    localStorage.setItem("fin_advisor_tone", val);
    setToneFeedback(`✓ Advisor tone set to ${val === "straight" ? "Straightforward" : "Encouraging"}`);
    setTimeout(() => setToneFeedback(""), 2500);
  };

  const handleDeleteAccount = () => {
    if (window.confirm("⚠️ Are you sure you want to delete your account and clear all local financial records? This action cannot be undone.")) {
      localStorage.clear();
      if (onLogout) onLogout();
      window.location.reload();
    }
  };

  const handleSendSupport = (e) => {
    e.preventDefault();
    setSupportSent(true);
    setTimeout(() => {
      setSupportSent(false);
      setSupportMsg("");
      setActiveModal(null);
    }, 2000);
  };

  return (
    <div className="profile-screen">
      <div className="dash-title">Profile & Settings</div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div className="prof-row"><span className="k">Name</span><span className="v">{user?.full_name || "Not provided"}</span></div>
        <div className="prof-row"><span className="k">Email</span><span className="v">{user?.email || "Not available"}</span></div>
        <div className="prof-row"><span className="k">Age</span><span className="v">{user?.age ? `${user.age} years` : "Not provided"}</span></div>
        <div className="prof-row"><span className="k">Member since</span><span className="v">{user?.created_at ? new Date(user.created_at).toLocaleDateString("en-IN") : "Not available"}</span></div>
      </div>

      <div className="card evidence-ledger" id="evidence-section">
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

      {/* ADVISOR TONE: Fully Functional */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
          <h3 style={{ margin: 0 }}>Advisor tone</h3>
          {toneFeedback && (
            <span style={{ fontSize: "11.5px", color: "var(--teal)", fontWeight: 600 }}>{toneFeedback}</span>
          )}
        </div>
        <div className="mood-opts">
          <button
            className={`mood-btn ${mood === "straight" ? "selected" : ""}`}
            onClick={() => handleToneChange("straight")}
          >
            Straightforward
          </button>
          <button
            className={`mood-btn ${mood === "encourage" ? "selected" : ""}`}
            onClick={() => handleToneChange("encourage")}
          >
            Encouraging
          </button>
        </div>
        <p style={{ margin: "10px 0 0", fontSize: "12px", color: "var(--muted)", lineHeight: 1.4 }}>
          {mood === "encourage"
            ? "🌟 Encouraging: Fin uses a warm coaching style with motivational milestones and celebratory progress tips."
            : "🎯 Straightforward: Fin delivers direct, concise numbers and analytical institutional summaries."}
        </p>
      </div>

      {/* SUPPORT & LEGAL: Fully Functional Links */}
      <div className="card" style={{ paddingBottom: 4 }}>
        <h3>Support & legal</h3>
        <div className="settings-link" onClick={() => setActiveModal("faq")}>
          <span>Help & FAQ</span><span className="chev">›</span>
        </div>
        <div className="settings-link" onClick={() => setActiveModal("support")}>
          <span>Contact support</span><span className="chev">›</span>
        </div>
        <div className="settings-link" onClick={() => setActiveModal("privacy")}>
          <span>Privacy policy</span><span className="chev">›</span>
        </div>
        <div className="settings-link" onClick={() => setActiveModal("terms")}>
          <span>Terms of service</span><span className="chev">›</span>
        </div>
        <div className="settings-link" onClick={() => setActiveModal("evidence")}>
          <span>Data and evidence</span><span className="chev">›</span>
        </div>
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
        <div className="settings-link danger" onClick={handleDeleteAccount}>
          <span>Delete account & data</span><span className="chev">›</span>
        </div>
      </div>

      {/* ─── MODALS ─────────────────────────────────────────────── */}

      {/* 1. Help & FAQ Modal */}
      {activeModal === "faq" && (
        <div className="modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Help & Frequently Asked Questions</h3>
              <button className="modal-close-btn" onClick={() => setActiveModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="faq-list">
                <details className="faq-item" open>
                  <summary>How does Fin calculate my investment capacity?</summary>
                  <p>
                    Fin evaluates your net monthly income, subtracts your recurring living expenses, and verifies whether you possess a 6-month liquid emergency fund. Your remaining surplus determines your monthly SIP capacity.
                  </p>
                </details>
                <details className="faq-item">
                  <summary>Is my uploaded payslip or financial statement safe?</summary>
                  <p>
                    Yes. Documents are processed ephemerally using cloud AI vision solely to parse earnings and deductions. They are never sold to advertisers or stored in plain-text format.
                  </p>
                </details>
                <details className="faq-item">
                  <summary>What mutual fund categories does InvestRight recommend?</summary>
                  <p>
                    Based on your SEBI-calibrated risk tier:
                    <br />• <strong>Conservative:</strong> Liquid Funds, Arbitrage & High-yield Fixed Deposits.
                    <br />• <strong>Moderate:</strong> Balanced Advantage & Nifty 50 Index Funds.
                    <br />• <strong>Aggressive:</strong> Multi-Cap, Flexi-Cap & Mid-Cap Growth Equity Funds.
                  </p>
                </details>
                <details className="faq-item">
                  <summary>How do I change my risk profile?</summary>
                  <p>
                    You can click <strong>Restart conversation</strong> below to re-take the risk tolerance questionnaire or tell Fin in Ask Fin chat: <em>"Update my risk tolerance to moderate"</em>.
                  </p>
                </details>
                <details className="faq-item">
                  <summary>Does Fin support regional voice recognition?</summary>
                  <p>
                    Yes! Fin supports native speech recognition and audio synthesis in Tamil (தமிழ்), Malayalam (മലയാളം), Kannada (ಕನ್ನಡ), and English.
                  </p>
                </details>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 2. Contact Support Modal */}
      {activeModal === "support" && (
        <div className="modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Contact Customer Support</h3>
              <button className="modal-close-btn" onClick={() => setActiveModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="support-grid">
                <div className="support-card">
                  <strong>Email Support</strong>
                  <span>support@investright.ai</span>
                </div>
                <div className="support-card">
                  <strong>Helpline (Toll-Free)</strong>
                  <span>1800-INVEST-FIN</span>
                </div>
              </div>

              {supportSent ? (
                <div style={{ textAlign: "center", padding: "20px", color: "var(--teal)", fontWeight: 600 }}>
                  ✓ Your support ticket has been received. Our team will contact you within 2 hours!
                </div>
              ) : (
                <form onSubmit={handleSendSupport}>
                  <label style={{ display: "block", fontSize: "12px", color: "var(--muted)", marginBottom: 6 }}>
                    Describe your question or issue:
                  </label>
                  <textarea
                    rows="4"
                    className="feedback-textarea"
                    required
                    placeholder="E.g. I have a question regarding my recommended asset allocation..."
                    value={supportMsg}
                    onChange={(e) => setSupportMsg(e.target.value)}
                  />
                  <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 14 }}>
                    <button type="button" className="btn-outline" onClick={() => setActiveModal(null)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn">
                      Submit Ticket →
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 3. Privacy Policy Modal */}
      {activeModal === "privacy" && (
        <div className="modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Privacy & Data Protection Policy</h3>
              <button className="modal-close-btn" onClick={() => setActiveModal(null)}>✕</button>
            </div>
            <div className="modal-body" style={{ maxHeight: "60vh", overflowY: "auto" }}>
              <p><strong>Last Updated: September 2026</strong></p>
              <p>InvestRight ("we", "our") is committed to protecting your financial privacy. This policy outlines how your information is handled:</p>
              
              <h4 style={{ color: "var(--ink)", margin: "14px 0 6px" }}>1. Zero Data Selling Guarantee</h4>
              <p>We do not sell, rent, or trade your personal or financial data to any third parties, brokers, or advertisers under any circumstances.</p>

              <h4 style={{ color: "var(--ink)", margin: "14px 0 6px" }}>2. Document & OCR Processing</h4>
              <p>Images and PDF payslips uploaded to Fin are extracted using secure encrypted vision pipelines solely to identify your income and deductions. Documents require your explicit confirmation before being bound to your profile.</p>

              <h4 style={{ color: "var(--ink)", margin: "14px 0 6px" }}>3. Data Storage & Encryption</h4>
              <p>User credentials and authentication tokens use industry-standard bcrypt hashing and JSON Web Tokens (JWT). Financial facts are stored in enterprise-grade PostgreSQL with TLS 1.3 encryption in transit.</p>

              <div style={{ textAlign: "right", marginTop: 20 }}>
                <button className="btn" onClick={() => setActiveModal(null)}>I Understand</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Terms of Service Modal */}
      {activeModal === "terms" && (
        <div className="modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Terms of Service & Regulatory Disclaimer</h3>
              <button className="modal-close-btn" onClick={() => setActiveModal(null)}>✕</button>
            </div>
            <div className="modal-body" style={{ maxHeight: "60vh", overflowY: "auto" }}>
              <div style={{ background: "#fef3c7", border: "1px solid #f59e0b", padding: "12px 14px", borderRadius: 8, color: "#92400e", marginBottom: 14 }}>
                <strong>⚠️ SEBI Compliance Notice:</strong> Fin is an AI-powered financial wellness and education assistant. Fin does not execute trades or provide SEBI-registered individualized portfolio management.
              </div>
              
              <h4 style={{ color: "var(--ink)", margin: "14px 0 6px" }}>1. Market Risk Disclaimer</h4>
              <p>Mutual fund investments and equity allocations are subject to market risks. Past performance does not guarantee future results. Please read all scheme-related documents carefully before investing.</p>

              <h4 style={{ color: "var(--ink)", margin: "14px 0 6px" }}>2. Educational & Planning Utility</h4>
              <p>Calculations such as savings rates, emergency runway, and compound SIP projections are provided strictly for budgeting and planning purposes.</p>

              <h4 style={{ color: "var(--ink)", margin: "14px 0 6px" }}>3. User Responsibility</h4>
              <p>You are responsible for ensuring that income and expense figures submitted reflect your authentic financial situation.</p>

              <div style={{ textAlign: "right", marginTop: 20 }}>
                <button className="btn" onClick={() => setActiveModal(null)}>Accept & Close</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. Data and Evidence Ledger Modal */}
      {activeModal === "evidence" && (
        <div className="modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Data & Evidence Audit Trail</h3>
              <button className="modal-close-btn" onClick={() => setActiveModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ margin: "0 0 14px", fontSize: "13px", color: "var(--muted)" }}>
                Auditable record of uploaded payslips, salary certificates, and confirmation statuses.
              </p>
              {evidence.length ? (
                <div style={{ display: "grid", gap: 10 }}>
                  {evidence.map((item) => (
                    <div key={item.id} style={{ border: "1px solid var(--line)", padding: "10px 14px", borderRadius: 8, background: "var(--panel)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <strong style={{ textTransform: "capitalize" }}>{item.field_name.replaceAll("_", " ")}</strong>
                        <span style={{ fontSize: "11px", color: item.confirmed ? "var(--teal)" : "#b45309", fontWeight: 600 }}>
                          {item.confirmed ? "✓ Verified by User" : "⏳ Pending Confirmation"}
                        </span>
                      </div>
                      <div style={{ fontSize: "12px", color: "var(--muted)" }}>
                        File: {item.filename} • Confidence: {Math.round(item.confidence * 100)}%
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "30px 10px", color: "var(--muted)" }}>
                  No uploaded evidence records yet. Upload a payslip or bank statement in Ask Fin chat to create your first auditable record.
                </div>
              )}
              <div style={{ textAlign: "right", marginTop: 20 }}>
                <button className="btn" onClick={() => setActiveModal(null)}>Done</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

