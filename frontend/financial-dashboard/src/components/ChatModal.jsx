import React, { useState } from 'react';
import PropTypes            from 'prop-types';
import './ChatPage.css';

/* hard-coded list so we can craft “both-companies” suggestions */
const ALL_COMPANIES = ['dipped-products', 'richard-pieris'];

export default function ChatPage({ companySlug, onClose }) {
  const niceName  = companySlug.replace(/-/g, ' ');
  const otherName = ALL_COMPANIES.find(s => s !== companySlug)
                      ?.replace(/-/g, ' ') || 'richard pieris';

  /* ---------------- initial messages ---------------- */
  const [history, setHistory] = useState([
    { role: 'assistant', content: 'Hello! How can I assist you today?' }
  ]);
  const [input, setInput]     = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  /* ---------------- suggestions (exactly 4) ---------- */
  const suggestions = [
    `Show the highest revenue quarter for ${niceName}`,
    `Display ${niceName}'s net-margin trend`,
    `Compare QoQ revenue growth between dipped products and richard pieris`,
    'What is the latest TTM net income for each company?'
  ];

  /* ---------------- send handler --------------------- */
  const sendMessage = async (overrideText) => {
    const question = (overrideText ?? input).trim();
    if (!question) return;

    const newHistory = [...history, { role: 'user', content: question }];
    setHistory(newHistory);
    setInput('');
    setLoading(true); setError(null);

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

  /* ---------------- UI -------------------------------- */
  return (
    <div className="chat-page">
      <header className="chat-header">
        <h2>Live Agent</h2>
        <button className="close-btn" onClick={onClose}>×</button>
      </header>

      {/* quick-suggest buttons */}
      <div className="suggestions">
        {suggestions.map((txt,i)=>(
          <button
            key={i}
            className="suggestion-pill"
            onClick={()=>sendMessage(txt)}
            disabled={loading}
          >
            {txt}
          </button>
        ))}
      </div>

      {/* message history */}
      <div className="chat-body">
        {history.map((msg,i)=>(
          <div
            key={i}
            className={`chat-message ${
              msg.role==='user' ? 'from-user' : 'from-bot'
            }`}
          >
            {msg.content}
          </div>
        ))}
        {error && <div className="chat-error">{error}</div>}
      </div>

      {/* composer */}
      <footer className="chat-footer">
        <textarea
          className="chat-input"
          placeholder="Type your question…"
          value={input}
          onChange={e=>setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={()=>sendMessage()}
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
  onClose   : PropTypes.func.isRequired,
};
