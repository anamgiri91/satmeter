import { useState } from 'react';
import Gauge from './Gauge';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const EXAMPLES = [
  {
    label: 'Cites a number',
    text: "According to our school's own Common Data Set, we admit about 8% of applicants with sub-1400 SATs. It's not zero, but it's rare.",
  },
  {
    label: 'Tells a story',
    text: 'I got waitlisted in March and didn\'t hear back until the last week of June. Checked the portal every single day.',
  },
  {
    label: 'States an opinion',
    text: 'Legacy applicants basically get a free pass at every top school, everyone in admissions knows it.',
  },
  {
    label: 'Expresses a feeling',
    text: "I've read this decision letter about thirty times now and I still don't know how to feel about it.",
  },
];

const LABEL_META = {
  evidence_based_advice: {
    name: 'Evidence-based advice',
    color: 'var(--evidence)',
  },
  anecdotal_experience: {
    name: 'Anecdotal experience',
    color: 'var(--anecdote)',
  },
  unsupported_take: {
    name: 'Unsupported take',
    color: 'var(--unsupported)',
  },
  emotional_reaction: {
    name: 'Emotional reaction',
    color: 'var(--emotional)',
  },
};

export default function App() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: trimmed }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? "Couldn't reach the API. If this is the first request in a while, the free-tier server may still be waking up — try again in a few seconds."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  const scoresByLabel = result
    ? Object.fromEntries(result.scores.map((s) => [s.label, s.probability]))
    : {};

  return (
    <div className="page">
      <header className="header">
        <span className="eyebrow">TAKEMETER</span>
        <h1>What kind of claim is this?</h1>
        <p className="subhead">
          Paste a comment from an admissions forum. A fine-tuned DistilBERT model reads it for its{' '}
          <em>epistemic type</em> — not whether the advice is good, but what kind of claim it's making.
        </p>
      </header>

      <main className="layout">
        <section className="card input-card">
          <form onSubmit={handleSubmit}>
            <label htmlFor="comment" className="field-label">
              Comment
            </label>
            <textarea
              id="comment"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. “Top schools reject most 1600s, so don't get your hopes up.”"
              rows={7}
              maxLength={3000}
            />
            <div className="input-footer">
              <div className="examples">
                {EXAMPLES.map((ex) => (
                  <button
                    type="button"
                    key={ex.label}
                    className="chip"
                    onClick={() => setText(ex.text)}
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
              <button type="submit" className="submit-btn" disabled={loading || !text.trim()}>
                {loading ? 'Reading…' : 'Classify'}
              </button>
            </div>
          </form>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="card result-card">
          <Gauge scoresByLabel={scoresByLabel} predictedLabel={result?.predicted_label} />

          {!result && !loading && (
            <p className="placeholder">The meter will point at the predicted category once you classify a comment.</p>
          )}

          {result && (
            <>
              <div className="predicted-readout" style={{ color: LABEL_META[result.predicted_label].color }}>
                {LABEL_META[result.predicted_label].name}
              </div>
              <ul className="score-list">
                {result.scores.map((s) => (
                  <li key={s.label} className={s.label === result.predicted_label ? 'active' : ''}>
                    <div className="score-row">
                      <span className="score-name">{LABEL_META[s.label].name}</span>
                      <span className="score-pct">{(s.probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${s.probability * 100}%`,
                          background: LABEL_META[s.label].color,
                        }}
                      />
                    </div>
                    <p className="score-desc">{s.description}</p>
                  </li>
                ))}
              </ul>
              <p className="meta">inference: {result.inference_ms}ms</p>
            </>
          )}
        </section>
      </main>

      <footer className="footer">
        <p>
          DistilBERT fine-tuned on 242 hand-labeled r/ApplyingToCollege comments — 0.839 macro-F1,
          matching a 70B-parameter zero-shot baseline.{' '}
          <a href="https://github.com/anamgiri91" target="_blank" rel="noreferrer">
            View source →
          </a>
        </p>
      </footer>
    </div>
  );
}
