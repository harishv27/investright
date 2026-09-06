import { useState, useRef, useEffect, useMemo } from "react";
import { api } from "../api/client";
import { t } from "./translations";

// ─── Quiz questions ────────────────────────────────────────────────────────────
const QUIZ_QUESTIONS = [
  {
    q: "If your portfolio dropped 20% in one month, what would you do?",
    opts: [
      { t: "😱 Sell everything now", v: 1 },
      { t: "😬 Sell some to limit losses", v: 2 },
      { t: "😐 Hold and wait it out", v: 3 },
      { t: "🙂 Stay calm, not worried", v: 4 },
      { t: "😎 Buy more at the dip!", v: 5 },
    ],
  },
  {
    q: "How much investing experience do you have?",
    opts: [
      { t: "None at all", v: 1 },
      { t: "A little", v: 2 },
      { t: "Some (MFs, stocks)", v: 3 },
      { t: "Considerable", v: 4 },
      { t: "A lot", v: 5 },
    ],
  },
  {
    q: "How okay are you with month-to-month ups and downs?",
    opts: [
      { t: "Very uncomfortable", v: 1 },
      { t: "A bit uneasy", v: 2 },
      { t: "Neutral — okay-ish", v: 3 },
      { t: "Comfortable", v: 4 },
      { t: "Totally fine with it", v: 5 },
    ],
  },
  {
    q: "When might you urgently need this money?",
    opts: [
      { t: "Within a year", v: 1 },
      { t: "1–3 years", v: 2 },
      { t: "3–5 years", v: 3 },
      { t: "5–10 years", v: 4 },
      { t: "10+ years away", v: 5 },
    ],
  },
];

// ─── Income categories ─────────────────────────────────────────────────────────
const INCOME_CATEGORIES = [
  { key: "salary",    icon: "💼", label: "Fixed salary / take-home",    hint: "e.g. 60000" },
  { key: "business",  icon: "🏪", label: "Business / self-employment",   hint: "e.g. 30000" },
  { key: "freelance", icon: "💻", label: "Freelancing / consulting",      hint: "e.g. 15000" },
  { key: "rental",    icon: "🏘️", label: "Rental income",                hint: "e.g. 10000" },
  { key: "interest",  icon: "📈", label: "Interest / dividends",          hint: "e.g. 2000"  },
];

// ─── Expense categories ────────────────────────────────────────────────────────
const EXPENSE_CATEGORIES = [
  { key: "rent",          icon: "🏠", label: "Rent / home loan EMI",    hint: "e.g. 12000" },
  { key: "food",          icon: "🍱", label: "Food & dining out",        hint: "e.g. 5000"  },
  { key: "groceries",     icon: "🛒", label: "Groceries",                hint: "e.g. 3000"  },
  { key: "transport",     icon: "🚌", label: "Transport / fuel",         hint: "e.g. 2000"  },
  { key: "utilities",     icon: "💡", label: "Utilities & internet",     hint: "e.g. 1500"  },
  { key: "entertainment", icon: "🎬", label: "Movies & entertainment",   hint: "e.g. 1000"  },
  { key: "medical",       icon: "💊", label: "Medical & health",         hint: "e.g. 500"   },
  { key: "emis",          icon: "💳", label: "Loan EMIs (other)",        hint: "e.g. 3000"  },
];

// ─── Horizon options ───────────────────────────────────────────────────────────
const HORIZON_OPTIONS = [
  { label: "< 1 year",  sub: "Very short term",  years: 1,  icon: "⚡" },
  { label: "1–3 yrs",   sub: "Short term",        years: 2,  icon: "🌱" },
  { label: "3–5 yrs",   sub: "Medium term",       years: 4,  icon: "🌿" },
  { label: "5–10 yrs",  sub: "Long term",         years: 7,  icon: "🌳" },
  { label: "10+ yrs",   sub: "Very long term",    years: 15, icon: "🏔️" },
];

