
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lead, LeadPriority, LeadStage } from '../types';

interface CreateLeadViewProps {
  onAdd: (lead: Lead) => void;
}

const CreateLeadView: React.FC<CreateLeadViewProps> = ({ onAdd }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    company: '',
    title: '',
    industry: 'Cloud Infrastructure',
    estimatedValue: '5000',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newLead: Lead = {
      id: Date.now().toString(),
      name: `${formData.firstName} ${formData.lastName}`,
      title: formData.title,
      company: formData.company,
      email: formData.email,
      phone: formData.phone,
      linkedin: `linkedin.com/in/${formData.firstName.toLowerCase()}${formData.lastName.toLowerCase()}`,
      industry: formData.industry,
      employees: '1-10',
      revenue: '$0 - $1M',
      owner: 'Alex Thompson',
      ownerAvatar: '',
      source: 'Direct Entry',
      created: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      priority: LeadPriority.MEDIUM,
      stage: LeadStage.DISCOVERY,
      estimatedValue: `$${Number(formData.estimatedValue).toLocaleString()}`,
      projectType: 'IT Consulting',
      activities: []
    };
    onAdd(newLead);
    navigate('/leads');
  };

  return (
    <div className="p-8 max-w-4xl mx-auto w-full">
      <div className="mb-8">
        <Link to="/" className="text-primary text-sm font-bold flex items-center gap-1 mb-4">
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Back to Dashboard
        </Link>
        <h1 className="text-3xl font-black text-[#0d111c] dark:text-white">Create New Lead</h1>
        <p className="text-slate-500 mt-2">Enter the details of the new prospective client for IT services.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-sm">
        <div className="space-y-8">
          <div>
            <h3 className="text-lg font-bold mb-6 text-[#0d111c] dark:text-white pb-2 border-b border-slate-100 dark:border-slate-800">Personal & Contact</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">First Name *</label>
                <input required className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary" 
                  value={formData.firstName} onChange={e => setFormData({...formData, firstName: e.target.value})} placeholder="e.g. John" />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Last Name *</label>
                <input required className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary" 
                  value={formData.lastName} onChange={e => setFormData({...formData, lastName: e.target.value})} placeholder="e.g. Doe" />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Email Address *</label>
                <input required type="email" className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary" 
                  value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} placeholder="john@example.com" />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Phone Number</label>
                <input className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary" 
                  value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} placeholder="+1 (555) 000-0000" />
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-6 text-[#0d111c] dark:text-white pb-2 border-b border-slate-100 dark:border-slate-800">Project Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Company Name *</label>
                <input required className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary" 
                  value={formData.company} onChange={e => setFormData({...formData, company: e.target.value})} placeholder="Acme Corp" />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Job Title</label>
                <input className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary" 
                  value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} placeholder="e.g. CTO" />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Estimated Budget (USD)</label>
                <input type="number" className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary" 
                  value={formData.estimatedValue} onChange={e => setFormData({...formData, estimatedValue: e.target.value})} />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Industry</label>
                <select className="w-full rounded-xl border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-white p-3 focus:ring-primary focus:border-primary"
                  value={formData.industry} onChange={e => setFormData({...formData, industry: e.target.value})}>
                  <option>Cloud Infrastructure</option>
                  <option>Software Development</option>
                  <option>Cybersecurity</option>
                  <option>Fintech</option>
                  <option>Retail</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-12 flex justify-end gap-4 pt-8 border-t border-slate-100 dark:border-slate-800">
          <button type="button" onClick={() => navigate('/')} className="px-6 py-2.5 rounded-xl font-bold text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">Discard Changes</button>
          <button type="submit" className="px-10 py-2.5 rounded-xl font-bold bg-primary text-white shadow-lg shadow-primary/20 hover:bg-blue-700 transition-all">Create Lead</button>
        </div>
      </form>
      
      <div className="mt-8 flex justify-center gap-8 text-[11px] font-bold text-slate-400 uppercase tracking-widest">
        <div className="flex items-center gap-1.5"><span className="material-symbols-outlined text-[16px]">lock</span> Encrypted Data Entry</div>
        <div className="flex items-center gap-1.5"><span className="material-symbols-outlined text-[16px]">cloud_sync</span> Auto-sync enabled</div>
      </div>
    </div>
  );
};

export default CreateLeadView;
