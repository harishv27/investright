import { useState } from "react";

const SLIDES = [
  {
    icon: "💬",
    title: "Chat, don't fill forms",
    text: "Tell Fin about your income, goals, and comfort with risk — just like texting a friend.",
  },
  {
    icon: "📊",
    title: "Real numbers, not guesses",
    text: "Every calculation — savings rate, risk score, recommendation — comes from real financial logic, never invented.",
  },
  {
    icon: "🧭",
    title: "Decision support, not advice",
    text: "Fin helps you understand your options. You always make the final call.",
  },
];

export default function Onboarding({ onDone }) {
  const [index, setIndex] = useState(0);
  const slide = SLIDES[index];

  const next = () => {
    if (index === SLIDES.length - 1) {
      onDone();
    } else {
      setIndex(index + 1);
    }
  };

  return (
    <div className="onboarding">
      <button className="ob-skip" onClick={onDone}>Skip</button>
      <div className="ob-slide">
        <div className="ob-icon">{slide.icon}</div>
        <h2>{slide.title}</h2>
        <p>{slide.text}</p>
      </div>
      <div className="ob-dots">
        {SLIDES.map((_, i) => (
          <div key={i} className={`ob-dot ${i === index ? "active" : ""}`} />
        ))}
      </div>
      <div className="ob-actions">
        <button className="btn btn-block" onClick={next}>
          {index === SLIDES.length - 1 ? "Get started" : "Next"}
        </button>
      </div>
    </div>
  );
}