// ─── Goal options ──────────────────────────────────────────────────────────────
const GOAL_OPTIONS = [
  { t: "🛡️ Keep my money safe",        v: "Capital preservation" },
  { t: "⚖️ Grow steadily, not too risky", v: "Balanced growth"    },
  { t: "🚀 Build long-term wealth",    v: "Long-term wealth"      },
  { t: "💰 Regular passive income",    v: "Income generation"     },
  { t: "🏠 Buy a house",               v: "House purchase"        },
  { t: "🎓 Child's education",         v: "Child education"       },
  { t: "✈️ Travel / big purchase",     v: "Travel / lifestyle"    },
  { t: "🧘 Retirement",                v: "Retirement"            },
];

// ─── Script ────────────────────────────────────────────────────────────────────
function buildScript(lang) {
  const script = [
    {
      bot: t(lang, "greeting"),
      type: "choice",
      options: [{ t: t(lang, "lets_go") }, { t: t(lang, "sure_go") }],
    },
    {
      bot: t(lang, "income_q"),
      type: "income",
    },
    {
      bot: t(lang, "expense_q"),
      type: "expenses",
    },
    {
      bot: t(lang, "savings_q"),
      type: "number",
      field: "savings",
      placeholder: "e.g. 250000",
    },
    {
      bot: t(lang, "invest_q"),
      type: "number",
      field: "planned_investment",
      placeholder: "e.g. 5000",
    },
    {
      bot: t(lang, "goal_q"),
      type: "goal",
    },
    {
      bot: t(lang, "horizon_q"),
      type: "horizon",
    },
    {
      bot: t(lang, "risk_q"),
      type: "choice",
      options: [{ t: t(lang, "lets_do_it") }],
    },
  ];
  QUIZ_QUESTIONS.forEach((q, idx) =>
    script.push({ bot: t(lang, `quiz_${idx+1}`), type: "choice", quiz: true, options: q.opts.map((o, i) => ({ t: t(lang, `quiz_${idx+1}_o${i+1}`), v: o.v })) })
  );
  script.push({ bot: "__RESULT__" });
  return script;
}

function indianizeCurrency(text) {
  return text.replace(/\$/g, "₹").replace(/\bUSD\b/gi, "INR").replace(/\bdollars?\b/gi, "rupees");
}

function fmt(n) {
  return Number(n || 0).toLocaleString("en-IN");
}

