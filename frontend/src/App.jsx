import { useEffect, useRef, useState } from "react";
import { analyze, getSamples } from "./api.js";
import Results from "./components/Results.jsx";

const MAX_TEXT = 5000;

export default function App() {
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [samples, setSamples] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [analyzedText, setAnalyzedText] = useState("");
  const [activeInput, setActiveInput] = useState("message");
  const [scrollProgress, setScrollProgress] = useState(0);
  const resultsRef = useRef(null);

  useEffect(() => { getSamples().then(setSamples).catch(() => setSamples([])); }, []);

  useEffect(() => {
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        setScrollProgress(max > 0 ? window.scrollY / max : 0);
        document.documentElement.style.setProperty("--scroll-y", `${window.scrollY}px`);
      });
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => { cancelAnimationFrame(frame); window.removeEventListener("scroll", update); window.removeEventListener("resize", update); };
  }, []);

  useEffect(() => {
    const nodes = document.querySelectorAll(".reveal-on-scroll");
    if (!("IntersectionObserver" in window)) { nodes.forEach((node) => node.classList.add("is-visible")); return; }
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add("is-visible"); observer.unobserve(entry.target); }
    }), { threshold: 0.12, rootMargin: "0px 0px -35px 0px" });
    nodes.forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, [result]);

  async function run(nextText = text, nextUrl = url) {
    setError("");
    if (!nextText.trim() && !nextUrl.trim()) {
      setError("Add a message or a link first, and VERITAS will inspect it.");
      return;
    }
    setLoading(true);
    try {
      const data = await analyze({ text: nextText, url: nextUrl });
      setResult(data);
      setAnalyzedText(nextText);
      window.setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  function loadSample(sample) {
    setText(sample.text || ""); setUrl(sample.url || "");
    setActiveInput(sample.url && !sample.text ? "link" : "message");
    run(sample.text || "", sample.url || "");
  }

  function clearAll() {
    setText(""); setUrl(""); setResult(null); setError(""); setAnalyzedText("");
  }

  return (
    <div className="app-shell">
      <div className="scroll-progress" aria-hidden="true"><span style={{ transform: `scaleX(${scrollProgress})` }} /></div>
      <div className="scene-grid" aria-hidden="true" />
      <div className="orb orb-one" aria-hidden="true" /><div className="orb orb-two" aria-hidden="true" /><div className="orb orb-three" aria-hidden="true" />
      <div className="ambient ambient-one" /><div className="ambient ambient-two" />
      <div className="signal-rings" aria-hidden="true"><span /><span /><span /></div>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="VERITAS home"><span className="brand-mark" aria-hidden="true"><svg viewBox="0 0 40 40" role="presentation"><path d="M20 3.5 34.3 11.8V28.2L20 36.5 5.7 28.2V11.8Z"/><path d="M12 13.5 20 27.5 28 13.5M14.5 9.5h11"/><circle cx="20" cy="20" r="2.2"/></svg></span><span>VERITAS<small>TRUST, VERIFIED.</small></span></a>
        <div className="topbar-status"><span className="status-dot" /> PRIVATE BY DESIGN <span className="topbar-divider">/</span> LINK-SAFE ANALYSIS</div>
      </header>

      <main id="top" className="main-content">
        <section className="hero reveal-on-scroll">
          <div className="eyebrow"><span className="eyebrow-line" /> DIGITAL TRUST INTELLIGENCE</div>
          <h1>Look closer.<br /><span>Stay one step ahead.</span></h1>
          <p className="hero-copy">Suspicious internship offer? Unexpected bank alert? Strange link? VERITAS looks for scam and spam patterns, then shows you the evidence behind the warning.</p>
          <div className="hero-proof"><span><b>01</b> Learn from patterns</span><i /> <span><b>02</b> See the evidence</span><i /> <span><b>03</b> Choose with clarity</span></div>
        </section>

        <section className="workspace-card reveal-on-scroll" aria-label="Analyze a message or link">
          <div className="workspace-heading"><div><span className="section-kicker">START AN ANALYSIS</span><h2>What would you like to verify?</h2></div><span className="secure-tag"><span className="mini-lock">⌑</span> No link is opened</span></div>
          <div className="input-tabs" role="tablist" aria-label="Input type">
            <button role="tab" aria-selected={activeInput === "message"} className={activeInput === "message" ? "input-tab active" : "input-tab"} onClick={() => setActiveInput("message")}><span>✳</span> Message or offer</button>
            <button role="tab" aria-selected={activeInput === "link"} className={activeInput === "link" ? "input-tab active" : "input-tab"} onClick={() => setActiveInput("link")}><span>↗</span> Website link</button>
          </div>
          {activeInput === "message" ? <div className="input-panel" key="message">
            <label htmlFor="msg">Paste the message, internship offer, SMS or email text</label>
            <textarea id="msg" rows={7} maxLength={MAX_TEXT} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste the message here… Include the sender's wording so VERITAS can look for context." />
            <div className="field-meta"><span>Tip: include the full wording, but remove passwords or private account details.</span><span className={text.length > MAX_TEXT * .9 ? "counter near-limit" : "counter"}>{text.length.toLocaleString()} / {MAX_TEXT.toLocaleString()}</span></div>
            <label htmlFor="url" className="optional-label">Link included in the message <span>OPTIONAL</span></label>
            <div className="url-input-wrap"><span>↗</span><input id="url" type="text" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/offer" maxLength={2048} /></div>
          </div> : <div className="input-panel link-mode" key="link">
            <label htmlFor="url-only">Paste the suspicious link</label>
            <div className="url-input-wrap prominent"><span>↗</span><input id="url-only" type="text" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://suspicious-website.example" maxLength={2048} /></div>
            <div className="link-safety-note"><span className="shield-icon">◇</span><div><strong>Safe to inspect here</strong><p>VERITAS examines the URL's text and structure only. It will not visit the site, follow redirects or download anything.</p></div></div>
          </div>}
          <div className="action-row"><button className="analyze-button" onClick={() => activeInput === "link" ? run("", url) : run()} disabled={loading}><span>{loading ? "◌" : "✧"}</span>{loading ? "Analyzing patterns…" : "Analyze with VERITAS"}<span className="button-arrow">→</span></button><button className="clear-button" onClick={clearAll} disabled={loading}>Clear</button></div>
          {loading && <div className="loading-track"><span /></div>}
          {error && <p className="error-message" role="alert">⚠ {error}</p>}
          {samples.length > 0 && <div className="examples"><div className="examples-heading"><span>NEED A TEST CASE?</span><span>TRY A SAMPLE</span></div><div className="sample-chips">{samples.map((s) => <button key={s.id} className={`sample-chip ${s.kind}`} onClick={() => loadSample(s)}><span className="sample-dot" />{s.label}<span className="chip-arrow">↗</span></button>)}</div></div>}
          <div className="privacy-line"><span className="privacy-icon">◈</span><span>Your submission is analyzed in memory and is not stored by the analysis endpoint.</span><span className="privacy-right">BUILT FOR CAUTION, NOT CERTAINTY</span></div>
        </section>

        <div ref={resultsRef} className="results-anchor reveal-on-scroll">{result && <Results result={result} analyzedText={analyzedText} />}</div>
        <section className="principles reveal-on-scroll"><div className="principle-icon">◉</div><div><span className="section-kicker">A NOTE ON TRUST</span><h3>No detector can promise perfect safety.</h3><p>VERITAS highlights patterns and evidence to help you make a more informed decision. Verify senders independently before paying, sharing identity documents or entering login details.</p></div></section>
      </main>
      <footer className="site-footer"><span>VERITAS <b>©</b> 2026</span><span>CLARITY OVER CERTAINTY.</span><span>MADE TO HELP YOU PAUSE BEFORE YOU CLICK.</span></footer>
    </div>
  );
}
