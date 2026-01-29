
import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar: React.FC = () => {
  const navItems = [
    { label: 'Dashboard', icon: 'dashboard', path: '/' },
    { label: 'Leads', icon: 'filter_list', path: '/leads' },
    { label: 'Deals', icon: 'handshake', path: '/deals' },
    { label: 'Reports', icon: 'bar_chart', path: '/reports' },
  ];

  return (
    <aside className="w-64 border-r border-[#cfd5e8] dark:border-slate-800 bg-white dark:bg-slate-900 hidden lg:flex flex-col sticky top-0 h-screen">
      <div className="p-6 flex flex-col h-full">
        <div className="flex items-center gap-3 mb-10">
          <div className="bg-primary min-w-[40px] size-10 rounded-lg flex items-center justify-center text-white shrink-0">
            <span className="material-symbols-outlined">hub</span>
          </div>
          <div className="flex flex-col whitespace-nowrap overflow-hidden">
            <h1 className="text-[#0d111c] dark:text-white text-base font-bold leading-none mb-1 truncate">CRM Core</h1>
            <p className="text-[#4b5f9b] dark:text-slate-400 text-xs font-normal truncate">IT Services & Delivery</p>
          </div>
        </div>

        <nav className="flex flex-col gap-2 flex-grow">
          {navItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary font-bold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`
              }
            >
              <span className="material-symbols-outlined text-[22px]">{item.icon}</span>
              <span className="text-sm font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-6 pt-6 border-t border-[#cfd5e8] dark:border-slate-800">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
              }`
            }
          >
            <span className="material-symbols-outlined text-[22px]">settings</span>
            <span className="text-sm font-medium">Settings</span>
          </NavLink>

          <div className="flex items-center gap-3 px-2">
            <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shrink-0 overflow-hidden">
              <img
                alt="Alex Thompson"
                className="w-full h-full object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDxapFELSnmiOEHfrM_QJJEUvA5tI3AqxKcjjyOvJry4z6OdyZRxLAI3gpOWQqxD50wzQDaXFC5CsUhDYM6qQTDPWFzuQI-cTBMkLFszafQRLPy1wxwWPKZjPi44egGA0SF8krPYRVokUsTaOrlLUjq1DiDDq--3ADtciv02-sOLGKxfKoMN8TbWZ8VMXu9f10p6Pi1YpA0TfkX7xYVLMeupkgZoyjnSDX1MC0iXIXhjKTN6BuwDmEsRdSPEPsYemmnDHMT413e81sz"
              />
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="text-sm font-bold text-[#0d111c] dark:text-white truncate">Alex Thompson</span>
              <span className="text-[10px] font-bold text-[#4b5f9b] dark:text-slate-400 uppercase tracking-wider truncate">SENIOR LEAD MANAGER</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
