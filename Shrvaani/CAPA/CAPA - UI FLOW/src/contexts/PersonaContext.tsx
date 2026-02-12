import React, { createContext, useContext, useState, ReactNode } from "react";

import {
    AlertCircle,
    CheckSquare,
    FileInput,
    Search,
    ClipboardList,
    PlayCircle,
    LayoutDashboard,
    CheckCircle2,
    FileBarChart
} from "lucide-react";

export type WorkflowStage =
    | "COMPLAINT_PAGE"
    | "NON_CONFORMANCE"
    | "RISK_SCORE_ANALYSIS"
    | "CAPA_INTAKE"
    | "INVESTIGATION_RCA"
    | "ACTION_PLAN_GENERATION"
    | "ACTION_PLAN_IMPLEMENTATION"
    | "ACTION_PLAN_EFFECTIVENESS"
    | "CAPA_LIST_PAGE"
    | "COMPLAINT_STATUS"
    | "COMPLETED";

export interface WorkflowStageInfo {
    id: WorkflowStage;
    label: string;
    icon: any;
    color: string;
    purpose: string;
    summary: string;
    timeInfo: string;
    primaryUsers: string[];
    secondaryUsers?: string[];
    sections: string[];
}

export const STAGES: WorkflowStageInfo[] = [
    {
        id: "COMPLAINT_PAGE",
        label: "Complaint Page",
        icon: AlertCircle,
        color: "bg-blue-500",
        purpose: "Capture quality issues and complaints from internal and external sources.",
        summary: "Managing incoming quality signals",
        timeInfo: "2 days ago",
        primaryUsers: ["External Reporter"],
        secondaryUsers: ["CAPA Owner (view-only)"],
        sections: [
            "Complaint ID and reference number",
            "Complaint raised by and date",
            "Complaint type and category",
            "Complaint source (Customer/Internal/Audit/Telemetry)",
            "Product/Device identifier (Model/SKU/Lot/Serial)",
            "Current workflow stage",
            "SLA/age of complaint",
            "Supporting documents/attachments",
            "Dashboard with complaint metrics"
        ]
    },
    {
        id: "NON_CONFORMANCE",
        label: "Non-Conformance Page",
        icon: CheckSquare,
        color: "bg-orange-500",
        purpose: "Validate whether a complaint is legitimate and determine if CAPA is needed.",
        summary: "Assessing issue legitimacy",
        timeInfo: "Today",
        primaryUsers: ["CAPA Owner", "Reviewer"],
        sections: [
            "Linked complaint details",
            "NC ID and validation status",
            "CAPA needed indicator (Yes/No)",
            "Validation checklist",
            "Evidence completeness indicator",
            "Validated by (name + role) and date",
            "Internal notes (not visible to external)",
            "Submit for review button (CAPA Owner)",
            "Approve/Reject NC and Mark CAPA needed (Reviewer)"
        ]
    },
    {
        id: "CAPA_LIST_PAGE",
        label: "CAPA List Page",
        icon: FileBarChart,
        color: "bg-slate-500",
        purpose: "Track and manage all CAPAs in the system.",
        summary: "Reviewing CAPA inventory",
        timeInfo: "Active",
        primaryUsers: ["CAPA Owner"],
        sections: [
            "List of all CAPAs (ID, NC ID, Complaint ID)",
            "CAPA status and priority",
            "CAPA owner assignment",
            "Category/severity/criticality level",
            "Target closure date and days overdue",
            "Search and filter functionality",
            "Dashboard with CAPA metrics"
        ]
    },
    {
        id: "RISK_SCORE_ANALYSIS",
        label: "Risk Score Page",
        icon: AlertCircle,
        color: "bg-red-500",
        purpose: "AI-driven risk assessment using SOD technique.",
        summary: "Evaluating risk criticality",
        timeInfo: "Pending",
        primaryUsers: ["CAPA Owner"],
        sections: [
            "Risk score (RPN) calculated by AI",
            "Severity, Occurrence, Detection scores",
            "Criticality level (Low/Medium/High)",
            "FMEA mapping linkage",
            "Regulatory impact flags",
            "AI Reasoning summary",
            "AI Confidence Score",
            "Threshold reference indicators",
            "Visual risk matrix or bar chart",
            "CAPA Intake or CAPA Reject buttons"
        ]
    },
    {
        id: "CAPA_INTAKE",
        label: "CAPA Intake Page",
        icon: FileInput,
        color: "bg-purple-500",
        purpose: "Collect structured information to formally initiate CAPA with AI assistance.",
        summary: "Structuring CAPA data",
        timeInfo: "Pending",
        primaryUsers: ["CAPA Owner"],
        secondaryUsers: ["Reviewer (view-only)"],
        sections: [
            "Sub-division 1: Problem Identification",
            "Sub-division 2: Problem Description",
            "Sub-division 3: Risk Assessment",
            "Sub-division 4: Regulatory Linkage",
            "Auto-generated CAPA ID (read-only)",
            "Target completion date",
            "Linked SOP/policy references",
            "AI Assistant for form validation"
        ]
    },
    {
        id: "INVESTIGATION_RCA",
        label: "Investigation (RCA) Page",
        icon: Search,
        color: "bg-indigo-500",
        purpose: "Identify the root cause using AI-powered analysis.",
        summary: "Visual root cause analysis",
        timeInfo: "Upcoming",
        primaryUsers: ["CAPA Owner", "RCA Owner"],
        secondaryUsers: ["Reviewer (view-only)"],
        sections: [
            "Problem statement (locked)",
            "RCA methodology selection (5-Why/Fishbone/Hybrid)",
            "AI-generated RCA analysis workspace",
            "Evidence panel with linked documentation",
            "Identified causes and actual/verified root cause",
            "RCA method justification",
            "Generate/Regenerate action plan buttons",
            "Submit for approval",
            "RCA approval status and reviewer comments"
        ]
    },
    {
        id: "ACTION_PLAN_GENERATION",
        label: "Action Plan Generation Page",
        icon: ClipboardList,
        color: "bg-green-500",
        purpose: "Define corrective and preventive actions based on RCA with AI recommendations.",
        summary: "Drafting corrective actions",
        timeInfo: "Future",
        primaryUsers: ["CAPA Owner"],
        secondaryUsers: ["Reviewer (view-only)"],
        sections: [
            "Confirmed root cause summary",
            "List of AI-generated action plans",
            "Action plan ID and description",
            "Action type (Corrective/Preventive)",
            "Assigned action owner",
            "Resource requirements and timeline",
            "Due dates and verification method",
            "Status indicators",
            "QMS procedure linkage"
        ]
    },
    {
        id: "ACTION_PLAN_IMPLEMENTATION",
        label: "Action Plan Implementation Page",
        icon: PlayCircle,
        color: "bg-cyan-500",
        purpose: "Enable execution and tracking of assigned actions by action owners.",
        summary: "Monitoring CAPA lifecycle",
        timeInfo: "Final",
        primaryUsers: ["Action Owner", "External Action Owner"],
        secondaryUsers: ["CAPA Owner"],
        sections: [
            "Assigned actions list with details",
            "Action status (Completed/Pending/Approved)",
            "Evidence upload functionality",
            "Evidence review status (Pending/Accepted/Rejected)",
            "Reviewed by and review date",
            "Rework required flag",
            "Request extension button",
            "Notifications and due date alerts"
        ]
    },
    {
        id: "ACTION_PLAN_EFFECTIVENESS",
        label: "Action Plan Effectiveness Page",
        icon: FileBarChart,
        color: "bg-slate-600",
        purpose: "AI-driven effectiveness evaluation and final CAPA closure with audit trail.",
        summary: "Reviewing system logs",
        timeInfo: "Archives",
        primaryUsers: ["Reviewer", "Auditor"],
        sections: [
            "AI effectiveness analysis (Evidence vs Plan)",
            "Monitoring period (start/end)",
            "Metrics observed (before vs after)",
            "Conclusion (Effective/Not Effective)",
            "Reviewer approval status",
            "Approve CAPA closure button (Reviewer)",
            "Redirect to Action Plan button",
            "Generate closure report",
            "Complete audit trail",
            "Download reports",
            "Compliance verification"
        ]
    },
];

