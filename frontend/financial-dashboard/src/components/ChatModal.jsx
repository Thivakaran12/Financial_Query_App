// src/components/ChatModal.jsx
import React, { useState } from 'react';

export default function ChatModal({ companySlug, onClose }) {
  const [question, setQuestion] = useState('');
  const [answer,   setAnswer]   = useState(null);
  const [error,    setError]    = useState(null);
  const [loading,  setLoading]  = useState(false);

  // pick up your API URL from CRA-environment (must start with REACT_APP_)
  const API_BASE = process.env.REACT_APP_API_URL || '';

  async function askLLM() {
    setAnswer(null);
    setError(null);
    setLoading(true);

    console.log('[ChatModal] asking LLM for:', question, 'company:', companySlug);
    try {
      const url = `${API_BASE}/api/chat`;
      console.log('[ChatModal] FETCH →', url);
      const res = await fetch(url, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ company: companySlug, question }),
      });
      console.log('[ChatModal] HTTP status:', res.status);

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const body = await res.json();
      console.log('[ChatModal] JSON response:', body);
      setAnswer(body.answer);
    } catch (e) {
      console.error('[ChatModal] error:', e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position:      'fixed',
      top:           0, left: 0, right: 0, bottom: 0,
      background:    'rgba(0,0,0,0.5)',
      display:       'flex',
      alignItems:    'center',
      justifyContent:'center',
    }}>
      <div style={{ background:'#fff', padding:20, width:400 }}>
        <button onClick={onClose} style={{ float:'right' }}>×</button>
        <h2>Ask the LLM</h2>

        <textarea
          rows={4}
          value={question}
          onChange={e => setQuestion(e.target.value)}
          style={{ width:'100%' }}
        />

        <button onClick={askLLM} disabled={loading} style={{ marginTop: 8 }}>
          {loading ? '…thinking…' : 'Send'}
        </button>

        {error && (
          <div style={{ color:'red', marginTop:10 }}>
            {error}
          </div>
        )}

        {answer && (
          <div style={{ marginTop:10, whiteSpace:'pre-wrap' }}>
            {answer}
          </div>
        )}
      </div>
    </div>
  );
}



// import React, { useState } from 'react';

// export default function ChatModal({ companySlug, onClose }) {
//   const [question, setQuestion] = useState('');
//   const [answer,   setAnswer]   = useState(null);
//   const [error,    setError]    = useState(null);
//   const [loading,  setLoading]  = useState(false);

//   async function askLLM() {
//     setError(null);
//     setAnswer(null);
//     setLoading(true);

//     try {
//       const res = await fetch('http://localhost:8000/api/chat', {
//         method:  'POST',
//         headers: {'Content-Type':'application/json'},
//         body:    JSON.stringify({ company: companySlug, question }),
//       });
//       if (!res.ok) {
//         const text = await res.text();
//         throw new Error(`HTTP ${res.status}: ${text}`);
//       }
//       const body = await res.json();
//       setAnswer(body.answer);
//     } catch (e) {
//       console.error('ChatModal error', e);
//       setError(e.message);
//     } finally {
//       setLoading(false);
//     }
//   }

//   return (
//     <div style={{
//       position:'fixed', top:0,left:0,right:0,bottom:0,
//       background:'rgba(0,0,0,0.5)', display:'flex',
//       alignItems:'center', justifyContent:'center'
//     }}>
//       <div style={{ background:'#fff', padding:20, width:400 }}>
//         <button onClick={onClose} style={{ float:'right' }}>×</button>
//         <h2>Ask the LLM</h2>
//         <textarea
//           rows={4}
//           value={question}
//           onChange={e => setQuestion(e.target.value)}
//           style={{ width:'100%' }}
//         />
//         <button onClick={askLLM} disabled={loading}>
//           {loading ? '…thinking…' : 'Send'}
//         </button>
//         {error   && <div style={{ color:'red', marginTop:10 }}>{error}</div>}
//         {answer  && <div style={{ marginTop:10, whiteSpace:'pre-wrap' }}>{answer}</div>}
//       </div>
//     </div>
//   );
// }
