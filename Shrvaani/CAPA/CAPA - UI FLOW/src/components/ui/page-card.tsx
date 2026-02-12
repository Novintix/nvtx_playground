import { useState } from "react";
import { LucideIcon, ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface PageCardProps {
  title: string;
  purpose: string;
  icon: LucideIcon;
  sections: string[];
  primaryUsers: string[];
  secondaryUsers?: string[];
  status?: "active" | "pending" | "review";
}

const PageCard = ({
  title,
  purpose,
  icon: Icon,
  sections,
  primaryUsers,
  secondaryUsers,
  status = "active",
}: PageCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Updated status colors to match screenshot
  const statusColors = {
    active: "bg-emerald-50 text-emerald-600 border-none font-medium px-3 py-0.5",
    pending: "bg-amber-50 text-amber-600 border-none font-medium px-3 py-0.5",
    review: "bg-sky-50 text-sky-600 border-none font-medium px-3 py-0.5",
  };

  const visibleSections = isExpanded ? sections : sections.slice(0, 4);

  return (
    <div className="group h-full flex flex-col relative bg-white rounded-2xl border border-slate-100 p-8 shadow-sm hover:shadow-xl transition-all duration-300">

      {/* Header: Icon + Title + Status */}
      <div className="flex items-start gap-4 mb-6">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-md">
          <Icon className="h-6 w-6 stroke-[2px]" />
        </div>
        <div className="flex-1 min-w-0 pt-0.5">
          <h3 className="font-bold text-lg text-slate-900 mb-2 leading-tight">{title}</h3>
          <Badge variant="outline" className={`rounded-full text-[11px] uppercase tracking-wide ${statusColors[status]}`}>
            {status === "active" ? "Active" : status === "pending" ? "Pending" : "In Review"}
          </Badge>
        </div>
      </div>

      <p className="text-sm text-slate-500 mb-8 leading-relaxed border-b border-slate-100 pb-6 min-h-[5rem]">
        {purpose}
      </p>

      {/* Key Sections */}
      <div className="flex-1 space-y-6">
        <div>
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.1em] mb-3">
            Key Sections
          </h4>
          <div className="flex flex-wrap gap-2">
            {visibleSections.map((section, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-[11px] font-semibold"
              >
                {section}
              </span>
            ))}
            {sections.length > 4 && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="inline-flex items-center px-3 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-400 hover:text-slate-600 text-[11px] font-medium transition-colors"
              >
                {isExpanded ? (
                  <>Show less <ChevronUp className="ml-1 h-3 w-3" /></>
                ) : (
                  <>+{sections.length - 4} more <ChevronDown className="ml-1 h-3 w-3" /></>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Users Section */}
        <div className="pt-6 border-t border-slate-100 mt-auto">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.1em] mb-3">
            Users
          </h4>
          <div className="flex flex-wrap gap-2">
            {primaryUsers.map((user, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-[11px] font-bold"
              >
                {user}
              </span>
            ))}
            {secondaryUsers?.map((user, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full bg-slate-100 text-slate-500 text-[11px] font-medium"
              >
                {user}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export { PageCard };
