// src/components/ChatPage.jsx
import React, { useState } from 'react';
import PropTypes            from 'prop-types';
import './ChatPage.css';

export default function ChatPage({ companySlug, onClose }) {
  /* ───── Helpers ────────────────────────────── */
  const niceName = companySlug.replace(/-/g, ' ');

  const buildSuggestions = () => [
    `Show the highest revenue quarter for ${niceName}`,
    `Display ${niceName}'s net‐margin trend`,
    'Compare QoQ gross‐profit growth between dipped products and richard pieris',
    'What is the latest TTM net income for each company?'
  ];

  /* ───── State ──────────────────────────────── */
  const [history, setHistory] = useState([
    { role: 'assistant', content: 'Hello! How can I assist you today?' }
  ]);
  const [input,    setInput]     = useState('');
  const [loading,  setLoading]   = useState(false);
  const [error,    setError]     = useState(null);

  /* ───── Send handler ───────────────────────── */
  const sendMessage = async (overrideText) => {
    const question = (overrideText ?? input).trim();
    if (!question) return;

    const newHistory = [...history, { role: 'user', content: question }];
    setHistory(newHistory);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const resp = await fetch('/api/chat', {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({
          question,
          company_slug: companySlug,
          history: newHistory
        })
      });
      if (!resp.ok) throw new Error(await resp.text());
      const { answer } = await resp.json();
      setHistory(h => [...h, { role: 'assistant', content: answer }]);
    } catch (e) {
      console.error(e);
      setError(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ───── UI ─────────────────────────────────── */
  return (
    <div className="chat-page">
      <header className="chat-header">
        {/* only “Live Agent” now */}
        <h2>Live Agent</h2>
        <button className="close-btn" onClick={onClose}>×</button>
      </header>

      {/* suggestion pills */}
      <div className="suggestions">
        {buildSuggestions().map((txt, i) => (
          <button
            key={i}
            className="suggestion-pill"
            onClick={() => sendMessage(txt)}
            disabled={loading}
          >
            {txt}
          </button>
        ))}
      </div>

      {/* conversation history */}
      <div className="chat-body">
        {history.map((m,i) => (
          <div
            key={i}
            className={`chat-message ${m.role === 'user' ? 'from-user' : 'from-bot'}`}
          >
            {m.content}
          </div>
        ))}
        {error && <div className="chat-error">{error}</div>}
      </div>

      {/* input footer */}
      <footer className="chat-footer">
        <textarea
          className="chat-input"
          placeholder="Type your question…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          {loading ? '…' : 'Send'}
        </button>
      </footer>
    </div>
  );
}

ChatPage.propTypes = {
  companySlug: PropTypes.string.isRequired,
  onClose    : PropTypes.func.isRequired,
};
