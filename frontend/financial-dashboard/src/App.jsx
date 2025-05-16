import React, { useEffect, useState } from 'react';
import { fetchCompanyData } from './services/financialApi';
import CompanySelector     from './components/CompanySelector';
import PnLChart            from './components/PnLChart';
import ChatModal           from './components/ChatModal';
import './App.css';

const SLUGS = {
  'Dipped Products': 'dipped-products',
  'Richard Pieris':  'richard-pieris',
};

export default function App() {
  const [companyName, setCompanyName] = useState(Object.keys(SLUGS)[0]);
  const [data, setData]               = useState([]);
  const [showChat, setShowChat]       = useState(false);

  useEffect(() => {
    const slug = SLUGS[companyName];
    fetchCompanyData(slug)
      .then(setData)
      .catch(err=>{
        console.error('load data failed for',slug,err);
        setData([]);
      });
  }, [companyName]);

  return (
    <div style={{padding:20, position:'relative'}}>
      <h1>Financial Dashboard</h1>

      <button
        style={{position:'absolute', top:20, right:20}}
        onClick={()=>setShowChat(true)}
      >Chat with LLM</button>

      <CompanySelector
        options={Object.keys(SLUGS)}
        value={companyName}
        onChange={setCompanyName}
      />
      <PnLChart data={data} />

      {showChat && (
        <ChatModal
          companySlug={SLUGS[companyName]}
          onClose={()=>setShowChat(false)}
        />
      )}
    </div>
  );
}
