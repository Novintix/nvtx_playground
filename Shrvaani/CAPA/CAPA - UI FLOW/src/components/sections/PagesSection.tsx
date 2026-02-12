import {
  AlertCircle,
  CheckSquare,
  FileInput,
  Search,
  FileBarChart,
  ClipboardList,
  PlayCircle
} from "lucide-react";
import { PageCard } from "@/components/ui/page-card";

const PagesSection = () => {
  const pages = [
    {
      title: "Complaint Page",
      purpose: "Capture quality issues and complaints from internal or external sources.",
      icon: AlertCircle,
      sections: [
        "Search bar & Drop-down Filters (ID, status, severity)",
        "Dashboard cards (Total count, Status count)",
        "Complaint ID & Reference number",
        "Complaint raised by & date",
        "Complaint type → category",
        "Complaint source (Customer/Internal/Audit/Telemetry)",
        "Product/Device identifier (Model/Serial)",
        "Current workflow stage (New/NC/CAPA/Closed)",
        "SLA/age of complaint (days open)"
      ],
      primaryUsers: ["External Reporter"],
      secondaryUsers: ["CAPA Owner (view-only)"],
      status: "active" as const,
    },
    {
      title: "Non-Conformance Page",
      purpose: "Validate whether a complaint is legitimate and determine if CAPA is needed.",
      icon: CheckSquare,
      sections: [
        "Search bar & Filters (ID, severity, date, status)",
        "Dashboard cards (Total count, CAPA needed count)",
        "Linked Complaint ID",
        "NC ID & Validation Status (Pending/Valid/Invalid)",
        "CAPA needed indicator (Yes/No)",
        "Validated by (name + role) & date",
        "Validation checklist (yes/no with comments)",
        "Evidence completeness indicator",
        "Internal notes (non-visible externally)"
      ],
      primaryUsers: ["CAPA Owner", "Reviewer"],
      status: "review" as const,
    },
    {
      title: "CAPA List Page",
      purpose: "Track and manage all CAPAs in the system.",
      icon: FileBarChart,
      sections: [
        "Search bar & Filters (ID, priority, date, status)",
        "Dashboard cards (Total count, Status count)",
        "CAPA ID & Linked NC/Complaint IDs",
        "CAPA status & owner",
        "Category/severity/criticality level",
        "CAPA priority (derived from risk score)",
        "Target closure date & Days overdue",
        "Action buttons (Review/Initiate, View Status)",
        "View CAPA summary button"
      ],
      primaryUsers: ["CAPA Owner"],
      status: "active" as const,
    },
    {
      title: "Risk Score Analysis Page",
      purpose: "AI-driven risk assessment using SOD (Severity, Occurrence, Detection) technique.",
      icon: AlertCircle,
      sections: [
        "Risk score calculated by backend agent",
        "Severity, Occurrence, Detection counts",
        "Criticality level based on score",
        "Threshold reference indicators",
        "Visual indicator (risk matrix or bar)",
        "CAPA Intake button (Navigate to form)",
        "CAPA Reject button (Report download & Comment)"
      ],
      primaryUsers: ["CAPA Owner"],
      status: "active" as const,
    },
    {
      title: "CAPA Intake Page",
      purpose: "Collect structured information to formally initiate CAPA with AI assistance.",
      icon: FileInput,
      sections: [
        "Intake form (auto-fill enabled)",
        "Auto-generated CAPA ID (read-only)",
        "Problem Identification (Cause, Date, Reporter)",
        "Problem Description (Category, Location, Time)",
        "Risk Assessment (Severity, Occurrence, Detection)",
        "Regulatory Linkage",
        "Target completion date",
        "Submit CAPA button (Move to RCA)"
      ],
      primaryUsers: ["CAPA Owner"],
      secondaryUsers: ["Reviewer (view-only)"],
      status: "pending" as const,
    },
    {
      title: "Investigation (RCA) Page",
      purpose: "Identify the root cause using AI-powered analysis (5-Why or Fishbone).",
      icon: Search,
      sections: [
        "Complaint details & Methodology selection",
        "AI-generated RCA result (Fishbone/5-Why)",
        "RCA method justification",
        "Identified/Actual cause & Evidence linkage",
        "Regenerate RCA button",
        "Generate/Regenerate Action Plan buttons",
        "RCA approval status & Reviewer comments"
      ],
      primaryUsers: ["CAPA Owner", "Reviewer"],
      secondaryUsers: ["Reviewer (view-only)"],
      status: "active" as const,
    },
    {
      title: "Action Plan Generation Page",
      purpose: "Define corrective and preventive actions based on RCA with AI recommendations.",
      icon: ClipboardList,
      sections: [
        "List of AI-generated action plans",
        "Action Plan ID & Linked CAPA ID",
        "Action description & Action type (Corrective/Preventive)",
        "Action owner name/designation",
        "Resource requirements & Timeline",
        "Verification method",
        "Status (Completed/Pending/Approved)",
        "Evidence upload for verification"
      ],
      primaryUsers: ["CAPA Owner"],
      secondaryUsers: ["Reviewer (view-only)"],
      status: "active" as const,
    },
    {
      title: "Action Plan Implementation Page",
      purpose: "Enable execution and tracking of assigned actions by action owners.",
      icon: PlayCircle,
      sections: [
        "List of actions to implement/track",
        "Action Plan ID & Linked CAPA ID",
        "Action details & Owner",
        "Action status (Completed/Pending/Approved)",
        "Action type (Corrective/Preventive)",
        "Evidence upload & Verification method",
        "Evidence review status (Pending/Accepted/Rejected)",
        "Reviewed by & Review date",
        "Rework required flag"
      ],
      primaryUsers: ["Action Owner", "External Action Owner"],
      secondaryUsers: ["CAPA Owner"],
      status: "active" as const,
    },
    {
      title: "Action Plan Effectiveness Page",
      purpose: "AI-driven effectiveness evaluation and final CAPA closure with audit trail.",
      icon: FileBarChart,
      sections: [
        "AI effectiveness analysis (Evidence vs Complaint)",
        "Monitoring period (start/end)",
        "Metrics observed (before vs after)",
        "Conclusion (Effective/Not Effective)",
        "Reviewer approval status",
        "Approve CAPA closure button",
        "Redirect to Action Plan button",
        "Generate closure report",
        "Complete audit trail"
      ],
      primaryUsers: ["Reviewer", "Auditor"],
      status: "active" as const,
    },
  ];

  return (
    <section id="pages" className="py-24 bg-slate-50 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.03),transparent)] pointer-events-none" />

      <div className="container relative z-10">
        <div className="text-center mb-20">
          <h2 className="text-4xl md:text-5xl font-black text-slate-900 mb-6 tracking-tight">
            System <span className="text-primary italic">Pages</span>
          </h2>
          <p className="text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed">
            Core workflow interfaces designed for specific roles and stages in the CAPA process.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3 max-w-7xl mx-auto">
          {pages.map((page, index) => (
            <div
              key={index}
              className="animate-fade-in h-full"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <PageCard {...page} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default PagesSection;