export type PersonaType =
    | "CAPA_OWNER"
    | "REVIEWER"
    | "ACTION_OWNER"
    | "AUDITOR"
    | "EXTERNAL_REPORTER"
    | "EXTERNAL_ACTION_OWNER";

interface PersonaConfig {
    name: string;
    role: string;
    visibleStages: WorkflowStage[];
    editableStages: WorkflowStage[];
}

export const PERSONA_CONFIGS: Record<PersonaType, PersonaConfig> = {
    CAPA_OWNER: {
        name: "CAPA Owner",
        role: "Process Manager",
        visibleStages: [
            "COMPLAINT_PAGE",
            "NON_CONFORMANCE",
            "CAPA_LIST_PAGE",
            "RISK_SCORE_ANALYSIS",
            "CAPA_INTAKE",
            "INVESTIGATION_RCA",
            "ACTION_PLAN_GENERATION",
            "ACTION_PLAN_IMPLEMENTATION",
            "ACTION_PLAN_EFFECTIVENESS"
        ],
        editableStages: [
            "NON_CONFORMANCE",
            "CAPA_LIST_PAGE",
            "RISK_SCORE_ANALYSIS",
            "CAPA_INTAKE",
            "INVESTIGATION_RCA",
            "ACTION_PLAN_GENERATION"
        ]
    },
    REVIEWER: {
        name: "Reviewer / Approver",
        role: "Governance & Authority",
        visibleStages: [
            "COMPLAINT_PAGE",
            "NON_CONFORMANCE",
            "CAPA_LIST_PAGE",
            "RISK_SCORE_ANALYSIS",
            "CAPA_INTAKE",
            "INVESTIGATION_RCA",
            "ACTION_PLAN_GENERATION",
            "ACTION_PLAN_IMPLEMENTATION",
            "ACTION_PLAN_EFFECTIVENESS"
        ],
        editableStages: [
            "NON_CONFORMANCE",
            "ACTION_PLAN_EFFECTIVENESS"
        ]
    },
    ACTION_OWNER: {
        name: "Action Owner",
        role: "Execution Specialist",
        visibleStages: [
            "COMPLAINT_PAGE",
            "CAPA_LIST_PAGE",
            "ACTION_PLAN_GENERATION",
            "ACTION_PLAN_IMPLEMENTATION",
            "ACTION_PLAN_EFFECTIVENESS"
        ],
        editableStages: [
            "ACTION_PLAN_IMPLEMENTATION"
        ]
    },
    AUDITOR: {
        name: "Viewer / Auditor",
        role: "Compliance & Oversight",
        visibleStages: [
            "COMPLAINT_PAGE",
            "NON_CONFORMANCE",
            "CAPA_LIST_PAGE",
            "RISK_SCORE_ANALYSIS",
            "CAPA_INTAKE",
            "INVESTIGATION_RCA",
            "ACTION_PLAN_GENERATION",
            "ACTION_PLAN_IMPLEMENTATION",
            "ACTION_PLAN_EFFECTIVENESS"
        ],
        editableStages: [
            "ACTION_PLAN_EFFECTIVENESS"
        ]
    },
    EXTERNAL_REPORTER: {
        name: "External Reporter",
        role: "Customer / Client",
        visibleStages: [
            "COMPLAINT_PAGE",
            "NON_CONFORMANCE",
            "ACTION_PLAN_EFFECTIVENESS"
        ],
        editableStages: [
            "COMPLAINT_PAGE"
        ]
    },
    EXTERNAL_ACTION_OWNER: {
        name: "External Action Owner",
        role: "Supplier / Vendor",
        visibleStages: [
            "ACTION_PLAN_GENERATION",
            "ACTION_PLAN_IMPLEMENTATION"
        ],
        editableStages: [
            "ACTION_PLAN_IMPLEMENTATION"
        ]
    }
};

interface PersonaContextType {
    persona: PersonaType;
    setPersona: (persona: PersonaType) => void;
    config: PersonaConfig;
    allPersonas: PersonaType[];
    stageIndex: number;
    setStageIndex: (index: number) => void;
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

export const PersonaProvider = ({ children }: { children: ReactNode }) => {
    const [persona, setPersona] = useState<PersonaType>("CAPA_OWNER");
    const [stageIndex, setStageIndex] = useState(0);

    // Reset stage index when persona changes
    React.useEffect(() => {
        setStageIndex(0);
    }, [persona]);

    return (
        <PersonaContext.Provider value={{
            persona,
            setPersona,
            config: PERSONA_CONFIGS[persona],
            allPersonas: Object.keys(PERSONA_CONFIGS) as PersonaType[],
            stageIndex,
            setStageIndex
        }}>
            {children}
        </PersonaContext.Provider>
    );
};

export const usePersona = () => {
    const context = useContext(PersonaContext);
    if (!context) throw new Error("usePersona must be used within a PersonaProvider");
    return context;
};
