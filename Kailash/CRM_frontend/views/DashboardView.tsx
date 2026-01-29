
import React from 'react';
import { Link } from 'react-router-dom';
import { Lead } from '../types';

interface DashboardViewProps {
  leads: Lead[];
}

const DashboardView: React.FC<DashboardViewProps> = ({ leads }) => {
  return (
    <div className="p-8 max-w-6xl mx-auto w-full">
      <div className="mb-10">
        <h1 className="text-[#0d111c] dark:text-white text-3xl font-extrabold tracking-tight mb-2">Welcome back, Team.</h1>
        <p className="text-[#4b5f9b] dark:text-slate-400 text-lg">Manage your sales opportunities and track delivery progress.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        <Link to="/create-lead" className="group relative flex flex-col p-8 bg-primary rounded-xl shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 transition-all">
          <div className="mb-8 flex h-14 w-14 items-center justify-center rounded-xl bg-white/20 text-white backdrop-blur-sm group-hover:scale-110 transition-transform">
            <span className="material-symbols-outlined text-[32px] font-bold">person_add</span>
          </div>
          <div className="mt-auto">
            <h3 className="text-xl font-bold text-white mb-2">Create New Lead</h3>
            <p className="text-blue-100/80 text-sm leading-relaxed max-w-[240px]">Register a new client opportunity and initiate the qualifying process.</p>
          </div>
          <div className="absolute top-8 right-8 text-white/50 group-hover:text-white transition-colors">
            <span className="material-symbols-outlined">arrow_forward</span>
          </div>
        </Link>

        <Link to="/leads" className="group relative flex flex-col p-8 bg-white dark:bg-slate-900 border border-[#cfd5e8] dark:border-slate-800 rounded-xl hover:border-primary transition-all">
          <div className="mb-8 flex h-14 w-14 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800 text-primary group-hover:bg-primary group-hover:text-white transition-all">
            <span className="material-symbols-outlined text-[32px]">view_list</span>
          </div>
          <div className="mt-auto">
            <h3 className="text-xl font-bold text-[#0d111c] dark:text-white mb-2">View All Leads</h3>
            <p className="text-[#4b5f9b] dark:text-slate-400 text-sm leading-relaxed max-w-[240px]">Review and manage your active sales pipeline and follow-ups.</p>
          </div>
          <div className="absolute top-8 right-8 text-slate-300 dark:text-slate-700 group-hover:text-primary transition-colors">
            <span className="material-symbols-outlined">arrow_forward</span>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-[#cfd5e8] dark:border-slate-800 rounded-xl overflow-hidden h-fit">
          <div className="px-6 py-4 border-b border-[#cfd5e8] dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
            <h4 className="text-xs font-bold text-[#0d111c] dark:text-white uppercase tracking-wider">Upcoming Tasks</h4>
            <button className="text-primary text-xs font-bold hover:underline">View Calendar</button>
          </div>
          <div className="divide-y divide-[#cfd5e8] dark:divide-slate-800">
            <div className="px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 rounded-full bg-orange-400"></div>
                <div>
                  <p className="text-sm font-semibold text-[#0d111c] dark:text-white">Proposal Review: BlueTech Solutions</p>
                  <p className="text-xs text-[#4b5f9b] dark:text-slate-400">Due in 2 hours • Assigned to Delivery Team</p>
                </div>
              </div>
              <span className="material-symbols-outlined text-slate-300 dark:text-slate-600 text-[20px]">chevron_right</span>
            </div>
            <div className="px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                <div>
                  <p className="text-sm font-semibold text-[#0d111c] dark:text-white">Follow-up: Orion Systems</p>
                  <p className="text-xs text-[#4b5f9b] dark:text-slate-400">Due Tomorrow • Direct Follow-up</p>
                </div>
              </div>
              <span className="material-symbols-outlined text-slate-300 dark:text-slate-600 text-[20px]">chevron_right</span>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-[#cfd5e8] dark:border-slate-800 rounded-xl p-6 h-fit">
          <h4 className="text-xs font-bold text-[#4b5f9b] dark:text-slate-500 uppercase tracking-widest mb-6">Quick Stats</h4>
          <div className="space-y-6">
            <div>
              <p className="text-[10px] font-bold text-[#4b5f9b] dark:text-slate-400 uppercase tracking-widest mb-1">Active Pipeline</p>
              <p className="text-2xl font-black text-[#0d111c] dark:text-white">$1.2M</p>
            </div>
            <div className="pt-6 border-t border-[#cfd5e8] dark:border-slate-800">
              <p className="text-[10px] font-bold text-[#4b5f9b] dark:text-slate-400 uppercase tracking-widest mb-1">New Leads (24h)</p>
              <p className="text-2xl font-black text-[#0d111c] dark:text-white">12</p>
            </div>
            <div className="pt-6 border-t border-[#cfd5e8] dark:border-slate-800">
              <p className="text-[10px] font-bold text-[#4b5f9b] dark:text-slate-400 uppercase tracking-widest mb-1">Conversion Rate</p>
              <p className="text-2xl font-black text-primary">24.5%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
