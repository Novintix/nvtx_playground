
import React, { useState } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import DashboardView from './views/DashboardView';
import LeadsListView from './views/LeadsListView';
import LeadDetailView from './views/LeadDetailView';
import CreateLeadView from './views/CreateLeadView';
import { MOCK_LEADS } from './constants';
import { Lead } from './types';

const App: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>(MOCK_LEADS);

  const addLead = (newLead: Lead) => {
    setLeads(prev => [...prev, newLead]);
  };

  const updateLead = (updatedLead: Lead) => {
    setLeads(prev => prev.map(l => l.id === updatedLead.id ? updatedLead : l));
  };

  return (
    <Router>
      <div className="flex min-h-screen bg-background-light dark:bg-background-dark transition-colors duration-200">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
          <Routes>
            <Route path="/" element={<DashboardView leads={leads} />} />
            <Route path="/leads" element={<LeadsListView leads={leads} />} />
            <Route path="/leads/:id" element={<LeadDetailView leads={leads} onUpdate={updateLead} />} />
            <Route path="/create-lead" element={<CreateLeadView onAdd={addLead} />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;
