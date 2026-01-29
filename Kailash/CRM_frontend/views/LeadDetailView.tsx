
import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Lead, LeadStage } from '../types';
import { getLeadAISummary } from '../geminiService';

interface LeadDetailViewProps {
  leads: Lead[];
  onUpdate: (lead: Lead) => void;
}

const LeadDetailView: React.FC<LeadDetailViewProps> = ({ leads, onUpdate }) => {
  const { id } = useParams<{ id: string }>();
  const lead = leads.find(l => l.id === id);
  const [note, setNote] = useState('');
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  if (!lead) return <div className="p-8">Lead not found</div>;

  const handleStageChange = (newStage: LeadStage) => {
    onUpdate({ ...lead, stage: newStage });
  };

  const generateAI = async () => {
    setIsAiLoading(true);
    const summary = await getLeadAISummary(lead);
    setAiSummary(summary);
    setIsAiLoading(false);
  };

  const addNote = () => {
    if (!note.trim()) return;
    const newActivity = {
      id: Date.now().toString(),
      type: 'task' as const,
      title: 'Internal Note',
      description: note,
      timestamp: 'Just now',
      loggedBy: 'Alex Thompson'
    };
    onUpdate({ ...lead, activities: [newActivity, ...lead.activities] });
    setNote('');
  };

  const stages = [LeadStage.DISCOVERY, LeadStage.PROPOSAL, LeadStage.NEGOTIATION, LeadStage.CLOSED];

  return (
    <div className="flex h-screen min-w-0">
      <aside className="w-[30%] border-r border-[#e7eaf3] dark:border-slate-800 bg-white dark:bg-slate-900 overflow-y-auto p-6 flex flex-col gap-6">
        <Link to="/leads" className="flex items-center gap-2 text-slate-400 hover:text-primary transition-colors mb-2 text-sm font-medium">
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Back to Leads
        </Link>
        
        <div className="flex flex-col items-center text-center gap-4 pb-6 border-b border-[#e7eaf3] dark:border-slate-800">
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full min-h-24 w-24 border-4 border-white dark:border-slate-800 shadow-sm" 
            style={{ backgroundImage: `url(https://picsum.photos/seed/${lead.id}/200/200)` }}></div>
          <div className="flex flex-col">
            <h1 className="text-[#0d111c] dark:text-white text-2xl font-bold tracking-tight">{lead.name}</h1>
            <p className="text-[#4b5f9b] dark:text-slate-400 text-sm font-medium">{lead.title}</p>
            <div className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary self-center">
              {lead.priority} Priority Lead
            </div>
          </div>
          <div className="flex w-full gap-2 mt-2">
            <button className="flex-1 bg-primary text-white py-2 px-4 rounded-lg font-bold text-sm hover:bg-blue-700 transition-colors">Convert</button>
            <button className="flex-1 bg-slate-100 dark:bg-slate-800 text-[#0d111c] dark:text-white py-2 px-4 rounded-lg font-bold text-sm hover:bg-slate-200 transition-colors">Edit</button>
          </div>
        </div>

        <div>
          <h3 className="text-[#0d111c] dark:text-white text-sm font-bold uppercase tracking-wider mb-4">Contact Details</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[#4b5f9b] dark:text-slate-400 text-[20px]">mail</span>
              <div>
                <p className="text-[10px] text-[#4b5f9b] dark:text-slate-500 uppercase font-bold">Email</p>
                <p className="text-sm dark:text-slate-300">{lead.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[#4b5f9b] dark:text-slate-400 text-[20px]">call</span>
              <div>
                <p className="text-[10px] text-[#4b5f9b] dark:text-slate-500 uppercase font-bold">Phone</p>
                <p className="text-sm dark:text-slate-300">{lead.phone}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[#4b5f9b] dark:text-slate-400 text-[20px]">public</span>
              <div>
                <p className="text-[10px] text-[#4b5f9b] dark:text-slate-500 uppercase font-bold">LinkedIn</p>
                <a className="text-sm text-primary hover:underline" href={`https://${lead.linkedin}`} target="_blank" rel="noreferrer">{lead.linkedin}</a>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-[#0d111c] dark:text-white text-sm font-bold uppercase tracking-wider mb-4">Company Info</h3>
          <div className="grid grid-cols-1 gap-y-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 p-4">
            <div className="border-b border-[#e7eaf3] dark:border-slate-700 pb-2">
              <p className="text-[#4b5f9b] dark:text-slate-400 text-xs font-normal">Industry</p>
              <p className="text-[#0d111c] dark:text-white text-sm font-medium">{lead.industry}</p>
            </div>
            <div className="border-b border-[#e7eaf3] dark:border-slate-700 pb-2">
              <p className="text-[#4b5f9b] dark:text-slate-400 text-xs font-normal">Employees</p>
              <p className="text-[#0d111c] dark:text-white text-sm font-medium">{lead.employees}</p>
            </div>
            <div>
              <p className="text-[#4b5f9b] dark:text-slate-400 text-xs font-normal">Revenue</p>
              <p className="text-[#0d111c] dark:text-white text-sm font-medium">{lead.revenue}</p>
            </div>
          </div>
        </div>
      </aside>

      <section className="w-[70%] overflow-y-auto bg-background-light dark:bg-background-dark p-8 no-scrollbar">
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-[#e7eaf3] dark:border-slate-800 p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold">Pipeline Stage</h3>
            <p className="text-sm text-[#4b5f9b] dark:text-slate-400">Estimated Value: <span className="text-[#0d111c] dark:text-white font-bold">{lead.estimatedValue}</span></p>
          </div>
          <div className="flex w-full h-12 gap-1 overflow-hidden">
            {stages.map((s, idx) => {
              const isActive = lead.stage === s;
              const isPast = stages.indexOf(lead.stage) > idx;
              return (
                <button
                  key={s}
                  onClick={() => handleStageChange(s)}
                  className={`flex-1 flex items-center justify-center font-bold text-[10px] pipeline-arrow pr-4 transition-all ${
                    isActive ? 'bg-primary text-white shadow-inner border-y-2 border-white dark:border-slate-900' : 
                    isPast ? 'bg-primary/60 text-white' : 
                    'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500'
                  }`}
                >
                  {(isActive || isPast) && <span className="material-symbols-outlined text-[16px] mr-1">check_circle</span>}
                  {s.toUpperCase()}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-[#e7eaf3] dark:border-slate-800 overflow-hidden">
            <div className="border-b border-[#e7eaf3] dark:border-slate-800 p-4 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
              <span className="text-sm font-bold text-[#4b5f9b] dark:text-slate-300">Quick Note & Activity</span>
              <div className="flex gap-2">
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-[#0d111c] dark:text-white hover:bg-slate-200 transition-colors">
                  <span className="material-symbols-outlined text-[18px]">attachment</span>
                  Attach
                </button>
                <button 
                  onClick={addNote}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-primary text-white hover:bg-blue-700 transition-colors"
                >
                  <span className="material-symbols-outlined text-[18px]">add_task</span>
                  Log Activity
                </button>
              </div>
            </div>
            <div className="p-4">
              <textarea 
                className="w-full border-none focus:ring-0 text-sm dark:bg-transparent dark:text-white placeholder:text-slate-400 min-h-[100px] resize-none" 
                placeholder="Type an internal note or summary of your recent interaction..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
              ></textarea>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-[#e7eaf3] dark:border-slate-800 p-8">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold">Activities & Timeline</h3>
              <div className="flex items-center gap-4 text-sm">
                <button onClick={generateAI} className="flex items-center gap-2 bg-emerald-500 text-white px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-emerald-600 transition-colors disabled:opacity-50" disabled={isAiLoading}>
                  <span className="material-symbols-outlined text-[18px]">{isAiLoading ? 'sync' : 'auto_awesome'}</span>
                  {isAiLoading ? 'Analyzing...' : 'AI Insights'}
                </button>
                <div className="h-4 w-px bg-slate-200 dark:bg-slate-700"></div>
                <button className="text-primary font-bold border-b-2 border-primary pb-1">All Activities</button>
                <button className="text-[#4b5f9b] dark:text-slate-400 hover:text-[#0d111c] dark:hover:text-white pb-1">Calls</button>
                <button className="text-[#4b5f9b] dark:text-slate-400 hover:text-[#0d111c] dark:hover:text-white pb-1">Meetings</button>
              </div>
            </div>

            {aiSummary && (
              <div className="mb-8 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-100 dark:border-emerald-800 rounded-xl relative">
                <h4 className="text-emerald-700 dark:text-emerald-400 text-xs font-black uppercase tracking-widest mb-2 flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
                  Gemini AI Suggestion
                </h4>
                <div className="text-sm text-emerald-800 dark:text-emerald-300 whitespace-pre-line leading-relaxed">
                  {aiSummary}
                </div>
                <button onClick={() => setAiSummary(null)} className="absolute top-4 right-4 text-emerald-300 hover:text-emerald-600">
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>
            )}

            <div className="relative pl-8 border-l-2 border-[#e7eaf3] dark:border-slate-800 space-y-10">
              {lead.activities.map(activity => (
                <div key={activity.id} className="relative">
                  <div className={`absolute -left-[45px] top-0 size-8 rounded-full flex items-center justify-center border-4 border-white dark:border-slate-900 ${
                    activity.type === 'call' ? 'bg-blue-100 text-blue-600' :
                    activity.type === 'email' ? 'bg-green-100 text-green-600' :
                    activity.type === 'meeting' ? 'bg-purple-100 text-purple-600' :
                    'bg-orange-100 text-orange-600'
                  }`}>
                    <span className="material-symbols-outlined text-[18px]">
                      {activity.type === 'call' ? 'phone' : 
                       activity.type === 'email' ? 'mail' : 
                       activity.type === 'meeting' ? 'groups' : 'task_alt'}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-bold dark:text-white">{activity.title}</h4>
                      <span className="text-xs text-[#4b5f9b] dark:text-slate-400">{activity.timestamp}</span>
                    </div>
                    <p className="text-sm text-[#4b5f9b] dark:text-slate-400 mt-1">
                      {activity.type === 'task' ? 'Completed by ' : 'Logged by '} 
                      <span className="font-medium text-[#0d111c] dark:text-slate-200">{activity.loggedBy}</span>
                    </p>
                    {activity.description && (
                      <div className={`mt-3 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-sm leading-relaxed ${activity.type === 'meeting' ? 'italic border-l-4 border-primary/30' : ''}`}>
                        {activity.description}
                      </div>
                    )}
                    {activity.attachment && (
                      <div className="mt-3 flex items-center gap-3 p-3 rounded-lg border border-[#e7eaf3] dark:border-slate-700 w-fit">
                        <span className="material-symbols-outlined text-red-500">picture_as_pdf</span>
                        <span className="text-xs font-medium dark:text-slate-300">{activity.attachment.name} ({activity.attachment.size})</span>
                        <button className="text-primary text-[18px]"><span className="material-symbols-outlined">download</span></button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <button className="mt-8 w-full py-3 rounded-lg border border-dashed border-[#e7eaf3] dark:border-slate-700 text-[#4b5f9b] dark:text-slate-400 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              Load older activities...
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LeadDetailView;
