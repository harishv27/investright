import { useState, useEffect } from "react";
import { api } from "../api/client";

const FEATURE_CHOICES = [
  "Tamil / Regional Voice Input",
  "Payslip / Document OCR Scanner",
  "Conversational AI Financial Advice",
  "Disciplined Risk Profiling",
  "Clean Modern Dashboard & Cashflow Visuals",
];

export default function Feedback({ isAdmin = false, currentUser = null, onDone }) {
  // Admin View State
  const [feedbacks, setFeedbacks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loadingFeedbacks, setLoadingFeedbacks] = useState(isAdmin);
  const [showSurveyForm, setShowSurveyForm] = useState(!isAdmin);
  const [searchTerm, setSearchTerm] = useState("");

  // User Survey State
  const [form, setForm] = useState({
    overall_rating: 5,
    voice_feature_rating: 5,
    text_chat_rating: 5,
    ai_advisor_rating: 5,
    user_friendly_rating: 5,
    document_extraction_rating: 5,
    multilingual_rating: 5,
    nps_score: 10,
    most_valuable_feature: "Tamil / Regional Voice Input",
    suggestions: "",
  });

  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Load feedbacks if admin
  useEffect(() => {
    if (isAdmin) {
      setLoadingFeedbacks(true);
      Promise.all([
        api.getAllFeedbacks().catch(() => []),
        api.getFeedbackSummary().catch(() => null),
      ]).then(([allFb, sumData]) => {
        setFeedbacks(allFb || []);
        setSummary(sumData);
        setLoadingFeedbacks(false);
      });
    }
  }, [isAdmin]);

  const handleStar = (field, val) => {
    setForm((prev) => ({ ...prev, [field]: val }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await api.submitFeedback(form);
      setSubmitted(true);
      if (isAdmin) {
        // Refresh admin view
        const fresh = await api.getAllFeedbacks();
        const freshSummary = await api.getFeedbackSummary();
        setFeedbacks(fresh || []);
        setSummary(freshSummary);
      }
    } catch (err) {
      setError(err.message || "Could not submit feedback. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleExportCsv = () => {
    if (!feedbacks || feedbacks.length === 0) return;
    const headers = [
      "ID",
      "User Name",
      "User Email",
      "Overall (1-5)",
      "Voice (1-5)",
      "Chat (1-5)",
      "AI Advisor (1-5)",
      "Ease of Use (1-5)",
      "OCR Extraction (1-5)",
      "Multilingual (1-5)",
      "NPS (1-10)",
      "Favorite Feature",
      "Suggestions",
      "Submitted At",
    ];
    const csvRows = [headers.join(",")];
    for (const f of feedbacks) {
      const row = [
        f.id,
        `"${(f.user_name || "Anonymous").replace(/"/g, '""')}"`,
        `"${(f.user_email || "").replace(/"/g, '""')}"`,
        f.overall_rating,
        f.voice_feature_rating,
        f.text_chat_rating,
        f.ai_advisor_rating,
        f.user_friendly_rating,
        f.document_extraction_rating,
        f.multilingual_rating,
        f.nps_score,
        `"${(f.most_valuable_feature || "").replace(/"/g, '""')}"`,
        `"${(f.suggestions || "").replace(/"/g, '""')}"`,
        `"${f.created_at || ""}"`,
      ];
      csvRows.push(row.join(","));
    }
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `investright_user_feedbacks_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const renderStars = (field, label, desc) => (
    <div className="feedback-question-card">
      <div className="feedback-q-header">
        <label className="feedback-q-title">{label}</label>
        <span className="feedback-rating-badge">{form[field]} / 5</span>
      </div>
      {desc && <p className="feedback-q-desc">{desc}</p>}
      <div className="star-rating-row">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`star-btn ${form[field] >= star ? "active" : ""}`}
            onClick={() => handleStar(field, star)}
          >
            ★
          </button>
        ))}
      </div>
    </div>
  );

  // ─────────────────────────────────────────────────────────────
  // ADMIN VIEW: Display Feedback Responses Alone
  // ─────────────────────────────────────────────────────────────
  if (isAdmin && !showSurveyForm) {
    const filteredFeedbacks = feedbacks.filter((f) => {
      if (!searchTerm) return true;
      const q = searchTerm.toLowerCase();
      return (
        (f.user_name && f.user_name.toLowerCase().includes(q)) ||
        (f.user_email && f.user_email.toLowerCase().includes(q)) ||
        (f.suggestions && f.suggestions.toLowerCase().includes(q)) ||
        (f.most_valuable_feature && f.most_valuable_feature.toLowerCase().includes(q))
      );
    });

    return (
      <div className="admin-feedback-screen">
        <div className="admin-feedback-hero">
          <div>
            <span className="header-kicker">ADMINISTRATOR INTELLIGENCE VIEW</span>
            <h2 style={{ fontFamily: "Fraunces, serif", fontSize: "26px", margin: "4px 0 8px" }}>
              Verified User Feedback & Experience Ratings
            </h2>
            <p style={{ color: "var(--muted)", fontSize: "14px", margin: 0 }}>
              Live customer satisfaction logs across speech recognition, conversational RAG, document parsing, and NPS.
            </p>
          </div>
          <div className="admin-feedback-actions">
            <button className="btn-outline" onClick={handleExportCsv} disabled={feedbacks.length === 0}>
              📥 Export All to CSV
            </button>
            <button className="btn-outline" onClick={() => setShowSurveyForm(true)}>
              📝 Test Survey Form
            </button>
          </div>
        </div>

        {/* High-level Counters (How Many) */}
        <div className="admin-stat-grid">
          <div className="admin-stat-card">
            <span>Total Submissions</span>
            <strong>{feedbacks.length}</strong>
            <small>Verified user responses</small>
          </div>
          <div className="admin-stat-card">
            <span>Overall Score</span>
            <strong style={{ color: "var(--teal)" }}>
              ★ {summary ? summary.average_overall : "5.0"} <span style={{ fontSize: "14px", color: "var(--muted)" }}>/ 5</span>
            </strong>
            <small>Platform satisfaction</small>
          </div>
          <div className="admin-stat-card">
            <span>Voice & Audio</span>
            <strong>★ {summary ? summary.average_voice : "5.0"} <span style={{ fontSize: "14px", color: "var(--muted)" }}>/ 5</span></strong>
            <small>Speech recognition</small>
          </div>
          <div className="admin-stat-card">
            <span>AI Advisor Trust</span>
            <strong>★ {summary ? summary.average_ai_advisor : "5.0"} <span style={{ fontSize: "14px", color: "var(--muted)" }}>/ 5</span></strong>
            <small>Grounded calculations</small>
          </div>
          <div className="admin-stat-card">
            <span>Net Promoter Score</span>
            <strong style={{ color: "#0284c7" }}>{summary ? `+${Math.round(summary.average_nps * 10)}` : "+90"}</strong>
            <small>Avg {summary ? summary.average_nps : "9.5"} / 10</small>
          </div>
        </div>

        {/* Filter bar */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", gap: "12px", flexWrap: "wrap" }}>
          <div style={{ fontWeight: 600, fontSize: "15px", color: "var(--ink)" }}>
            Responses ({filteredFeedbacks.length} of {feedbacks.length})
          </div>
          <input
            type="text"
            placeholder="Search by user, email, or suggestion..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              padding: "8px 14px",
              borderRadius: "20px",
              border: "1px solid var(--line)",
              fontSize: "13px",
              width: "280px",
              background: "var(--panel)",
            }}
          />
        </div>

        {/* Detailed Responses Feed (From Whom, How Many, All details) */}
        {loadingFeedbacks ? (
          <div style={{ padding: "40px 0", textAlign: "center", color: "var(--muted)" }}>
            Loading user feedback logs...
          </div>
        ) : filteredFeedbacks.length === 0 ? (
          <div className="feedback-card" style={{ textAlign: "center", padding: "40px 20px" }}>
            <div style={{ fontSize: "36px", marginBottom: "10px" }}>💬</div>
            <strong style={{ display: "block", fontSize: "16px", color: "var(--ink)" }}>No feedback responses match</strong>
            <p style={{ color: "var(--muted)", fontSize: "13px", marginTop: "4px" }}>
              Try clearing your search query or submit a test review using the survey form.
            </p>
          </div>
        ) : (
          <div className="feedback-feed">
            {filteredFeedbacks.map((f) => (
              <div key={f.id} className="feedback-card">
                <div className="feedback-card-top">
                  <div className="feedback-card-user">
                    <strong>{f.user_name || "Anonymous User"}</strong>
                    <span>
                      {f.user_email || "No email provided"} • Submitted: {f.created_at ? new Date(f.created_at).toLocaleString() : "Just now"}
                    </span>
                  </div>
                  <div className="feedback-card-badges">
                    <span className="badge-rating">★ {f.overall_rating} / 5 Overall</span>
                    <span className="badge-nps">NPS {f.nps_score} / 10</span>
                  </div>
                </div>

                {/* Granular Dimension Ratings */}
                <div className="feedback-scores-row">
                  <div className="feedback-score-item">
                    <span>Voice Input</span>
                    <strong>★ {f.voice_feature_rating} / 5</strong>
                  </div>
                  <div className="feedback-score-item">
                    <span>Text Chat</span>
                    <strong>★ {f.text_chat_rating} / 5</strong>
                  </div>
                  <div className="feedback-score-item">
                    <span>AI Advisor</span>
                    <strong>★ {f.ai_advisor_rating} / 5</strong>
                  </div>
                  <div className="feedback-score-item">
                    <span>Ease of Use</span>
                    <strong>★ {f.user_friendly_rating} / 5</strong>
                  </div>
                  <div className="feedback-score-item">
                    <span>Document OCR</span>
                    <strong>★ {f.document_extraction_rating} / 5</strong>
                  </div>
                  <div className="feedback-score-item">
                    <span>Multilingual</span>
                    <strong>★ {f.multilingual_rating} / 5</strong>
                  </div>
                </div>

                {/* Most valuable feature */}
                {f.most_valuable_feature && (
                  <div className="feedback-valuable-feature">
                    Most Valued Feature: <strong>{f.most_valuable_feature}</strong>
                  </div>
                )}

                {/* User suggestions & written feedback */}
                {f.suggestions ? (
                  <div className="feedback-comment-box">
                    "{f.suggestions}"
                  </div>
                ) : (
                  <div style={{ fontSize: "12px", color: "var(--muted)", fontStyle: "italic" }}>
                    No written suggestions provided.
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // USER SUBMISSION VIEW (Or Admin previewing the form)
  // ─────────────────────────────────────────────────────────────
  if (submitted) {
    return (
      <div className="feedback-screen">
        <div className="feedback-success-card">
          <div className="success-icon">🎉</div>
          <h2>Thank you for your feedback!</h2>
          <p>Your honest ratings and suggestions have been securely recorded. They help us make Fin and InvestRight significantly more accessible and helpful for everyone.</p>
          <div style={{ display: "flex", gap: "10px", justifyContent: "center", marginTop: "20px" }}>
            {isAdmin && (
              <button className="btn-outline" onClick={() => { setSubmitted(false); setShowSurveyForm(false); }}>
                ← View All Responses
              </button>
            )}
            <button className="btn" onClick={() => (onDone ? onDone() : setSubmitted(false))}>
              Back to Dashboard →
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-screen">
      <div className="feedback-hero">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <span className="header-kicker">USER EXPERIENCE SURVEY</span>
            <h2>Your Experience & Feedback</h2>
            <p>
              Help us evaluate and improve InvestRight. Please rate your experience with Fin across speech, text, AI accuracy, and document extraction.
            </p>
          </div>
          {isAdmin && (
            <button className="btn-outline" onClick={() => setShowSurveyForm(false)}>
              ← Back to Admin Responses
            </button>
          )}
        </div>
      </div>

      {error && <div className="auth-error" style={{ margin: "16px 0" }}>⚠️ {error}</div>}

      <form onSubmit={handleSubmit} className="feedback-form">
        {/* 1. Overall */}
        {renderStars("overall_rating", "1. Overall Application Experience", "How would you rate your overall journey using InvestRight?")}

        {/* 2. Voice */}
        {renderStars("voice_feature_rating", "2. Voice Input & Speech Recognition", "How accurately and smoothly did the microphone pick up your voice?")}

        {/* 3. Text Chat */}
        {renderStars("text_chat_rating", "3. Conversational Text Chat", "How natural and responsive was the chat flow during onboarding and Q&A?")}

        {/* 4. AI Advisor */}
        {renderStars("ai_advisor_rating", "4. AI Advisor (Fin) Quality & Groundedness", "How clear, helpful, and trustworthy were Fin's financial calculations and advice?")}

        {/* 5. User-Friendly Design */}
        {renderStars("user_friendly_rating", "5. Ease of Use & Navigation", "Was the layout, cashflow visualization, and interface intuitive?")}

        {/* 6. Document OCR */}
        {renderStars("document_extraction_rating", "6. Payslip & Document Extraction", "How well did the system identify figures from your uploaded files/images?")}

        {/* 7. Multilingual */}
        {renderStars("multilingual_rating", "7. Multilingual Support (English, Tamil, Malayalam, Kannada)", "How accurate were the translations and local language voice interaction?")}

        {/* 8. NPS */}
        <div className="feedback-question-card">
          <div className="feedback-q-header">
            <label className="feedback-q-title">8. Likelihood to Recommend (NPS)</label>
            <span className="feedback-rating-badge">{form.nps_score} / 10</span>
          </div>
          <p className="feedback-q-desc">How likely are you to recommend InvestRight to friends or family? (1 = Not likely, 10 = Extremely likely)</p>
          <div className="nps-scale">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
              <button
                key={num}
                type="button"
                className={`nps-btn ${form.nps_score === num ? "selected" : ""}`}
                onClick={() => setForm((prev) => ({ ...prev, nps_score: num }))}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* 9. Feature Choice */}
        <div className="feedback-question-card">
          <label className="feedback-q-title">9. What feature did you find most valuable?</label>
          <div className="chip-row" style={{ marginTop: 12 }}>
            {FEATURE_CHOICES.map((choice) => (
              <button
                key={choice}
                type="button"
                className={`chip ${form.most_valuable_feature === choice ? "active" : ""}`}
                style={form.most_valuable_feature === choice ? { background: "var(--teal)", color: "#fff", borderColor: "var(--teal)" } : {}}
                onClick={() => setForm((prev) => ({ ...prev, most_valuable_feature: choice }))}
              >
                {choice}
              </button>
            ))}
          </div>
        </div>

        {/* 10. Open Feedback */}
        <div className="feedback-question-card">
          <label className="feedback-q-title">10. Suggestions or Improvements</label>
          <p className="feedback-q-desc">Anything you would like us to add, improve, or change?</p>
          <textarea
            rows="4"
            className="feedback-textarea"
            placeholder="Share your ideas, comments, or any issues you encountered..."
            value={form.suggestions}
            onChange={(e) => setForm((prev) => ({ ...prev, suggestions: e.target.value }))}
          />
        </div>

        <button type="submit" className="btn btn-block" disabled={submitting} style={{ padding: "16px", fontSize: "16px", marginTop: "12px" }}>
          {submitting ? "Submitting Review..." : "Submit Experience Feedback →"}
        </button>
      </form>
    </div>
  );
}

