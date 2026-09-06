import { useState } from "react";

export default function Consent({ onAccept }) {
  const [checked, setChecked] = useState(false);

  return (
    <div className="consent">
      <div>
        <div className="consent-icon">🛡️</div>
        <h2>Before we start</h2>
        <div className="consent-body">
          Fin analyzes the financial information you share to suggest a risk profile
          and investment category. This is <strong>decision-support guidance, not
          licensed financial advice</strong>, and no recommendation guarantees future
          investment performance. Verify details with the relevant platform or a
          licensed advisor before acting.
        </div>
        <label className="consent-check">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
          />
          <span>
            I understand this is decision support, not financial advice, and I
            consent to my financial data being processed for this purpose.
          </span>
        </label>
      </div>
      <button className="btn btn-block" disabled={!checked} onClick={onAccept}>
        Continue
      </button>
    </div>
  );
}
