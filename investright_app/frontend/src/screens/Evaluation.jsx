const rows = [
  { metric: "Retrieval precision@4", fin: "0.99", recent: "0.20", random: "0.19", interpretation: "Higher is better; Fin retrieves topic-relevant memories." },
  { metric: "Context attached", fin: "456 chars", recent: "11,123 chars", random: "11,123 chars", interpretation: "Lower reduces prompt size and irrelevant context." },
  { metric: "Retrieved memories", fin: "4", recent: "100", random: "100", interpretation: "Fin uses a bounded, ranked context window." },
  { metric: "Stale items surfaced", fin: "0 / 4", recent: "0 / 4", random: "Not measured", interpretation: "The seeded stale-income test did not enter Fin's top four." },
  { metric: "Context assembly latency", fin: "2.717 ms", recent: "0.0012 ms", random: "Not measured", interpretation: "Ranking adds small compute cost for better relevance." },
  { metric: "Authoritative profile facts", fin: "Included", recent: "Included", random: "Included", interpretation: "Structured facts are separated from conversational memory." },
  { metric: "Capacity guardrail", fin: "Enabled", recent: "Not available", random: "Not available", interpretation: "Fin caps recommendations when financial capacity is lower than willingness." },
  { metric: "Evidence confirmation", fin: "Required", recent: "Not available", random: "Not available", interpretation: "Document-derived values require user confirmation." },
];

export default function Evaluation() {
  return (
    <div className="evaluation-screen">
      <div className="evaluation-hero">
        <div>
          <span className="header-kicker">RESEARCH WORKSPACE</span>
          <h2>Agent performance evaluation</h2>
          <p>Offline comparison of Fin's provenance-aware retrieval against simple history baselines. These values are reproducible from the experiment artifact checked into the repository.</p>
        </div>
        <div className="evaluation-badge"><strong>0.99</strong><span>precision@4</span></div>
      </div>

      <div className="evaluation-grid">
        <div className="evaluation-stat"><span>Fin retrieval</span><strong>Lexical RAG</strong><small>Ranked, recency-weighted memory</small></div>
        <div className="evaluation-stat"><span>Evaluation set</span><strong>100 conversations</strong><small>5 topics, 20 items per topic</small></div>
        <div className="evaluation-stat"><span>Evidence policy</span><strong>Authoritative first</strong><small>Profile facts outrank conversation</small></div>
      </div>

      <div className="card evaluation-card">
        <div className="section-heading"><h3>Comparative results</h3><span className="planner-badge">Offline experiment</span></div>
        <div className="table-wrap">
          <table className="evaluation-table">
            <thead><tr><th>Metric</th><th>Fin / lexical RAG</th><th>Most recent baseline</th><th>Random baseline</th><th>Research reading</th></tr></thead>
            <tbody>{rows.map((row) => <tr key={row.metric}><th>{row.metric}</th><td className="fin-cell">{row.fin}</td><td>{row.recent}</td><td>{row.random}</td><td className="reading-cell">{row.interpretation}</td></tr>)}</tbody>
          </table>
        </div>
      </div>

      <div className="evaluation-notes">
        <div className="card"><h3>What this demonstrates</h3><p>Fin trades a small amount of ranking latency for a 24x smaller context than full history and much higher topic precision than recency or random selection. Current profile values remain explicitly authoritative.</p></div>
        <div className="card"><h3>What remains to measure</h3><p>The LLM-dependent study still needs unsupported-number rate, answer faithfulness, token cost, response latency, user comprehension, and longitudinal risk-drift evaluation with real or carefully anonymized data.</p></div>
      </div>
    </div>
  );
}