import React from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';

import Layout     from './components/Layout';
import Dashboard  from './components/Dashboard';
import ChatPage   from './components/ChatPage';

/* global styles & palette */
import './theme.css';
import './App.css';

/* ------------------------------------------------------------------------- */
/* ChatWrapper pulls ?company=… from URL and passes it to ChatPage           */
/* ------------------------------------------------------------------------- */
function ChatWrapper() {
  const query       = new URLSearchParams(window.location.search);
  const companySlug = query.get('company') || 'dipped-products';
  const navigate    = useNavigate();

  return (
    <ChatPage
      companySlug={companySlug}
      onClose={() => navigate(-1)}  // go back
    />
  );
}

/* ------------------------------------------------------------------------- */
/* App – top‐level router wrapped in our new Layout                           */
/* ------------------------------------------------------------------------- */
export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"    element={<Dashboard />} />
          <Route path="/chat" element={<ChatWrapper />} />
          {/* add more routes here if needed */}
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
