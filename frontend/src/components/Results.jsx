import { useState } from "react";
import HighlightedText from "./HighlightedText.jsx";
import FindingCard from "./FindingCard.jsx";
import UrlPanel from "./UrlPanel.jsx";

const BAND_META = {
  low: { icon: "✓", title: "Fewer warning signs", sub: "Stay aware" },
  moderate: { icon: "!", title: "Pause and verify", sub: "Caution advised" },
  high: { icon: "⚠", title: "High-risk patterns", sub: "Verify before acting" },
  critical: { icon: "⛔", title: "Strong danger signals", sub: "Do not proceed yet" },
};

export default function Results({ result, analyzedText }) {
  const [showChecklist, setShowChecklist] = useState(false);
  const band = result.risk_band || result.level || "moderate";
  const meta = BAND_META[band] || BAND_META.moderate;
  const label = result.risk_label || result.level_label || meta.title;
  const classification = result.class_label;

  return <div className="results animate-in" aria-live="polite">
    <div className="results-heading"><div><span className="section-kicker">ANALYSIS COMPLETE</span><h2>Your VERITAS readout</h2></div><span className="analysis-stamp"><span className="status-dot" /> RESULT READY</span></div>
    <section className={`risk-overview risk-${band}`}>
      <div className="risk-symbol" aria-hidden="true">{meta.icon}</div>
      <div className="risk-main"><span className="risk-overline">OVERALL ASSESSMENT</span><h3>{label}</h3><p>{result.risk_summary || result.summary}</p>{classification && <span className={`classification-pill class-${result.classification}`}>{classification}</span>}</div>
      <div className="risk-side"><span className="risk-side-label">RISK POSTURE</span><div className="risk-level-text">{band === "low" ? "GUARDED" : band === "moderate" ? "CAUTIOUS" : band === "high" ? "ELEVATED" : "SEVERE"}</div><div className="risk-segments" aria-label={`Risk category: ${band}`}>{["low", "moderate", "high", "critical"].map((v) => <span key={v} className={(["low", "moderate", "high", "critical"].indexOf(band) >= ["low", "moderate", "high", "critical"].indexOf(v)) ? `segment segment-${v} filled` : "segment"} />)}</div><span className="risk-side-foot">{meta.sub}</span></div>
    </section>
    {result.model_note && <p className="model-note"><span>ⓘ</span>{result.model_note}</p>}
    {result.notes?.map((n, i) => <p key={i} className="notice">{n}</p>)}

    {result.model_cues?.length > 0 && <section className="result-panel"><div className="panel-heading"><div><span className="section-kicker">MODEL EXPLANATION</span><h3>Patterns that influenced the readout</h3></div><span className="panel-index">01</span></div><p className="muted">These words or phrases were influential for the message classifier. They are clues, not proof of intent.</p><div className="cue-list">{result.model_cues.map((cue, i) => <span className="cue-chip" key={`${cue}-${i}`}>{cue}</span>)}</div></section>}

    {analyzedText.trim() && result.highlights?.length > 0 && <section className="result-panel"><div className="panel-heading"><div><span className="section-kicker">VISIBLE EVIDENCE</span><h3>Where the warning signs appear</h3></div><span className="panel-index">02</span></div><p className="muted">Highlighted phrases match signals explained below. Focus or hover a highlight for its label.</p><HighlightedText text={analyzedText} highlights={result.highlights} /></section>}

    <section className="result-panel"><div className="panel-heading"><div><span className="section-kicker">WHY IT WAS FLAGGED</span><h3>Evidence, not just a verdict</h3></div><span className="panel-index">{analyzedText.trim() && result.highlights?.length ? "03" : "02"}</span></div>
      {result.findings?.length ? <div className="findings">{result.findings.map((f) => <FindingCard key={f.id} finding={f} />)}</div> : <div className="empty-evidence"><span>✓</span><div><strong>No known rule-based warning signs matched.</strong><p>This does not establish that the sender or offer is legitimate. New or unusual scam patterns may not be recognised.</p></div></div>}
      <p className="evidence-legend"><span className="badge badge-evidence">Observed evidence</span> appears in the submitted text or link. <span className="badge badge-assumption">Needs verification</span> cannot be confirmed from the text alone.</p>
    </section>

    <UrlPanel urls={result.urls || []} />
    <section className="result-panel next-steps-panel"><div className="panel-heading"><div><span className="section-kicker">YOUR NEXT MOVE</span><h3>What to do now</h3></div><span className="panel-index">→</span></div><ul className="steps">{(result.next_steps || []).map((s, i) => <li key={i}><span className="step-number">{String(i + 1).padStart(2, "0")}</span><span>{s}</span></li>)}</ul>
      <button className="checklist-toggle" onClick={() => setShowChecklist((v) => !v)} aria-expanded={showChecklist}>{showChecklist ? "Hide verification checklist" : "Open verification checklist"}<span>{showChecklist ? "−" : "+"}</span></button>
      {showChecklist && <ul className="checklist">{(result.verification_checklist || []).map((s, i) => <li key={i}><label><input type="checkbox" /> <span>{s}</span></label></li>)}</ul>}
    </section>
    {result.report_guidance && <section className="result-panel report-panel"><div className="panel-heading"><div><span className="section-kicker">IF YOU'VE ALREADY ACTED</span><h3>{result.report_guidance.title}</h3></div><span className="panel-index">!</span></div><ul className="steps">{result.report_guidance.items.map((s, i) => <li key={i}><span className="step-number">{String(i + 1).padStart(2, "0")}</span><span>{s}</span></li>)}</ul><p className="muted">{result.report_guidance.note}</p></section>}
    <p className="disclaimer">{result.disclaimer} Always verify independently before sharing money, credentials or identity documents.</p>
  </div>;
}
