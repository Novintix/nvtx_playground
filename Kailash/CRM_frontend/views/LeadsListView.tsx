
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Lead, LeadPriority } from '../types';

interface LeadsListViewProps {
  leads: Lead[];
}

const LeadsListView: React.FC<LeadsListViewProps> = ({ leads }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredLeads = leads.filter(l => 
    l.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    l.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col flex-1 h-screen min-w-0">
      <header className="bg-white dark:bg-slate-900 border-b border-[#cfd5e8] dark:border-slate-800 px-8 py-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0">
        <div>
          <h2 className="text-[#0d111c] dark:text-white text-3xl font-black tracking-tight">Leads</h2>
          <p className="text-[#4b5f9b] dark:text-slate-400 text-sm">Manage your sales pipeline and delivery prospects.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center justify-center gap-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 px-4 h-10 rounded-lg text-sm font-bold border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
            <span className="material-symbols-outlined text-[20px]">file_download</span>
            Import
          </button>
          <Link to="/create-lead" className="flex items-center justify-center gap-2 bg-primary text-white px-5 h-10 rounded-lg text-sm font-bold shadow-sm shadow-primary/20 hover:bg-blue-700 transition-colors">
            <span className="material-symbols-outlined text-[20px]">add</span>
            Create Lead
          </Link>
        </div>
      </header>

      <div className="px-8 py-6 flex flex-col gap-4 overflow-hidden">
        <div className="flex flex-col lg:flex-row gap-4 items-center shrink-0">
          <div className="w-full lg:max-w-md relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
              <span className="material-symbols-outlined">search</span>
            </span>
            <input
              className="block w-full bg-white dark:bg-slate-900 border border-[#cfd5e8] dark:border-slate-800 rounded-lg py-2.5 pl-10 pr-3 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary dark:text-white transition-all"
              placeholder="Search leads by name, company, or owner..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-3 w-full lg:w-auto">
            <button className="flex h-10 items-center justify-center gap-2 rounded-lg bg-white dark:bg-slate-900 border border-[#cfd5e8] dark:border-slate-800 px-4 text-sm font-medium text-[#0d111c] dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              <span className="material-symbols-outlined text-[20px]">filter_alt</span>
              Filter
              <span className="ml-1 flex items-center justify-center bg-primary/10 text-primary text-[10px] font-bold h-4 w-4 rounded-full">4</span>
            </button>
            <button className="flex h-10 items-center justify-center gap-2 rounded-lg bg-white dark:bg-slate-900 border border-[#cfd5e8] dark:border-slate-800 px-4 text-sm font-medium text-[#0d111c] dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              <span className="material-symbols-outlined text-[20px]">sort</span>
              Sort
            </button>
            <button className="text-slate-400 text-xs font-bold px-3 hover:text-primary transition-colors">RESET</button>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-[#cfd5e8] dark:border-slate-800 rounded-xl overflow-hidden shadow-sm flex flex-col min-h-0">
          <div className="overflow-x-auto flex-1 no-scrollbar">
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-[#cfd5e8] dark:border-slate-800 sticky top-0 z-10">
                  <th className="px-6 py-4 w-12 text-center">
                    <input className="rounded border-[#cfd5e8] dark:border-slate-700 text-primary focus:ring-primary h-4 w-4 bg-white dark:bg-slate-900" type="checkbox"/>
                  </th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Lead Name</th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Company</th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Source</th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Project Type</th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Stage</th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Priority</th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Owner</th>
                  <th className="px-4 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredLeads.map(lead => (
                  <tr key={lead.id} className="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                    <td className="px-6 py-4 text-center">
                      <input className="rounded border-[#cfd5e8] dark:border-slate-700 text-primary focus:ring-primary h-4 w-4 bg-white dark:bg-slate-900" type="checkbox"/>
                    </td>
                    <td className="px-4 py-4">
                      <Link to={`/leads/${lead.id}`} className="text-sm font-semibold text-primary hover:underline cursor-pointer">{lead.name}</Link>
                    </td>
                    <td className="px-4 py-4 text-sm text-[#4b5f9b] dark:text-slate-300">{lead.company}</td>
                    <td className="px-4 py-4 text-sm">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200">{lead.source}</span>
                    </td>
                    <td className="px-4 py-4 text-sm text-[#4b5f9b] dark:text-slate-300">{lead.projectType}</td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold ${
                        lead.stage === 'New' ? 'bg-blue-100 text-blue-700' : 'bg-emerald-100 text-emerald-700'
                      } dark:bg-slate-800/40 dark:text-slate-200`}>{lead.stage}</span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <span className={`h-2 w-2 rounded-full ${lead.priority === LeadPriority.HIGH ? 'bg-red-500' : lead.priority === LeadPriority.MEDIUM ? 'bg-amber-500' : 'bg-slate-300'}`}></span>
                        <span className="text-sm">{lead.priority}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <div className="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-xs" title={lead.owner}>
                          {lead.owner.split(' ').map(n => n[0]).join('')}
                        </div>
                        <span className="text-xs text-slate-500 dark:text-slate-400 lg:hidden xl:inline">{lead.owner}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-500 dark:text-slate-400">{lead.created}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between border-t border-[#cfd5e8] dark:border-slate-800 shrink-0">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Showing {filteredLeads.length} of {leads.length} leads</span>
            <div className="flex gap-1">
              <button className="flex items-center justify-center size-8 rounded border border-[#cfd5e8] dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-400 hover:text-primary transition-colors">
                <span className="material-symbols-outlined text-[20px]">chevron_left</span>
              </button>
              <button className="flex items-center justify-center size-8 rounded border border-primary bg-primary text-white font-bold text-xs">1</button>
              <button className="flex items-center justify-center size-8 rounded border border-[#cfd5e8] dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 font-medium text-xs hover:border-primary transition-colors">2</button>
              <button className="flex items-center justify-center size-8 rounded border border-[#cfd5e8] dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-400 hover:text-primary transition-colors">
                <span className="material-symbols-outlined text-[20px]">chevron_right</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-slate-900 text-white px-6 py-3 rounded-xl shadow-2xl flex items-center gap-6 z-50">
        <span className="text-sm font-semibold border-r border-slate-700 pr-6">3 Leads Selected</span>
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 hover:text-primary transition-colors text-xs font-bold">
            <span className="material-symbols-outlined text-[18px]">assignment_ind</span>
            ASSIGN
          </button>
          <button className="flex items-center gap-2 hover:text-primary transition-colors text-xs font-bold">
            <span className="material-symbols-outlined text-[18px]">update</span>
            STAGE
          </button>
          <button className="flex items-center gap-2 hover:text-red-500 transition-colors text-xs font-bold">
            <span className="material-symbols-outlined text-[18px]">delete</span>
            DELETE
          </button>
        </div>
        <button className="ml-2 text-slate-400 hover:text-white">
          <span className="material-symbols-outlined">close</span>
        </button>
      </div>
    </div>
  );
};

export default LeadsListView;
