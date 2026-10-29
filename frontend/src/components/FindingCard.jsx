const BADGES = {
  found_in_text: { text: "Observed in message", cls: "badge-evidence" },
  found_in_link: { text: "Observed in link", cls: "badge-evidence" },
  needs_verification: { text: "Needs verification", cls: "badge-assumption" },
};

export default function FindingCard({ finding }) {
  const badge = BADGES[finding.evidence_type] ?? BADGES.found_in_text;
  return <article className="finding-card"><div className="finding-topline"><span className="finding-marker">◇</span><h4>{finding.title}</h4><span className={`badge ${badge.cls}`}>{badge.text}</span></div><p className="why">{finding.why}</p>{finding.evidence?.length > 0 && <ul className="evidence">{finding.evidence.map((e, i) => <li key={i}>{e}</li>)}</ul>}</article>;
}
