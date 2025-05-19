// src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';

import Dashboard from './components/Dashboard';  // ← new polished dashboard
import ChatPage  from './components/ChatPage';   // ← existing full-screen chat

/* global styles & palette -------------------------------------------------- */
import './theme.css';
import './App.css';

/* ------------------------------------------------------------------------- */
/* A thin wrapper that pulls ?company=… from the URL and passes it down.     */
/* ------------------------------------------------------------------------- */
function ChatWrapper() {
  const query        = new URLSearchParams(window.location.search);
  const companySlug  = query.get('company') || 'dipped-products';
  const navigateBack = useNavigate();          // used for the close button

  return (
    <ChatPage
      companySlug={companySlug}
      onClose={() => navigateBack(-1)}          // go back to previous page
    />
  );
}

/* ------------------------------------------------------------------------- */
/* App – top-level router                                                    */
/* ------------------------------------------------------------------------- */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/chat" element={<ChatWrapper />} />
        <Route path="/*"    element={<Dashboard   />} />
      </Routes>
    </BrowserRouter>
  );
}
