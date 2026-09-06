import { useState } from "react";
import { api } from "../api/client";

const FEATURE_CHOICES = [
  "Tamil / Regional Voice Input",
  "Payslip / Document OCR Scanner",
  "Conversational AI Financial Advice",
  "Disciplined Risk Profiling",
  "Clean Modern Dashboard & Cashflow Visuals",
];

export default function Feedback({ onDone }) {
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
    } catch (err) {
      setError(err.message || "Could not submit feedback. Please try again.");
    } finally {
      setSubmitting(false);
    }
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

  if (submitted) {
    return (
      <div className="feedback-screen">
        <div className="feedback-success-card">
          <div className="success-icon">🎉</div>
          <h2>Thank you for your feedback!</h2>
          <p>Your honest ratings and suggestions have been securely recorded. They help us make Fin and InvestRight significantly more accessible and helpful for everyone.</p>
          <button className="btn" style={{ marginTop: 20 }} onClick={() => (onDone ? onDone() : setSubmitted(false))}>
            Back to Dashboard →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-screen">
      <div className="feedback-hero">
        <span className="header-kicker">USER EXPERIENCE SURVEY</span>
        <h2>Your Experience & Feedback</h2>
        <p>
          Help us evaluate and improve InvestRight. Please rate your experience with Fin across speech, text, AI accuracy, and document extraction.
        </p>
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
