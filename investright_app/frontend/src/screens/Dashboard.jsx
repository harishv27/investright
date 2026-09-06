import { useEffect, useState } from "react";
import { api } from "../api/client";

const RISK_COLORS = {
  Conservative: "#1F6F5C",
  Moderate:     "#B8892B",
  Aggressive:   "#A94438",
};

const RISK_EMOJI = {
  Conservative: "🛡️",
  Moderate:     "⚖️",
  Aggressive:   "🚀",
};

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="stat-card">
      <div className="label">{label}</div>
      <div className={`value${accent ? " pos" : ""}`}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

export default function Dashboard({ data, onRefresh }) {
  const [portfolio, setPortfolio] = useState(null);
  const [showHoldingForm, setShowHoldingForm] = useState(false);
  const [holding, setHolding] = useState({
    name: "", asset_type: "Mutual fund", invested_amount: "", current_value: "",
  });
  const [portfolioError, setPortfolioError] = useState("");
  const [savingHolding, setSavingHolding] = useState(false);
  const [goalInputs, setGoalInputs] = useState({
    target: "1000000", years: "5", returnRate: "10", monthly: "",
  });

  useEffect(() => { onRefresh(); }, []); // eslint-disable-line

  const refreshPortfolio = async () => {
    try { setPortfolio(await api.getPortfolio()); }
    catch (error) { setPortfolioError(error.message); }
  };

  useEffect(() => { refreshPortfolio(); }, []);

  const addHolding = async (event) => {
    event.preventDefault();
    setPortfolioError("");
    setSavingHolding(true);
    try {
      await api.addHolding({
        ...holding,
        invested_amount: Number(holding.invested_amount),
        current_value: Number(holding.current_value),
      });
      setHolding({ name: "", asset_type: "Mutual fund", invested_amount: "", current_value: "" });
      setShowHoldingForm(false);
      await refreshPortfolio();
    } catch (error) { setPortfolioError(error.message); }
    finally { setSavingHolding(false); }
  };

  const deleteHolding = async (id) => { await api.deleteHolding(id); await refreshPortfolio(); };

  // ── Empty state ──────────────────────────────────────────────────────────────
  if (!data) {
    return (
      <div className="dash-screen">
        <div className="dash-empty-state">
          <div className="dash-empty-icon">🌱</div>
          <div className="dash-empty-title">Your dashboard is getting ready!</div>
          <p className="dash-empty-sub">
            Chat with Fin to share your income, expenses and risk preferences — your
            personalised financial snapshot will appear here.
          </p>
          <div className="dash-empty-steps">
            <div className="dash-step"><span>1</span> Share your income &amp; expenses</div>
            <div className="dash-step"><span>2</span> Answer 4 risk questions</div>
            <div className="dash-step"><span>3</span> Get your investment match</div>
          </div>
        </div>
      </div>
    );
  }

  const {
    monthly_savings, savings_rate_pct, expense_ratio_pct, investment_capacity,
    risk_score, risk_category, recommended_category, recommendation_rationale,
    recommendation_history, capacity_score, capacity_category, emergency_months,
    capacity_guidance, evidence_count, decision_risk_category, decision_risk_explanation,
  } = data;

  // Goal planner calc
  const goalTarget    = Number(goalInputs.target) || 0;
  const goalYears     = Number(goalInputs.years) || 0;
  const annualReturn  = (Number(goalInputs.returnRate) || 0) / 100;
  const monthlySIP    = Number(goalInputs.monthly) || investment_capacity || 0;
  const months        = goalYears * 12;
  const monthlyRate   = annualReturn / 12;
  const futureValue   = months > 0
    ? monthlyRate === 0
      ? monthlySIP * months
      : monthlySIP * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate)
    : 0;
  const requiredMonthly = months > 0
    ? monthlyRate === 0
      ? goalTarget / months
      : goalTarget * monthlyRate / (Math.pow(1 + monthlyRate, months) - 1)
    : 0;

  const color = RISK_COLORS[risk_category] || "#1F6F5C";
  const pct   = risk_score ? risk_score / 25 : 0;
  const circ  = 2 * Math.PI * 15.5;

  const savingsHealth = savings_rate_pct >= 30 ? "excellent" : savings_rate_pct >= 20 ? "good" : savings_rate_pct >= 10 ? "ok" : "low";
  const savingsHint   = { excellent: "Excellent! 🌟", good: "Good job! 👍", ok: "Room to improve", low: "Let's work on this" };

  const incomeEst = savings_rate_pct > 0 ? (monthly_savings * 100) / savings_rate_pct : 0;
  const expensesEst = incomeEst > 0 ? incomeEst - monthly_savings : 0;

  return (
    <div className="dash-screen">
      <div className="dash-title">Your snapshot</div>

      {/* ── Key stats & Cashflow ── */}
      <div className="card cashflow-card">
        <h3>Monthly cashflow</h3>
        <div className="cashflow-bar-wrap">
          <div className="cashflow-bar">
            <div className="cashflow-bar-spent" style={{ width: `${Math.min(100, expense_ratio_pct)}%` }}></div>
            <div className="cashflow-bar-saved" style={{ width: `${Math.max(0, 100 - expense_ratio_pct)}%` }}></div>
          </div>
          <div className="cashflow-labels">
            <div>
              <span className="dot spent"></span> Expenses
              <strong>₹{Math.round(expensesEst).toLocaleString("en-IN")}</strong>
            </div>
            <div style={{ textAlign: "right" }}>
              <strong>₹{Math.round(incomeEst).toLocaleString("en-IN")}</strong>
              Income <span className="dot saved"></span>
            </div>
          </div>
        </div>
      </div>

      <div className="stat-row">
        <StatCard
          label="Monthly savings"
          value={`₹${Math.round(monthly_savings).toLocaleString("en-IN")}`}
          sub={savingsHint[savingsHealth]}
          accent
        />
        <StatCard
          label="Savings rate"
          value={`${savings_rate_pct}%`}
          sub={`Expense ratio ${expense_ratio_pct}%`}
        />
      </div>
      <div className="stat-row">
        <StatCard
          label="Free to invest"
          value={`₹${Math.round(investment_capacity).toLocaleString("en-IN")}`}
          sub="After planned SIP"
        />
        <StatCard
          label="Emergency buffer"
          value={emergency_months ? `${emergency_months} mo` : "—"}
          sub={capacity_category || "Calculate below"}
        />
      </div>

      {/* ── Risk profile ── */}
      {risk_category && (
        <div className="card risk-card">
          <h3>Your risk profile</h3>
          <div className="gauge-row">
            <svg width="70" height="70" viewBox="0 0 36 36">
              <circle cx="18" cy="18" r="15.5" fill="none" stroke="#E1E0D8" strokeWidth="4" />
              <circle
                cx="18" cy="18" r="15.5" fill="none" stroke={color} strokeWidth="4"
                strokeDasharray={`${pct * circ} ${circ}`}
                strokeLinecap="round" transform="rotate(-90 18 18)"
              />
              <text x="18" y="21" textAnchor="middle" fontSize="9" fill="#16283D" fontFamily="IBM Plex Mono">
                {risk_score}
              </text>
            </svg>
            <div>
              <div className="gauge-cat-big" style={{ color }}>
                {RISK_EMOJI[risk_category]} {risk_category}
              </div>
              <div className="gauge-sub">Willingness score {risk_score} / 25</div>
            </div>
          </div>
          {decision_risk_category && decision_risk_category !== risk_category && (
            <div className="decision-note">
              <strong>⚠️ Guardrail applied: {decision_risk_category}</strong>
              <span>{decision_risk_explanation}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Recommendation ── */}
      {recommended_category && (
        <div className="card rec-card">
          <div className="rec-eyebrow">✨ RECOMMENDED FOR YOU</div>
          <div className="rec-title">{recommended_category}</div>
          <p className="rec-text">{recommendation_rationale}</p>
          <div className="chips-static">
            <span className="chip-static" style={{ color, borderColor: color }}>
              {risk_category} risk
            </span>
            {capacity_category && (
              <span className="chip-static">{capacity_category} capacity</span>
            )}
          </div>
        </div>
      )}

      {/* ── Financial capacity ── */}
      <div className="card capacity-card">
        <div className="section-heading">
          <h3>Financial capacity</h3>
          <span className="planner-badge">
            {evidence_count > 0 ? `${evidence_count} evidence confirmed` : "Self-reported"}
          </span>
        </div>
        <div className="capacity-summary">
          <div>
            <strong>{capacity_category || "Pending"}</strong>
            <span>{capacity_score ?? "--"} / 100</span>
          </div>
          <div className="capacity-meter">
            <i style={{ width: `${Math.min(100, capacity_score || 0)}%` }} />
          </div>
        </div>
        <p className="planner-note">
          {capacity_guidance || "Complete your financial profile to calculate capacity."}
        </p>
      </div>

      {/* ── Portfolio tracker ── */}
      <div className="card portfolio-card">
        <div className="section-heading">
          <h3>Portfolio tracker</h3>
          <button className="mini-btn" onClick={() => setShowHoldingForm((v) => !v)}>
            {showHoldingForm ? "✕ Close" : "+ Add holding"}
          </button>
        </div>

        {portfolio && portfolio.holdings.length > 0 ? (
          <>
            <div className="portfolio-total-row">
              <div>
                <span className="label">Current value</span>
                <strong>₹{Math.round(portfolio.current_value).toLocaleString("en-IN")}</strong>
              </div>
              <div className={portfolio.return_amount >= 0 ? "portfolio-gain" : "portfolio-loss"}>
                {portfolio.return_amount >= 0 ? "+" : "-"}₹{Math.abs(Math.round(portfolio.return_amount)).toLocaleString("en-IN")} ({portfolio.return_pct}%)
              </div>
            </div>
            <div className="holding-list">
              {portfolio.holdings.map((item) => (
                <div className="holding-row" key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.asset_type} · Invested ₹{Math.round(item.invested_amount).toLocaleString("en-IN")}</span>
                  </div>
                  <div className={item.return_amount >= 0 ? "portfolio-gain" : "portfolio-loss"}>
                    {item.return_pct}%{" "}
                    <button className="holding-delete" aria-label={`Delete ${item.name}`} onClick={() => deleteHolding(item.id)}>×</button>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="portfolio-empty">
            📂 No holdings yet — track your mutual funds, stocks, or FDs here.
          </div>
        )}

        {portfolioError && <div className="auth-error">{portfolioError}</div>}

        {showHoldingForm && (
          <form className="holding-form" onSubmit={addHolding}>
            <input required placeholder="Investment name (e.g. Axis Bluechip Fund)" value={holding.name} onChange={(e) => setHolding({ ...holding, name: e.target.value })} />
            <select value={holding.asset_type} onChange={(e) => setHolding({ ...holding, asset_type: e.target.value })}>
              <option>Mutual fund</option>
              <option>Stock</option>
              <option>ETF</option>
              <option>Fixed deposit</option>
              <option>Gold</option>
              <option>Other</option>
            </select>
            <input required min="1" type="number" placeholder="Amount invested (₹)" value={holding.invested_amount} onChange={(e) => setHolding({ ...holding, invested_amount: e.target.value })} />
            <input required min="0" type="number" placeholder="Current value (₹)" value={holding.current_value} onChange={(e) => setHolding({ ...holding, current_value: e.target.value })} />
            <button className="btn btn-block" disabled={savingHolding}>
              {savingHolding ? "Adding…" : "Add to portfolio →"}
            </button>
          </form>
        )}
      </div>

      {/* ── Goal planner ── */}
      <div className="card goal-card">
        <div className="section-heading">
          <h3>Goal planner 🎯</h3>
          <span className="planner-badge">SIP estimate</span>
        </div>
        <p className="planner-note" style={{ marginBottom: 12 }}>
          Play with the numbers to see how your goal stacks up.
        </p>
        <div className="goal-form-grid">
          <label>
            Target amount
            <input type="number" min="1" value={goalInputs.target} onChange={(e) => setGoalInputs({ ...goalInputs, target: e.target.value })} />
          </label>
          <label>
            Years
            <input type="number" min="1" max="60" value={goalInputs.years} onChange={(e) => setGoalInputs({ ...goalInputs, years: e.target.value })} />
          </label>
          <label>
            Expected return %
            <input type="number" min="0" max="50" step="0.5" value={goalInputs.returnRate} onChange={(e) => setGoalInputs({ ...goalInputs, returnRate: e.target.value })} />
          </label>
          <label>
            Your monthly SIP
            <input
              type="number"
              min="0"
              value={goalInputs.monthly || Math.round(investment_capacity)}
              placeholder={Math.round(investment_capacity)}
              onChange={(e) => setGoalInputs({ ...goalInputs, monthly: e.target.value })}
            />
          </label>
        </div>
        <div className="goal-result">
          <div>
            <span className="label">Estimated corpus</span>
            <strong>₹{Math.round(futureValue).toLocaleString("en-IN")}</strong>
          </div>
          <div>
            <span className="label">Required monthly SIP</span>
            <strong>₹{Math.round(requiredMonthly).toLocaleString("en-IN")}</strong>
          </div>
        </div>
        <p className="planner-note">
          📌 Illustration only. Actual returns vary. Not financial advice.
        </p>
      </div>

      {/* ── Recommendation history ── */}
      {recommendation_history?.length > 0 && (
        <div className="card">
          <h3>Recommendation history</h3>
          <div className="history-list">
            {recommendation_history.map((item, index) => (
              <div className="history-row" key={`${item.created_at}-${index}`}>
                <div>
                  <strong>{item.category}</strong>
                  <span>{new Date(item.created_at).toLocaleDateString("en-IN")}</span>
                </div>
                <div className="history-rationale">{item.rationale}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── How Fin works ── */}
      <div className="card how-card">
        <h3>🔍 How Fin got here</h3>
        <p style={{ fontSize: 12.5, color: "var(--muted)", lineHeight: 1.65, margin: 0 }}>
          Every number above comes from <strong>deterministic calculations</strong>, not AI guesses.
          The risk category, savings rate, capacity score — all computed from the numbers you provided.
          Ask Fin in the Chat tab for a plain-language breakdown and it'll show exactly which tools it used.
        </p>
      </div>
    </div>
  );
}