// ─── IncomeBreakdown component ─────────────────────────────────────────────────
function IncomeBreakdown({ onDone }) {
  const [cats, setCats] = useState(() =>
    Object.fromEntries(INCOME_CATEGORIES.map((c) => [c.key, ""]))
  );
  const [extra, setExtra] = useState("");
  const [extraLabel, setExtraLabel] = useState("");
  const [extras, setExtras] = useState([]);
  const [showExtraForm, setShowExtraForm] = useState(false);
  const [inputFocus, setInputFocus] = useState(null);

  const total =
    INCOME_CATEGORIES.reduce((s, c) => s + (Number(cats[c.key]) || 0), 0) +
    extras.reduce((s, e) => s + (Number(e.amount) || 0), 0);

  const handleAddExtra = () => {
    const amt = Number(extra);
    if (!extraLabel.trim() || !amt) return;
    setExtras((prev) => [...prev, { label: extraLabel.trim(), amount: amt }]);
    setExtra(""); setExtraLabel(""); setShowExtraForm(false);
  };

  const removeExtra = (idx) => setExtras((prev) => prev.filter((_, i) => i !== idx));

  const handleDone = () => {
    if (total === 0) return;
    const breakdown = {
      ...Object.fromEntries(INCOME_CATEGORIES.map((c) => [c.key, Number(cats[c.key]) || 0])),
      extras,
      total,
    };
    onDone(total, breakdown);
  };

  return (
    <div className="expense-breakdown">
      <div className="expense-grid">
        {INCOME_CATEGORIES.map((cat) => (
          <div
            key={cat.key}
            className={`expense-cat-row${inputFocus === cat.key ? " focused" : ""}${Number(cats[cat.key]) > 0 ? " has-value" : ""}`}
          >
            <span className="cat-icon">{cat.icon}</span>
            <span className="cat-label">{t(language, `inc_${cat.key}`)}</span>
            <div className="cat-input-wrap">
              <span className="rupee-prefix">₹</span>
              <input
                type="number"
                inputMode="numeric"
                placeholder={cat.hint}
                value={cats[cat.key]}
                onFocus={() => setInputFocus(cat.key)}
                onBlur={() => setInputFocus(null)}
                onChange={(e) => setCats((prev) => ({ ...prev, [cat.key]: e.target.value }))}
              />
            </div>
          </div>
        ))}

        {extras.map((e, idx) => (
          <div key={idx} className="expense-cat-row has-value extra-row">
            <span className="cat-icon">➕</span>
            <span className="cat-label">{e.label}</span>
            <div className="cat-input-wrap">
              <span className="rupee-prefix">₹</span>
              <span className="extra-amount">{fmt(e.amount)}</span>
              <button className="remove-extra" onClick={() => removeExtra(idx)} title="Remove">✕</button>
            </div>
          </div>
        ))}

        {showExtraForm ? (
          <div className="extra-form">
            <input
              type="text"
              placeholder="Category name"
              value={extraLabel}
              onChange={(e) => setExtraLabel(e.target.value)}
              className="extra-label-input"
            />
            <div className="cat-input-wrap">
              <span className="rupee-prefix">₹</span>
              <input
                type="number"
                inputMode="numeric"
                placeholder="Monthly amount"
                value={extra}
                onChange={(e) => setExtra(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddExtra()}
              />
            </div>
            <div className="extra-form-btns">
              <button className="chip" onClick={handleAddExtra}>{t(language, "add")} ✓</button>
              <button className="chip ghost" onClick={() => { setShowExtraForm(false); setExtra(""); setExtraLabel(""); }}>Cancel</button>
            </div>
          </div>
        ) : (
          <button className="add-expense-btn" onClick={() => setShowExtraForm(true)}>
            + {t(language, "add_extra")}
          </button>
        )}
      </div>

      <div className="expense-total-row">
        <div className="expense-total-label">
          <span>{t(language, "total_income")}</span>
          <span className="expense-total-amt income-total">₹{fmt(total)}</span>
        </div>
        <button className="btn" style={{ marginTop: 10 }} disabled={total === 0} onClick={handleDone}>
          {t(language, "done")} →
        </button>
      </div>
    </div>
  );
}

// ─── ExpenseBreakdown component ────────────────────────────────────────────────
function ExpenseBreakdown({ onDone, language }) {
  const [cats, setCats] = useState(() =>
    Object.fromEntries(EXPENSE_CATEGORIES.map((c) => [c.key, ""]))
  );
  const [extra, setExtra] = useState("");
  const [extraLabel, setExtraLabel] = useState("");
  const [extras, setExtras] = useState([]);
  const [showExtraForm, setShowExtraForm] = useState(false);
  const [inputFocus, setInputFocus] = useState(null);

  const total =
    EXPENSE_CATEGORIES.reduce((s, c) => s + (Number(cats[c.key]) || 0), 0) +
    extras.reduce((s, e) => s + (Number(e.amount) || 0), 0);

  const handleAddExtra = () => {
    const amt = Number(extra);
    if (!extraLabel.trim() || !amt) return;
    setExtras((prev) => [...prev, { label: extraLabel.trim(), amount: amt }]);
    setExtra(""); setExtraLabel(""); setShowExtraForm(false);
  };

  const removeExtra = (idx) => setExtras((prev) => prev.filter((_, i) => i !== idx));

  const handleDone = () => {
    if (total === 0) return;
    const breakdown = {
      ...Object.fromEntries(EXPENSE_CATEGORIES.map((c) => [c.key, Number(cats[c.key]) || 0])),
      extras,
      total,
    };
    onDone(total, breakdown, language);
  };

  return (
    <div className="expense-breakdown">
      <div className="expense-grid">
        {EXPENSE_CATEGORIES.map((cat) => (
          <div
            key={cat.key}
            className={`expense-cat-row${inputFocus === cat.key ? " focused" : ""}${Number(cats[cat.key]) > 0 ? " has-value" : ""}`}
          >
            <span className="cat-icon">{cat.icon}</span>
            <span className="cat-label">{t(language, `exp_${cat.key}`)}</span>
            <div className="cat-input-wrap">
              <span className="rupee-prefix">₹</span>
              <input
                type="number"
                inputMode="numeric"
                placeholder={cat.hint}
                value={cats[cat.key]}
                onFocus={() => setInputFocus(cat.key)}
                onBlur={() => setInputFocus(null)}
                onChange={(e) => setCats((prev) => ({ ...prev, [cat.key]: e.target.value }))}
              />
            </div>
          </div>
        ))}

        {extras.map((e, idx) => (
          <div key={idx} className="expense-cat-row has-value extra-row">
            <span className="cat-icon">➕</span>
            <span className="cat-label">{e.label}</span>
            <div className="cat-input-wrap">
              <span className="rupee-prefix">₹</span>
              <span className="extra-amount">{fmt(e.amount)}</span>
              <button className="remove-extra" onClick={() => removeExtra(idx)} title="Remove">✕</button>
            </div>
          </div>
        ))}

        {showExtraForm ? (
          <div className="extra-form">
            <input
              type="text"
              placeholder="Category name"
              value={extraLabel}
              onChange={(e) => setExtraLabel(e.target.value)}
              className="extra-label-input"
            />
            <div className="cat-input-wrap">
              <span className="rupee-prefix">₹</span>
              <input
                type="number"
                inputMode="numeric"
                placeholder="Monthly amount"
                value={extra}
                onChange={(e) => setExtra(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddExtra()}
              />
            </div>
            <div className="extra-form-btns">
              <button className="chip" onClick={handleAddExtra}>{t(language, "add")} ✓</button>
              <button className="chip ghost" onClick={() => { setShowExtraForm(false); setExtra(""); setExtraLabel(""); }}>Cancel</button>
            </div>
          </div>
        ) : (
          <button className="add-expense-btn" onClick={() => setShowExtraForm(true)}>
            + {t(language, "add_extra")}
          </button>
        )}
      </div>

      <div className="expense-total-row">
        <div className="expense-total-label">
          <span>{t(language, "total_expenses")}</span>
          <span className="expense-total-amt">₹{fmt(total)}</span>
        </div>
        <button className="btn" style={{ marginTop: 10 }} disabled={total === 0} onClick={handleDone}>
          {t(language, "done")} →
        </button>
      </div>
    </div>
  );
}

// ─── HorizonPicker component ───────────────────────────────────────────────────
function HorizonPicker({ onDone, language }) {
  const [selected, setSelected] = useState(null);

  const handleSelect = (opt) => {
    setSelected(opt.years);
    setTimeout(() => onDone(opt.label, opt.years), 280);
  };

  const getSubKey = (years) => {
    if (years === 1) return "hz_vshort";
    if (years === 2) return "hz_short";
    if (years === 4) return "hz_med";
    if (years === 7) return "hz_long";
    if (years === 15) return "hz_vlong";
    return "";
  };

  return (
    <div className="horizon-picker">
      {HORIZON_OPTIONS.map((opt) => (
        <button
          key={opt.years}
          className={`horizon-opt${selected === opt.years ? " selected" : ""}`}
          onClick={() => handleSelect(opt)}
        >
          <span className="horizon-icon">{opt.icon}</span>
          <span className="horizon-label">{opt.label}</span>
          <span className="horizon-sub">{t(language, getSubKey(opt.years))}</span>
        </button>
      ))}
    </div>
  );
}

// ─── Main Chat component ───────────────────────────────────────────────────────
export default function Chat({ mood, onProfileComplete, onViewDashboard, onAuthExpired }) {
  const [language, setLanguage] = useState("en-IN");
  const script = useMemo(() => buildScript(language), [language]);
  
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem("fin_chat_msgs");
    return saved ? JSON.parse(saved) : [{ role: "bot", text: buildScript("en-IN")[0].bot }];
  });
  const [step, setStep] = useState(() => Number(localStorage.getItem("fin_chat_step")) || 0);
  const [phase, setPhase] = useState(() => localStorage.getItem("fin_chat_phase") || "onboarding");
  const [profile, setProfile] = useState(() => JSON.parse(localStorage.getItem("fin_chat_profile") || "{}"));
  const [riskResponses, setRiskResponses] = useState(() => JSON.parse(localStorage.getItem("fin_chat_risk") || "[]"));
  
  const [textValue, setTextValue] = useState("");
  const [freeText, setFreeText] = useState("");
  const [asking, setAsking] = useState(false);
  const [lastSources, setLastSources] = useState([]);
  const [extracting, setExtracting] = useState(false);
  const [extraction, setExtraction] = useState(null);
  const [listening, setListening] = useState(false);
  const [result, setResult] = useState(null);
  const scrollRef = useRef(null);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);
  const current = script[step];
  const voiceSupported =
    typeof window !== "undefined" &&
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);

  // Persist state
  useEffect(() => {
    localStorage.setItem("fin_chat_msgs", JSON.stringify(messages));
    localStorage.setItem("fin_chat_step", step.toString());
    localStorage.setItem("fin_chat_phase", phase);
    localStorage.setItem("fin_chat_profile", JSON.stringify(profile));
    localStorage.setItem("fin_chat_risk", JSON.stringify(riskResponses));
  }, [messages, step, phase, profile, riskResponses]);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, phase, extraction]);

  useEffect(() => {
    let mounted = true;
    Promise.all([api.getConversations(), api.getProfile()])
      .then(([history, savedProfile]) => {
        if (!mounted) return;
        // If we have a saved profile but our local phase is onboarding, jump to done
        if (savedProfile && phase === "onboarding") {
          setPhase("done");
          setProfile(savedProfile);
        }
        // If local storage was totally empty but we have backend history, load it
        if (history.length > 0 && messages.length <= 1) {
          setMessages([
            { role: "bot", text: "Welcome back! Here's your previous chat history." },
            ...history.flatMap((item) => [
              { role: "user", text: item.query },
              { role: "bot", text: indianizeCurrency(item.response) },
            ])
          ]);
        }
      })
      .catch(() => {});
    return () => { mounted = false; };
  }, []); // run once on mount

  const handleClearChat = () => {
    if (!window.confirm("Are you sure you want to clear the chat history?")) return;
    const initial = [{ role: "bot", text: script[0].bot }];
    setMessages(initial);
    setStep(0);
    setPhase("onboarding");
    setProfile({});
    setRiskResponses([]);
    setResult(null);
    setLastSources([]);
  };

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return undefined;
    const recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = language;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).map((r) => r[0].transcript).join("");
      if (phase === "onboarding" && current?.type === "number")
        setTextValue(transcript.replace(/[^0-9.]/g, ""));
      else setFreeText(transcript);
    };
    recognitionRef.current = recognition;
    return () => { recognition.abort(); recognitionRef.current = null; };
  }, [phase, step, current ? current.type : null, language]);

  const appendBot = (text) => setMessages((m) => [...m, { role: "bot", text }]);
  const appendUser = (text) => setMessages((m) => [...m, { role: "user", text }]);

  const finishOnboarding = async (finalProfile, finalRiskResponses) => {
    setPhase("submitting");
    try {
      await api.saveProfile({
        income: Number(finalProfile.income),
        expenses: Number(finalProfile.expenses),
        savings: Number(finalProfile.savings),
        planned_investment: Number(finalProfile.planned_investment),
        goal: finalProfile.goal,
        horizon_years: Number(finalProfile.horizon_years),
      });
      const riskResult = await api.submitRiskAssessment(finalRiskResponses);
      const dashboard = await api.getDashboard();
      setResult({ riskResult, dashboard });
      await onProfileComplete();
      setPhase("done");
    } catch (e) {
      appendBot(`Something went wrong saving your profile: ${e.message}`);
      setPhase("onboarding");
    }
  };

  const advance = (nextProfile, nextRisk) => {
    const nextIndex = step + 1;
    setStep(nextIndex);
    const next = script[nextIndex];
    setTimeout(async () => {
      if (!next) return;
      if (next.bot === "__RESULT__") await finishOnboarding(nextProfile, nextRisk);
      else appendBot(next.bot);
    }, 350);
  };

  const handleAnswer = async (display, field, value) => {
    appendUser(display);
    const nextProfile = field ? { ...profile, [field]: value } : profile;
    if (field) setProfile(nextProfile);

    let nextRisk = riskResponses;
    if (script[step].quiz) { nextRisk = [...riskResponses, value]; setRiskResponses(nextRisk); }

    advance(nextProfile, nextRisk);
  };

  // Income done
  const handleIncomeDone = (total, breakdown) => {
    const lines = INCOME_CATEGORIES
      .filter((c) => Number(breakdown[c.key]) > 0)
      .map((c) => `${c.icon} ${c.label}: ₹${fmt(breakdown[c.key])}`);
    breakdown.extras.forEach((e) => lines.push(`➕ ${e.label}: ₹${fmt(e.amount)}`));
    lines.push(`\n💼 Total income: ₹${fmt(total)}`);
    appendUser(lines.join("\n"));

    const nextProfile = { ...profile, income: total };
    setProfile(nextProfile);
    const nextIndex = step + 1;
    setStep(nextIndex);
    const next = script[nextIndex];
    setTimeout(() => { if (next && next.bot !== "__RESULT__") appendBot(next.bot); }, 350);
  };

  // Expenses done
  const handleExpensesDone = (total, breakdown) => {
    const lines = EXPENSE_CATEGORIES
      .filter((c) => Number(breakdown[c.key]) > 0)
      .map((c) => `${c.icon} ${c.label}: ₹${fmt(breakdown[c.key])}`);
    breakdown.extras.forEach((e) => lines.push(`➕ ${e.label}: ₹${fmt(e.amount)}`));
    lines.push(`\n🧾 Total expenses: ₹${fmt(total)}`);
    appendUser(lines.join("\n"));

    const nextProfile = { ...profile, expenses: total };
    setProfile(nextProfile);
    const nextIndex = step + 1;
    setStep(nextIndex);
    const next = script[nextIndex];
    setTimeout(() => { if (next && next.bot !== "__RESULT__") appendBot(next.bot); }, 350);
  };

  // Horizon done
  const handleHorizonDone = (display, years) => {
    appendUser(`${display} — ${years >= 10 ? "Very long term" : years >= 5 ? "Long term" : years >= 3 ? "Medium term" : "Short term"}`);
    const nextProfile = { ...profile, horizon_years: years };
    setProfile(nextProfile);
    const nextIndex = step + 1;
    setStep(nextIndex);
    const next = script[nextIndex];
    setTimeout(() => { if (next && next.bot !== "__RESULT__") appendBot(next.bot); }, 350);
  };

  const submitTextInput = () => {
    const val = textValue.trim();
    if (!val) return;
    const s = script[step];
    setTextValue("");
    handleAnswer(
      `₹${Number(val).toLocaleString("en-IN")}`,
      s.field,
      s.field === "horizon_years" ? val : Number(val)
    );
  };

  const askAgent = async (message) => {
    appendUser(message);
    setFreeText("");
    setAsking(true);
    try {
      const res = await api.askAgent(message);
      appendBot(indianizeCurrency(res.answer));
      setLastSources(res.retrieval_sources || []);
    } catch (e) {
      if (e.status === 401) { onAuthExpired(); return; }
      appendBot(`Sorry, I couldn't reach the advisor: ${e.message}`);
    } finally {
      setAsking(false);
    }
  };

  const toggleVoice = () => {
    if (!recognitionRef.current) return;
    if (listening) recognitionRef.current.stop();
    else recognitionRef.current.start();
  };

  const speak = (text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    window.speechSynthesis.speak(utterance);
  };

  const uploadDocument = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const previewUrl = file.type.startsWith("image/") ? URL.createObjectURL(file) : null;
    setMessages((msgs) => [
      ...msgs,
      { role: "user", kind: "attachment", fileName: file.name, fileType: file.type, previewUrl },
    ]);
    setExtracting(true);
    try {
      setExtraction(await api.extractProfileMedia(file));
    } catch (error) {
      appendBot(`I couldn't read that file: ${error.message}`);
    } finally {
      setExtracting(false);
    }
  };

  const applyExtractedValue = (field, value) => {
    if (value === null || value === undefined) return;
    const fieldMap = { net_pay: "income", gross_earnings: "income" };
    const targetField = fieldMap[field] || field;
    const evidenceId = extraction?.evidence_ids?.[field];
    if (evidenceId) api.confirmEvidence(evidenceId, value).catch(() => {});
    if (["income", "expenses", "savings"].includes(targetField)) {
      setProfile((p) => ({ ...p, [targetField]: value }));
      if (current?.field === targetField) setTextValue(String(value));
    }
  };

  const openUpload = () => fileInputRef.current?.click();

  return (
    <div className="chat-screen">
      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((m, i) =>
          m.kind === "attachment" ? (
            <div className="msg-row user" key={i}>
              <div className="attachment-bubble">
                {m.previewUrl
                  ? <img src={m.previewUrl} alt={`Uploaded ${m.fileName}`} />
                  : <div className="pdf-icon">PDF</div>}
                <div className="attachment-meta">
                  <strong>{m.fileName}</strong>
                  <span>{m.fileType === "application/pdf" ? "PDF document" : "Image"}</span>
                </div>
              </div>
            </div>
          ) : m.role === "bot" ? (
            <div className="msg-row bot" key={i}>
              <div className="avatar-sm">F</div>
              <div className="bubble-wrap">
                <div className="bubble" style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>
                <button className="speak-btn" title="Read aloud" onClick={() => speak(m.text)}>🔊</button>
              </div>
            </div>
          ) : (
            <div className="msg-row user" key={i}>
              <div className="bubble" style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>
            </div>
          )
        )}

        {phase === "submitting" && (
          <div className="msg-row bot">
            <div className="avatar-sm">F</div>
            <div className="bubble">
              <span className="typing-dots"><span /><span /><span /></span>
              Crunching your numbers…
            </div>
          </div>
        )}

        {phase === "done" && result && (
          <>
            <div className="msg-row bot">
              <div className="avatar-sm">F</div>
              <div className="bubble">
                {mood === "encourage" ? "You're all set! 🎉 " : "Here's what I found. "}
                You save about{" "}
                <strong>₹{Math.round(result.dashboard.monthly_savings).toLocaleString("en-IN")}</strong>{" "}
                a month, and your risk profile is{" "}
                <strong>{result.riskResult.risk_category}</strong>.
              </div>
            </div>
            <div className="result-card">
              <div className="rc-label">Recommended for you</div>
              <div className="rc-value">{result.dashboard.recommended_category}</div>
              <span className="rc-tag">{result.riskResult.risk_category} risk</span>
              <button className="btn btn-block" style={{ marginTop: 12 }} onClick={onViewDashboard}>
                View full dashboard →
              </button>
            </div>
          </>
        )}
      </div>

      {/* Document extraction panel */}
      {extraction && (
        <div className="chat-input-area">
          <div className="extraction-panel">
            <div className="extraction-title">Review document evidence</div>
            <div className="extraction-file">{extraction.filename}</div>
            {Object.entries(extraction.candidates).map(([field, value]) => (
              <div className="extraction-row" key={field}>
                <span>{field.replace("_", " ")}</span>
                <strong>{value === null ? "Not found" : `₹${Number(value).toLocaleString("en-IN")}`}</strong>
                {value !== null &&
                  ["income", "expenses", "savings", "net_pay", "gross_earnings"].includes(field) && (
                    <button className="mini-btn" onClick={() => applyExtractedValue(field, value)}>
                      Confirm
                    </button>
                  )}
              </div>
            ))}
            <div className="upload-hint">
              {extraction.confidence_note} Confirmed values are applied to your profile.
            </div>
          </div>
        </div>
      )}

      {/* Onboarding input area */}
      {phase === "onboarding" && current && (
        <div className="chat-input-area">
          <div className="chat-language-selector" style={{ marginBottom: "10px", textAlign: "right" }}>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ padding: "4px 8px", borderRadius: "12px", border: "1px solid var(--line)", background: "transparent", fontSize: "11px", color: "var(--muted)" }}>
              <option value="en-IN">English</option>
              <option value="ta-IN">Tamil</option>
              <option value="ml-IN">Malayalam</option>
              <option value="kn-IN">Kannada</option>
            </select>
          </div>
          {current.type === "choice" && (
            <div className="chip-row">
              {current.options.map((o, i) => (
                <button
                  key={i}
                  className="chip"
                  onClick={() => handleAnswer(o.t, current.field, o.v !== undefined ? o.v : o.t)}
                >
                  {o.t}
                </button>
              ))}
            </div>
          )}

          {current.type === "income" && (
            <IncomeBreakdown onDone={handleIncomeDone} language={language} />
          )}

          {current.type === "expenses" && (
            <ExpenseBreakdown onDone={handleExpensesDone} language={language} />
          )}

          {current.type === "goal" && (
            <div className="chip-row chip-row-2col">
              {GOAL_OPTIONS.map((o, i) => {
                const keyMap = { "Capital preservation": "safe", "Balanced growth": "steady", "Long-term wealth": "wealth", "Income generation": "income", "House purchase": "house", "Child education": "child", "Travel / lifestyle": "travel", "Retirement": "retire" };
                const tKey = `goal_${keyMap[o.v]}`;
                return (
                  <button
                    key={i}
                    className="chip chip-goal"
                    onClick={() => handleAnswer(t(language, tKey), "goal", o.v)}
                  >
                    {t(language, tKey)}
                  </button>
                );
              })}
            </div>
          )}

          {current.type === "horizon" && (
            <HorizonPicker onDone={handleHorizonDone} language={language} />
          )}

          {current.type === "number" && (
            <div className="text-entry">
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf,image/jpeg,image/png,image/webp"
                onChange={uploadDocument}
                disabled={extracting}
                hidden
              />
              <button
                className="attach-btn"
                aria-label="Attach document"
                onClick={openUpload}
                disabled={extracting}
              >
                📎
              </button>
              <input
                type="number"
                placeholder={current.placeholder}
                value={textValue}
                onChange={(e) => setTextValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submitTextInput()}
              />
              {voiceSupported && (
                <button
                  className={`voice-btn${listening ? " listening" : ""}`}
                  onClick={toggleVoice}
                  title={listening ? "Stop" : "Speak"}
                >
                  🎙
                </button>
              )}
              <button className="send-btn" onClick={submitTextInput}>→</button>
            </div>
          )}
        </div>
      )}

      {/* Post-onboarding free chat */}
      {phase !== "onboarding" && phase !== "submitting" && (
        <div className="chat-input-area">
          <div className="chat-language-selector" style={{ marginBottom: "10px", textAlign: "right" }}>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{ padding: "4px 8px", borderRadius: "12px", border: "1px solid var(--line)", background: "transparent", fontSize: "11px", color: "var(--muted)" }}>
              <option value="en-IN">English</option>
              <option value="ta-IN">Tamil</option>
              <option value="ml-IN">Malayalam</option>
              <option value="kn-IN">Kannada</option>
            </select>
          </div>
          {phase === "done" && (
            <div className="suggested">
              <button onClick={() => askAgent(t(language, "suggest_1"))}>
                {t(language, "suggest_1")}
              </button>
              <button onClick={() => askAgent(t(language, "suggest_2"))}>
                {t(language, "suggest_2")}
              </button>
              <button onClick={() => askAgent(t(language, "suggest_3"))}>
                {t(language, "suggest_3")}
              </button>
              <button onClick={handleClearChat} style={{ color: "var(--rust)" }}>
                {t(language, "clear_chat")}
              </button>
            </div>
          )}
          {lastSources.length > 0 && (
            <div className="source-note">
              Grounded in {lastSources.length} profile / conversation source{lastSources.length > 1 ? "s" : ""}
            </div>
          )}
          <div className="text-entry">
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,image/jpeg,image/png,image/webp"
              onChange={uploadDocument}
              disabled={extracting}
              hidden
            />
            <button className="attach-btn" onClick={openUpload} disabled={extracting}>📎</button>
            <input
              type="text"
              placeholder={t(language, "free_placeholder")}
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && freeText.trim() && askAgent(freeText.trim())}
              disabled={asking}
            />
            {voiceSupported && (
              <button
                className={`voice-btn${listening ? " listening" : ""}`}
                onClick={toggleVoice}
              >
                🎙
              </button>
            )}
            <button
              className="send-btn"
              disabled={asking || !freeText.trim()}
              onClick={() => askAgent(freeText.trim())}
            >
              {asking ? "…" : "→"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
