import { useState } from "react";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
    LayoutDashboard,
    ChevronRight,
    ChevronLeft,
    Users,
    Info,
    Filter,
    ArrowUpRight,
    Circle,
    Dot,
    Paperclip,
    MessageSquare,
    Clock,
    Check,
    ListChecks,
    BarChart3,
    ShieldCheck,
    History,
    FileSearch,
    Download,
    RefreshCw,
    Target,
    Eye,
    Search,
    ClipboardList,
    AlertCircle,
    CheckCircle2,
    FileText,
    PlayCircle,
    CheckSquare,
    FileInput,
    FileBarChart,
    X,
    Zap,
    Calendar,
    Bot
} from "lucide-react";
import { Input } from "@/components/ui/input";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

import { usePersona, WorkflowStage, STAGES } from "@/contexts/PersonaContext";

// Mock Data
const MOCK_COMPLAINTS = [
    {
        id: "CP-9901",
        ref: "REF-2024-001",
        raisedBy: "John Doe",
        raisedDate: "2024-03-01",
        type: "Product Quality",
        status: "In Review",
        severity: "High",
        category: "Hardware Failure",
        source: "Customer",
        productIdentifier: "MD-900 / SN-12345",
        workflowStage: "NC Validation",
        slaDays: 5,
        description: "Unexpected noise during operation of clinical analyzer.",
        attachments: ["Incident_Photo.jpg", "Log_File_0301.txt"]
    },
    {
        id: "CP-9902",
        ref: "REF-2024-002",
        raisedBy: "Alice Smith",
        raisedDate: "2024-03-05",
        type: "Packaging",
        status: "Validated",
        severity: "Medium",
        category: "Sterility Breach",
        source: "Internal",
        productIdentifier: "PK-100 / SN-67890",
        workflowStage: "CAPA Intake",
        slaDays: 2,
        description: "Seal breach in sterile kit shipment.",
        attachments: ["Shipping_Manifest.pdf"]
    },
    {
        id: "CP-9903",
        ref: "REF-2024-003",
        raisedBy: "Bob Johnson",
        raisedDate: "2024-03-10",
        type: "Service Issue",
        status: "New",
        severity: "Low",
        category: "Technical Support",
        source: "Telemetry",
        productIdentifier: "SW-V2 / SN-N/A",
        workflowStage: "Complaint Intake",
        slaDays: 1,
        description: "Delayed response for software installation.",
        attachments: []
    },
];

const MOCK_NCS = [
    {
        ncId: "NC-2024-001",
        id: "CP-9902",
        ref: "REF-2024-002",
        raisedBy: "Alice Smith",
        raisedDate: "2024-03-05",
        type: "Packaging",
        status: "Validated",
        severity: "Medium",
        capaNeeded: "Yes",
        validationStatus: "Submit for Review",
        validatedBy: "Sarah Connor (Quality Manager)",
        validationDate: "2024-03-06",
        checklist: "8/8 Passed",
        evidenceIndicator: "90% (Missing 1/10 Photo)",
        internalNotes: "Issue confirmed at warehouse. Packaging material batch P-099 needs investigation.",
        description: "Seal breach in sterile kit shipment."
    },
];

const MOCK_CAPAS = [
    {
        capaId: "CAPA-2024-001",
        ncId: "NC-2024-001",
        complaintId: "CP-9902",
        status: "In Progress",
        owner: "Michael Scott (Production Head)",
        criticality: "High",
        severity: "High",
        category: "Safety",
        priority: "P1",
        targetDate: "2024-04-15",
        daysOverdue: 0,
    }
];


const CapaWorkflow = () => {
    const { config, persona, stageIndex, setStageIndex } = usePersona();

    type AccessLevel = "FULL" | "READ_ONLY" | "HIDDEN" | "STATUS_ONLY";

    const getAccessLevel = (stageId: string, elementId?: string): AccessLevel => {
        // Default mappings based on the provided matrix
        switch (stageId) {
            case "COMPLAINT_PAGE":
                if (persona === "EXTERNAL_REPORTER") {
                    if (elementId === "MOVE_TO_NC_BUTTON") return "HIDDEN";
                    return "FULL";
                }
                if (persona === "CAPA_OWNER") {
                    if (elementId === "MOVE_TO_NC_BUTTON") return "FULL";
                    if (elementId === "SUBMIT_BUTTON") return "HIDDEN";
                    return "READ_ONLY";
                }
                if (persona === "EXTERNAL_ACTION_OWNER") return "HIDDEN";
                if (elementId === "SUBMIT_BUTTON" || elementId === "MOVE_TO_NC_BUTTON") return "HIDDEN";
                return "READ_ONLY";

            case "NON_CONFORMANCE":
                if (persona === "CAPA_OWNER") {
                    if (elementId === "VALIDATE_NC_BUTTON") return "HIDDEN";
                    return "FULL";
                }
                if (persona === "EXTERNAL_REPORTER") return "STATUS_ONLY";
                if (persona === "REVIEWER" || persona === "AUDITOR") {
                    if (elementId === "VALIDATE_NC_BUTTON") return "FULL";
                    return "READ_ONLY";
                }
                return "HIDDEN";

            case "CAPA_LIST_PAGE":
                if (persona === "CAPA_OWNER") {
                    if (elementId === "INITIATE_CAPA_BUTTON") return "READ_ONLY";
                    return "FULL";
                }
                if (persona === "REVIEWER") {
                    if (elementId === "INITIATE_CAPA_BUTTON") return "FULL";
                    return "READ_ONLY";
                }
                if (persona === "ACTION_OWNER" || persona === "AUDITOR") return "READ_ONLY";
                return "HIDDEN";

            case "RISK_SCORE_ANALYSIS":
                if (persona === "CAPA_OWNER") {
                    if (elementId === "CAPA_INTAKE_BUTTON" || elementId === "CAPA_REJECT_BUTTON") return "READ_ONLY";
                    return "FULL";
                }
                if (persona === "REVIEWER" || persona === "AUDITOR") {
                    if (elementId === "CAPA_INTAKE_BUTTON" || elementId === "CAPA_REJECT_BUTTON") return "FULL";
                    return "READ_ONLY";
                }
                return "HIDDEN";

            case "CAPA_INTAKE":
                if (persona === "CAPA_OWNER") {
                    if (elementId === "CAPA_ID") return "READ_ONLY";
                    return "FULL";
                }
                if (persona === "REVIEWER" || persona === "AUDITOR") return "READ_ONLY";
                return "HIDDEN";

            case "INVESTIGATION_RCA":
                if (persona === "CAPA_OWNER") {
                    if (elementId === "APPROVE_BUTTON" || elementId === "REJECT_BUTTON") return "HIDDEN";
                    return "FULL";
                }
                if (persona === "REVIEWER") {
                    if (elementId === "APPROVE_BUTTON" || elementId === "REJECT_BUTTON") return "FULL";
                    return "READ_ONLY";
                }
                if (persona === "AUDITOR") return "READ_ONLY";
                return "HIDDEN";

            case "ACTION_PLAN_GENERATION":
                if (persona === "CAPA_OWNER") return "FULL";
                if (persona === "EXTERNAL_REPORTER") return "HIDDEN";
                return "READ_ONLY";

            case "ACTION_PLAN_IMPLEMENTATION":
                if (persona === "ACTION_OWNER" || persona === "EXTERNAL_ACTION_OWNER") return "FULL";
                if (persona === "CAPA_OWNER") {
                    if (elementId === "MANAGE_EVIDENCE") return "FULL";
                    return "READ_ONLY";
                }
                if (persona === "REVIEWER" || persona === "AUDITOR") return "READ_ONLY";
                return "HIDDEN";

            case "ACTION_PLAN_EFFECTIVENESS":
                if (persona === "REVIEWER" || persona === "AUDITOR") return "FULL";
                if (persona === "EXTERNAL_REPORTER") return "STATUS_ONLY";
                if (persona === "CAPA_OWNER" || persona === "ACTION_OWNER") return "READ_ONLY";
                return "HIDDEN";

            default:
                return "FULL";
        }
    };

    // Complaint Page State
    const [searchQuery, setSearchQuery] = useState("");
    const [filterSeverity, setFilterSeverity] = useState("All");
    const [filterStatus, setFilterStatus] = useState("All");
    const [selectedComplaintId, setSelectedComplaintId] = useState<string | null>(null);

    // NC Page State
    const [ncSearchQuery, setNcSearchQuery] = useState("");
    const [ncFilterSeverity, setNcFilterSeverity] = useState("All");
    const [ncFilterStatus, setNcFilterStatus] = useState("All");
    const [selectedNcId, setSelectedNcId] = useState<string | null>(null);

    // CAPA Page State
    const [capaSearchQuery, setCapaSearchQuery] = useState("");
    const [capaFilterPriority, setCapaFilterPriority] = useState("All");
    const [capaFilterStatus, setCapaFilterStatus] = useState("All");
    const [selectedCapaId, setSelectedCapaId] = useState<string | null>(null);
    const [showCapaSummary, setShowCapaSummary] = useState(false);

    // Risk Score Page State
    const [showRejectModal, setShowRejectModal] = useState(false);
    const [reviewerComment, setReviewerComment] = useState("");
    const [isCalculatingRiskScore, setIsCalculatingRiskScore] = useState(false);

    // Investigation (RCA) Page State
    const [isGeneratingRCA, setIsGeneratingRCA] = useState(false);
    const [showGeneratingActionPlanModal, setShowGeneratingActionPlanModal] = useState(false);
    const [rcaMethodology, setRcaMethodology] = useState("5-Why");
    const [showFindingRCAModal, setShowFindingRCAModal] = useState(false);
    const [showAuditTrailModal, setShowAuditTrailModal] = useState(false);
    const [showManageAccessModal, setShowManageAccessModal] = useState(false);
    const [showViewMetricsModal, setShowViewMetricsModal] = useState(false);

    // CAPA Intake Form State
    const [intakeFormData, setIntakeFormData] = useState({
        targetDate: "",
        causeOfIssue: "",
        dateRegistered: "",
        registeredBy: "",
        documentDetails: "",
        detailedDescription: "",
        whoRegistered: "",
        category: "",
        whenRecorded: "",
        whereRecorded: "",
        severity: "",
        occurrence: "",
        detection: "",
        regulatoryLinkage: ""
    });

    const handleIntakeChange = (field: string, value: string) => {
        setIntakeFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleAutofillIntake = () => {
        setIntakeFormData({
            targetDate: "2024-06-15",
            causeOfIssue: "Material fatigue in sensor housing.",
            dateRegistered: "2024-03-01T10:45",
            registeredBy: "John Doe",
            documentDetails: "Complaint ID: CP-9902, NC ID: NC-2024-001",
            detailedDescription: "Unexpected noise and vibration occurring after 200 cycles of operation in Module B analyzers.",
            whoRegistered: "John Doe (Customer)",
            category: "Hardware Failure",
            whenRecorded: "2024-03-01",
            whereRecorded: "Customer Site / Clinical Lab 4",
            severity: "9",
            occurrence: "2",
            detection: "1",
            regulatoryLinkage: "This CAPA is linked to ISO 13485:2016 Clause 8.5.2 (Corrective Action) and FDA 21 CFR 820.100."
        });
        alert("Form autofilled with data from Complaint ID: CP-9902 and NC ID: NC-2024-001");
    };

    const handleRegenerateRCA = () => {
        setIsGeneratingRCA(true);
        setTimeout(() => {
            setIsGeneratingRCA(false);
        }, 3000);
    };

    const handleMoveToRCA = () => {
        setShowFindingRCAModal(true);
        setTimeout(() => {
            setShowFindingRCAModal(false);
            setStageIndex(visibleStages.findIndex(s => s.id === "INVESTIGATION_RCA"));
        }, 3000);
    };

    const handleGenerateActionPlan = () => {
        setShowGeneratingActionPlanModal(true);
        setTimeout(() => {
            setShowGeneratingActionPlanModal(false);
            setStageIndex(visibleStages.findIndex(s => s.id === "ACTION_PLAN_GENERATION"));
        }, 3000);
    };

    const handleRejectActionPlan = () => {
        setShowGeneratingActionPlanModal(true);
        // Simulate regeneration
        setTimeout(() => {
            setShowGeneratingActionPlanModal(false);
        }, 3000);
    };


    // Filter stages based on persona visibility
    const visibleStages = STAGES.filter(s => config.visibleStages.includes(s.id));
    const currentStageInfo = visibleStages[stageIndex] || visibleStages[0];

    const nextStage = () => {
        if (stageIndex < visibleStages.length - 1) {
            setStageIndex(stageIndex + 1);
        } else {
            setStageIndex(-1); // Process complete
        }
    };

    const prevStage = () => {
        if (stageIndex > 0) {
            setStageIndex(stageIndex - 1);
        }
    };

    const renderStageContent = () => {
        if (stageIndex === -1) {
            return (
                <div className="animate-in zoom-in-95 duration-700 py-12 flex justify-center">
                    <Card className="w-full max-w-2xl border-none shadow-[0_32px_64px_-16px_rgba(0,0,0,0.15)] rounded-[3rem] overflow-hidden bg-white relative">
                        {/* Decorative Background Elements */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl" />
                        <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500/5 rounded-full translate-y-1/2 -translate-x-1/2 blur-3xl" />

                        {/* Certificate Header */}
                        <div className="bg-slate-900 px-12 py-10 text-center relative">
                            <div className="absolute top-6 left-6 opacity-20">
                                <ShieldCheck className="h-12 w-12 text-white" />
                            </div>
                            <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-emerald-500 shadow-xl shadow-emerald-500/40 mb-6 relative">
                                <CheckCircle2 className="h-10 w-10 text-white" />
                                <div className="absolute inset-0 rounded-full border-4 border-white/20 animate-ping opacity-20" />
                            </div>
                            <h3 className="text-3xl font-black text-white tracking-tight mb-2 uppercase">Closure Certified</h3>
                            <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em]">CAPA Lifecycle ID: CERT-2024-X992</p>
                        </div>

                        <CardContent className="px-12 py-10 space-y-10">
                            {/* Validation Metrics */}
                            <div className="grid grid-cols-3 gap-6">
                                {[
                                    { label: "Completion", val: "100%", sub: "Verify" },
                                    { label: "Effectiveness", val: "94%", sub: "Validated" },
                                    { label: "Regulatory", val: "Verified", sub: "Compliant" }
                                ].map((stat, i) => (
                                    <div key={i} className="text-center p-4 rounded-3xl bg-slate-50 border border-slate-100">
                                        <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">{stat.label}</p>
                                        <p className="text-xl font-black text-slate-900 tracking-tighter">{stat.val}</p>
                                        <p className="text-[8px] font-bold text-emerald-600 uppercase mt-1">{stat.sub}</p>
                                    </div>
                                ))}
                            </div>

                            {/* Certification Body */}
                            <div className="space-y-6">
                                <div className="flex items-center justify-between p-6 bg-slate-50/50 border border-slate-100 rounded-3xl">
                                    <div className="flex items-center gap-4">
                                        <div className="h-12 w-12 rounded-2xl bg-white border border-slate-200 flex items-center justify-center shadow-sm">
                                            <Zap className="h-6 w-6 text-indigo-500" />
                                        </div>
                                        <div>
                                            <p className="text-xs font-bold text-slate-900">AGENTIC-COE-7</p>
                                            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-widest">Digital Audit Primary</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <Badge variant="outline" className="bg-white text-slate-600 text-[10px] font-mono">HASH: 7F2d...91B</Badge>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between p-6 bg-white border border-slate-100 rounded-3xl shadow-lg shadow-slate-200/20">
                                    <div className="flex items-center gap-4">
                                        <div className="h-12 w-12 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                                            <Users className="h-6 w-6" />
                                        </div>
                                        <div>
                                            <p className="text-xs font-bold text-slate-900">Robert Ford</p>
                                            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-widest">Quality Director (E-Sign)</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Date Certified</p>
                                        <p className="text-xs font-bold text-slate-900 font-mono">2026-02-11</p>
                                    </div>
                                </div>
                            </div>

                            {/* Compliance Footnote */}
                            <div className="pt-6 border-t border-slate-100 flex items-center gap-4 text-slate-400 italic">
                                <ShieldCheck className="h-5 w-5 opacity-20" />
                                <p className="text-[10px] font-medium leading-relaxed">This CAPA has been verified against ISO 13485:2016 and 21 CFR 820.100 requirements. Final electronic record locked for retention period.</p>
                            </div>
                        </CardContent>

                        <CardFooter className="px-12 py-8 bg-slate-50 flex flex-col gap-4">
                            <div className="flex w-full gap-3">
                                <Button className="flex-1 h-12 bg-white border-slate-200 text-slate-600 font-bold text-[10px] uppercase tracking-widest shadow-sm hover:shadow-md transition-all rounded-2xl">
                                    <Download className="h-4 w-4 mr-2" /> Download Certificate
                                </Button>
                                <Button className="flex-1 h-12 bg-white border-slate-200 text-slate-600 font-bold text-[10px] uppercase tracking-widest shadow-sm hover:shadow-md transition-all rounded-2xl">
                                    <FileSearch className="h-4 w-4 mr-2" /> Export Audit Trace
                                </Button>
                            </div>
                            <Button
                                variant="ghost"
                                className="w-full text-slate-400 font-black text-[10px] uppercase tracking-[0.3em] h-10 hover:text-indigo-600 transition-colors"
                                onClick={() => setStageIndex(0)}
                            >
                                Start New Lifecycle
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            );
        }

        switch (currentStageInfo.id) {
            case "COMPLAINT_STATUS" as any:
                return (
                    <div className="space-y-6">
                        <div className="border rounded-lg p-6 bg-slate-50">
                            <div className="flex items-center justify-between mb-8">
                                <div>
                                    <p className="text-xs text-slate-500 uppercase font-bold tracking-tight">Current Status</p>
                                    <p className="text-2xl font-bold text-blue-600">In Review</p>
                                </div>
                                <Badge className="bg-blue-100 text-blue-600 border-none px-4 py-1">Case #CP-9901</Badge>
                            </div>
                            <div className="space-y-4">
                                {[
                                    { label: "Submitted", status: "done" },
                                    { label: "Validation", status: "active" },
                                    { label: "RCA", status: "pending" },
                                    { label: "Resolution", status: "pending" }
                                ].map((s, i) => (
                                    <div key={i} className="flex gap-4 items-center">
                                        <div className={`h-3 w-3 rounded-full ${s.status === 'done' ? 'bg-blue-600' : s.status === 'active' ? 'bg-blue-400 animate-pulse' : 'bg-slate-300'}`} />
                                        <span className={`text-sm ${s.status === 'done' ? 'text-slate-500 line-through' : 'font-semibold'}`}>{s.label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <p className="text-[10px] text-slate-400 italic text-center">Your privacy is protected. Internal RCA and Risk data are restricted from this view.</p>
                    </div>
                );
            case "COMPLAINT_PAGE":
                const filteredComplaints = MOCK_COMPLAINTS.filter(c => {
                    const matchesSearch = c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        c.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        c.raisedBy.toLowerCase().includes(searchQuery.toLowerCase());
                    const matchesSeverity = filterSeverity === "All" || c.severity === filterSeverity;
                    const matchesStatus = filterStatus === "All" || c.status === filterStatus;
                    return matchesSearch && matchesSeverity && matchesStatus;
                });

                const selectedComplaint = MOCK_COMPLAINTS.find(c => c.id === selectedComplaintId);

                const getSeverityColor = (sev: string) => {
                    switch (sev) {
                        case "High": return "text-red-600 bg-red-100";
                        case "Medium": return "text-amber-600 bg-amber-100";
                        case "Low": return "text-green-600 bg-green-100";
                        default: return "text-slate-600 bg-slate-100";
                    }
                };

                if (getAccessLevel("COMPLAINT_PAGE") === "HIDDEN") return null;
                const complaintAccess = getAccessLevel("COMPLAINT_PAGE");
                const isComplaintReadOnly = complaintAccess === "READ_ONLY" || complaintAccess === "STATUS_ONLY";

                return (
                    <div className="space-y-6">
                        {/* Dashboard Cards - Total and Status Counts */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <Card className="bg-slate-50 border-none shadow-sm">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold">{MOCK_COMPLAINTS.length}</p>
                                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tight">Total Complaints</p>
                                </CardContent>
                            </Card>
                            <Card className="bg-blue-50 border-none shadow-sm">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold text-blue-600">{MOCK_COMPLAINTS.filter(c => c.status === "New").length}</p>
                                    <p className="text-[10px] text-blue-600/70 uppercase font-bold tracking-tight">New</p>
                                </CardContent>
                            </Card>
                            <Card className="bg-amber-50 border-none shadow-sm">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold text-amber-600">{MOCK_COMPLAINTS.filter(c => c.status === "In Review").length}</p>
                                    <p className="text-[10px] text-amber-600/70 uppercase font-bold tracking-tight">In Review</p>
                                </CardContent>
                            </Card>
                            <Card className="bg-green-50 border-none shadow-sm">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold text-green-600">{MOCK_COMPLAINTS.filter(c => c.status === "Validated").length}</p>
                                    <p className="text-[10px] text-green-600/70 uppercase font-bold tracking-tight">Validated</p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Search and Filters */}
                        <div className="flex flex-col md:flex-row gap-4 items-center bg-white p-4 rounded-xl border border-slate-100 shadow-sm relative overflow-hidden">
                            <div className="flex justify-between items-center w-full md:w-auto gap-4">
                                {getAccessLevel("COMPLAINT_PAGE", "SUBMIT_BUTTON") === "FULL" && (
                                    <Button className="gradient-primary text-white border-none shadow-lg px-6 h-10 text-[10px] uppercase font-black tracking-widest hover:scale-105 transition-transform shrink-0">
                                        Submit Complaint
                                    </Button>
                                )}
                            </div>
                            <div className="absolute top-0 right-0 px-3 py-0.5 bg-indigo-50 border-b border-l border-indigo-100 rounded-bl-lg flex items-center gap-1.5">
                                <Zap className="h-3 w-3 text-indigo-500" />
                                <span className="text-[9px] font-black text-indigo-600 uppercase tracking-widest">Complaint Injector Agent</span>
                            </div>
                            <div className="relative flex-1 w-full">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search by ID, Description, or Reporter..."
                                    className="pl-10 h-10 border-slate-200"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <div className="flex gap-2 w-full md:w-auto">
                                <select
                                    className="h-10 px-3 border border-slate-200 rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-primary/20"
                                    value={filterSeverity}
                                    onChange={(e) => setFilterSeverity(e.target.value)}
                                >
                                    <option value="All">All Severities</option>
                                    <option value="High">High</option>
                                    <option value="Medium">Medium</option>
                                    <option value="Low">Low</option>
                                </select>
                                <select
                                    className="h-10 px-3 border border-slate-200 rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-primary/20"
                                    value={filterStatus}
                                    onChange={(e) => setFilterStatus(e.target.value)}
                                >
                                    <option value="All">All Statuses</option>
                                    <option value="New">New</option>
                                    <option value="In Review">In Review</option>
                                    <option value="Validated">Validated</option>
                                </select>
                            </div>
                        </div>

                        <div className={`grid grid-cols-1 gap-6 transition-all duration-500 ${selectedComplaintId ? 'lg:grid-cols-2' : 'lg:grid-cols-1'}`}>
                            {/* Complaint List */}
                            <div className={`space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar`}>
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="text-xs font-bold uppercase text-slate-400">Available Complaints</h4>
                                    {!selectedComplaintId && <p className="text-[10px] text-slate-400 italic">Select a case to view full details</p>}
                                </div>
                                {filteredComplaints.length > 0 ? (
                                    filteredComplaints.map(complaint => (
                                        <div
                                            key={complaint.id}
                                            onClick={() => setSelectedComplaintId(complaint.id)}
                                            className={`p-4 rounded-xl border transition-all cursor-pointer ${selectedComplaintId === complaint.id
                                                ? "border-primary bg-primary/5 shadow-md scale-[1.02]"
                                                : "border-slate-100 hover:border-slate-300 bg-white hover:shadow-sm"
                                                }`}
                                        >
                                            <div className="flex justify-between items-start mb-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm font-bold text-slate-900">{complaint.id}</span>
                                                    <Badge variant="outline" className="text-[9px] h-4 px-1 leading-none border-slate-200 text-slate-500 uppercase">{complaint.status}</Badge>
                                                </div>
                                                <Badge className={`${getSeverityColor(complaint.severity)} border-none text-[10px]`}>
                                                    {complaint.severity}
                                                </Badge>
                                            </div>
                                            <p className="text-xs text-slate-700 font-medium line-clamp-1">{complaint.description}</p>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-20 border-2 border-dashed rounded-xl bg-white">
                                        <Search className="h-10 w-10 text-slate-200 mx-auto mb-4" />
                                        <p className="text-slate-400 text-sm">No complaints found matching your criteria.</p>
                                    </div>
                                )}
                            </div>

                            {/* Selection Detail View */}
                            {selectedComplaint && (
                                <div className="animate-in fade-in slide-in-from-right-8 duration-500">
                                    <Card className="border-slate-100 shadow-xl ring-1 ring-slate-200/50 sticky top-4">
                                        <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-4">
                                            <div className="flex justify-between items-center">
                                                <div className="flex items-center gap-3">
                                                    <div className={`h-2 w-2 rounded-full ${selectedComplaint.status === 'New' ? 'bg-blue-400' : 'bg-success'}`} />
                                                    <CardTitle className="text-lg">Case Detail View</CardTitle>
                                                </div>
                                                <Button variant="ghost" size="sm" onClick={() => setSelectedComplaintId(null)} className="h-8 w-8 p-0 rounding-full">
                                                    <ChevronLeft className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="pt-6 space-y-5">
                                            <div className="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Complaint ID</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.id}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Ref Number</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.ref}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Raised By</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.raisedBy}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Raised Date</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.raisedDate}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Complaint Type</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.type}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Status</p>
                                                    <Badge variant="outline" className="text-[10px]">{selectedComplaint.status}</Badge>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Category</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.category}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Source</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.source}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Product/Device ID</p>
                                                    <p className="text-sm font-semibold text-xs">{selectedComplaint.productIdentifier}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Workflow Stage</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.workflowStage}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">SLA (Days Open)</p>
                                                    <p className="text-sm font-semibold">{selectedComplaint.slaDays} Days</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Severity</p>
                                                    <Badge className={`${getSeverityColor(selectedComplaint.severity)} border-none text-[10px]`}>
                                                        {selectedComplaint.severity}
                                                    </Badge>
                                                </div>
                                            </div>

                                            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Detailed Narrative</p>
                                                <p className="text-sm text-slate-700 leading-relaxed mb-4">
                                                    {selectedComplaint.description}
                                                </p>
                                                {selectedComplaint.attachments && selectedComplaint.attachments.length > 0 && (
                                                    <div className="space-y-2">
                                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Supporting Documents</p>
                                                        <div className="flex flex-wrap gap-2">
                                                            {selectedComplaint.attachments.map((file: string, idx: number) => (
                                                                <Badge key={idx} variant="secondary" className="bg-white border text-slate-600 flex gap-1 items-center px-2 py-1">
                                                                    <Paperclip className="h-3 w-3" /> {file}
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>

                                            <div className="flex gap-3">
                                                {getAccessLevel("COMPLAINT_PAGE", "MOVE_TO_NC_BUTTON") !== "HIDDEN" && (
                                                    <Button
                                                        className="flex-1 gap-2 gradient-primary text-white border-none shadow-md shadow-primary/20"
                                                        size="sm"
                                                        disabled={getAccessLevel("COMPLAINT_PAGE", "MOVE_TO_NC_BUTTON") !== "FULL"}
                                                        onClick={() => {
                                                            setStageIndex(visibleStages.findIndex(s => s.id === "NON_CONFORMANCE"));
                                                        }}
                                                    >
                                                        <ArrowUpRight className="h-4 w-4" /> Move to NC
                                                    </Button>
                                                )}
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="flex-1"
                                                    disabled={isComplaintReadOnly}
                                                >
                                                    Edit Details
                                                </Button>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </div>
                            )}
                        </div>
                    </div>
                );
            case "NON_CONFORMANCE":
                const ncAccess = getAccessLevel("NON_CONFORMANCE");
                if (ncAccess === "HIDDEN") return null;

                const filteredNcs = MOCK_NCS.filter(nc => {
                    const matchesSearch = nc.ncId.toLowerCase().includes(ncSearchQuery.toLowerCase()) ||
                        nc.id.toLowerCase().includes(ncSearchQuery.toLowerCase()) ||
                        nc.ref.toLowerCase().includes(ncSearchQuery.toLowerCase());
                    const matchesSeverity = ncFilterSeverity === "All" || nc.severity === ncFilterSeverity;
                    const matchesStatus = ncFilterStatus === "All" || nc.status === ncFilterStatus;
                    return matchesSearch && matchesSeverity && matchesStatus;
                });

                const selectedNc = MOCK_NCS.find(nc => nc.ncId === selectedNcId);
                const isNcReadOnly = ncAccess === "READ_ONLY" || ncAccess === "STATUS_ONLY";

                if (ncAccess === 'STATUS_ONLY') {
                    return (
                        <div className="space-y-6">
                            <div className="border rounded-xl p-8 bg-slate-50 text-center">
                                <CheckSquare className="h-12 w-12 text-blue-500 mx-auto mb-4" />
                                <h3 className="text-xl font-bold mb-2">Non-Conformance Validation Status</h3>
                                <p className="text-slate-500 mb-6">Your complaint is currently undergoing formal internal validation.</p>
                                <div className="max-w-md mx-auto bg-white p-4 rounded-lg border border-slate-100 shadow-sm">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-xs font-bold text-slate-400 uppercase">Current Stage</span>
                                        <Badge className="bg-blue-100 text-blue-600 border-none">Validation in Progress</Badge>
                                    </div>
                                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                                        <div className="bg-blue-500 h-full w-1/3" />
                                    </div>
                                </div>
                            </div>
                            <p className="text-[10px] text-slate-400 italic text-center">Detailed validation checklists and internal notes are restricted from external view.</p>
                        </div>
                    );
                }

                return (
                    <div className="space-y-6">
                        {/* NC Dashboard */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <Card className="bg-slate-50 border-slate-200">
                                <CardContent className="p-4 flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-xl bg-slate-900 text-white flex items-center justify-center">
                                        <ListChecks className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total NCs</p>
                                        <p className="text-xl font-bold text-slate-900">{MOCK_NCS.length}</p>
                                    </div>
                                </CardContent>
                            </Card>
                            <Card className="bg-slate-50 border-slate-200">
                                <CardContent className="p-4 flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-xl bg-indigo-500 text-white flex items-center justify-center">
                                        <PlayCircle className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">CAPA Needed</p>
                                        <p className="text-xl font-bold text-slate-900">
                                            {MOCK_NCS.filter(n => n.capaNeeded === "Yes").length}
                                        </p>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Search & Filters */}
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search by NC ID, Complaint ID or Ref..."
                                    className="pl-10 h-10 border-slate-200"
                                    value={ncSearchQuery}
                                    onChange={(e) => setNcSearchQuery(e.target.value)}
                                />
                            </div>
                            <div className="flex gap-2">
                                <select
                                    className="h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 outline-none"
                                    value={ncFilterSeverity}
                                    onChange={(e) => setNcFilterSeverity(e.target.value)}
                                >
                                    <option>All Severities</option>
                                    <option>High</option>
                                    <option>Medium</option>
                                    <option>Low</option>
                                </select>
                                <select
                                    className="h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 outline-none"
                                    value={ncFilterStatus}
                                    onChange={(e) => setNcFilterStatus(e.target.value)}
                                >
                                    <option>All Status</option>
                                    <option>New</option>
                                    <option>In Progress</option>
                                    <option>Closed</option>
                                </select>
                                <select
                                    className="h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 outline-none"
                                >
                                    <option>All Dates</option>
                                    <option>Last 7 Days</option>
                                    <option>Last 30 Days</option>
                                    <option>Last 90 Days</option>
                                </select>
                            </div>
                        </div>

                        {/* Dual-Pane View */}
                        <div className="flex flex-col lg:flex-row gap-6 min-h-[500px]">
                            {/* NC List */}
                            <div className={`${selectedNcId ? 'lg:w-[40%]' : 'w-full'} space-y-3 transition-all duration-300`}>
                                {filteredNcs.map((nc) => (
                                    <div
                                        key={nc.ncId}
                                        onClick={() => setSelectedNcId(nc.ncId)}
                                        className={`group p-4 rounded-xl border-2 transition-all cursor-pointer ${selectedNcId === nc.ncId ? 'border-primary bg-primary/5 shadow-md' : 'border-slate-50 bg-white hover:border-slate-200 shadow-sm'}`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <Badge variant="outline" className="text-[10px] font-bold mb-1 border-slate-200 text-slate-500">
                                                    {nc.ncId}
                                                </Badge>
                                                <h4 className="text-sm font-bold text-slate-900">{nc.ref}</h4>
                                            </div>
                                            <Badge className={nc.severity === "High" ? "bg-red-500" : nc.severity === "Medium" ? "bg-orange-500" : "bg-blue-500"}>
                                                {nc.severity}
                                            </Badge>
                                        </div>
                                        <div className="flex items-center gap-4 text-[10px] text-slate-500 font-medium">
                                            <span className="flex items-center gap-1"><Users className="h-3 w-3" /> {nc.id}</span>
                                            <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {nc.raisedDate}</span>
                                            <Badge variant="secondary" className="text-[9px] h-4">{nc.status}</Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* NC Detail Panel */}
                            {selectedNcId && selectedNc && (
                                <div className="flex-1 lg:w-[60%] animate-in slide-in-from-right-4 duration-300">
                                    <Card className="border-slate-200 shadow-xl sticky top-20">
                                        <CardHeader className="pb-4 border-b border-slate-100 flex-row justify-between items-start">
                                            <div className="flex items-center gap-4">
                                                <div className="p-3 bg-indigo-50 rounded-2xl text-indigo-600">
                                                    <CheckSquare className="h-6 w-6" />
                                                </div>
                                                <div>
                                                    <CardTitle className="text-xl">{selectedNc.ncId}</CardTitle>
                                                    <CardDescription className="text-[10px] uppercase font-bold tracking-widest text-indigo-500">{selectedNc.ref}</CardDescription>
                                                </div>
                                            </div>
                                            <Button variant="ghost" size="icon" onClick={() => setSelectedNcId(null)}>×</Button>
                                        </CardHeader>
                                        <CardContent className="py-6 space-y-6">
                                            <div className="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">NC ID</p>
                                                    <p className="text-sm font-semibold">{selectedNc.ncId}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Complaint ID</p>
                                                    <p className="text-sm font-semibold">{selectedNc.id}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Validation Status</p>
                                                    <Badge variant="secondary" className="text-xs">{selectedNc.validationStatus}</Badge>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">CAPA Needed</p>
                                                    <Badge variant="outline" className={selectedNc.capaNeeded === "Yes" ? "bg-green-50 text-green-700 border-green-200" : "bg-slate-50 text-slate-500"}>
                                                        {selectedNc.capaNeeded}
                                                    </Badge>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Validated By</p>
                                                    <p className="text-sm font-semibold">{selectedNc.validatedBy}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Validation Date</p>
                                                    <p className="text-sm font-semibold">{selectedNc.validationDate}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Checklist (Pass/Fail)</p>
                                                    <p className="text-sm font-semibold">{selectedNc.checklist}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Evidence Indicator</p>
                                                    <p className="text-sm font-semibold">{selectedNc.evidenceIndicator}</p>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Severity</p>
                                                    <Badge className={selectedNc.severity === "High" ? "bg-red-500" : selectedNc.severity === "Medium" ? "bg-orange-500" : "bg-blue-500"}>
                                                        {selectedNc.severity}
                                                    </Badge>
                                                </div>
                                            </div>

                                            {(persona === "CAPA_OWNER" || persona === "REVIEWER" || persona === "AUDITOR") && (
                                                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Internal Notes (Non-Visible Externally)</p>
                                                    <p className="text-sm text-slate-600 italic">
                                                        {selectedNc.internalNotes}
                                                    </p>
                                                </div>
                                            )}

                                            <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">NC Description</p>
                                                <p className="text-sm text-slate-700 leading-relaxed">
                                                    {selectedNc.description}
                                                </p>
                                            </div>

                                            <div className="flex gap-3 pt-4 border-t border-slate-100">
                                                {getAccessLevel("NON_CONFORMANCE", "VALIDATE_NC_BUTTON") === "FULL" && (
                                                    <Button
                                                        className="flex-1 gradient-primary text-white border-none shadow-lg"
                                                        onClick={() => {
                                                            alert("NC Validated and Marked for CAPA");
                                                            setStageIndex(visibleStages.findIndex(s => s.id === "CAPA_LIST_PAGE"));
                                                        }}
                                                    >
                                                        Validate NC & Mark CAPA Needed
                                                    </Button>
                                                )}
                                                <Button variant="outline" className="flex-1" disabled={isNcReadOnly}>
                                                    Edit NC Details
                                                </Button>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </div>
                            )}
                        </div>
                    </div>
                );
            case "CAPA_LIST_PAGE":
                const capaAccess = getAccessLevel("CAPA_LIST_PAGE");
                if (capaAccess === "HIDDEN") return null;
                const isCapaReadOnly = capaAccess === "READ_ONLY";

                const filteredCapas = MOCK_CAPAS.filter(c => {
                    const matchesSearch = c.capaId.toLowerCase().includes(capaSearchQuery.toLowerCase()) ||
                        c.ncId.toLowerCase().includes(capaSearchQuery.toLowerCase()) ||
                        c.complaintId.toLowerCase().includes(capaSearchQuery.toLowerCase());
                    const matchesPriority = capaFilterPriority === "All" || c.priority === capaFilterPriority;
                    const matchesStatus = capaFilterStatus === "All" || c.status === capaFilterStatus;
                    return matchesSearch && matchesPriority && matchesStatus;
                });
                const selectedCapa = MOCK_CAPAS.find(c => c.capaId === selectedCapaId);

                return (
                    <div className="space-y-6">
                        {/* CAPA Dashboard - Total and Status Counts */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <Card className="bg-slate-50 border-none">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold">{MOCK_CAPAS.length}</p>
                                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tight">Total CAPA</p>
                                </CardContent>
                            </Card>
                            <Card className="bg-blue-50 border-none">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold text-blue-600">{MOCK_CAPAS.filter(c => c.status === "New").length}</p>
                                    <p className="text-[10px] text-blue-600/70 uppercase font-bold tracking-tight">New</p>
                                </CardContent>
                            </Card>
                            <Card className="bg-amber-50 border-none">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold text-amber-600">{MOCK_CAPAS.filter(c => c.status === "In Progress").length}</p>
                                    <p className="text-[10px] text-amber-600/70 uppercase font-bold tracking-tight">In Progress</p>
                                </CardContent>
                            </Card>
                            <Card className="bg-green-50 border-none">
                                <CardContent className="p-4 text-center">
                                    <p className="text-2xl font-bold text-green-600">{MOCK_CAPAS.filter(c => c.status === "Completed").length}</p>
                                    <p className="text-[10px] text-green-600/70 uppercase font-bold tracking-tight">Completed</p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Search & Filters */}
                        <div className="flex flex-col md:flex-row gap-4 items-center bg-white p-4 rounded-xl border border-slate-100 shadow-sm">
                            <div className="relative flex-1 w-full">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search by CAPA, NC, or Complaint ID..."
                                    className="pl-10 h-10"
                                    value={capaSearchQuery}
                                    onChange={(e) => setCapaSearchQuery(e.target.value)}
                                />
                            </div>
                            <div className="flex gap-2 w-full md:w-auto">
                                <select
                                    className="h-10 px-3 border border-slate-200 rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-primary/20"
                                    value={capaFilterPriority}
                                    onChange={(e) => setCapaFilterPriority(e.target.value)}
                                >
                                    <option value="All">All Priorities</option>
                                    <option value="Critical">Critical</option>
                                    <option value="High">High</option>
                                    <option value="Medium">Medium</option>
                                    <option value="Low">Low</option>
                                </select>
                                <select
                                    className="h-10 px-3 border border-slate-200 rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-primary/20"
                                    value={capaFilterStatus}
                                    onChange={(e) => setCapaFilterStatus(e.target.value)}
                                >
                                    <option value="All">All Status</option>
                                    <option value="New">New</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="Completed">Completed</option>
                                </select>
                                <select
                                    className="h-10 px-3 border border-slate-200 rounded-md text-sm bg-white outline-none focus:ring-2 focus:ring-primary/20"
                                >
                                    <option>All Dates</option>
                                    <option>Last 7 Days</option>
                                    <option>Last 30 Days</option>
                                    <option>Last 90 Days</option>
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="space-y-3">
                                {filteredCapas.map(capa => (
                                    <div
                                        key={capa.capaId}
                                        onClick={() => setSelectedCapaId(capa.capaId)}
                                        className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedCapaId === capa.capaId ? 'border-primary bg-primary/5 shadow-md' : 'bg-white hover:border-slate-300'}`}
                                    >
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-sm font-bold">{capa.capaId}</span>
                                            <Badge className={capa.criticality === "High" ? "bg-red-500" : "bg-blue-500"}>{capa.criticality}</Badge>
                                        </div>
                                        <div className="flex justify-between text-[10px] text-slate-500">
                                            <span>NC: {capa.ncId}</span>
                                            <span>Target: {capa.targetDate}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {selectedCapa && (
                                <Card className="border-slate-100 shadow-xl">
                                    <CardHeader className="py-4 bg-slate-50/50">
                                        <CardTitle className="text-lg">CAPA Details</CardTitle>
                                    </CardHeader>
                                    <CardContent className="pt-6 space-y-6">
                                        <div className="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-6">
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">CAPA ID</p>
                                                <p className="text-sm font-semibold">{selectedCapa.capaId}</p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">NC ID</p>
                                                <p className="text-sm font-semibold">{selectedCapa.ncId}</p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Complaint ID</p>
                                                <p className="text-sm font-semibold">{selectedCapa.complaintId}</p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">CAPA Status</p>
                                                <Badge variant="outline" className="text-xs">{selectedCapa.status}</Badge>
                                            </div>
                                            <div className="col-span-2">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">CAPA Owner</p>
                                                <p className="text-sm font-semibold">{selectedCapa.owner}</p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Category</p>
                                                <p className="text-sm font-semibold">{selectedCapa.category}</p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Severity</p>
                                                <Badge className={selectedCapa.severity === "High" ? "bg-red-500" : "bg-blue-500"}>{selectedCapa.severity}</Badge>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Criticality Level</p>
                                                <Badge className={selectedCapa.criticality === "High" ? "bg-red-500" : "bg-blue-500"}>{selectedCapa.criticality}</Badge>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">CAPA Priority</p>
                                                <p className="text-sm font-semibold">{selectedCapa.priority}</p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Target Closure Date</p>
                                                <p className="text-sm font-semibold">{selectedCapa.targetDate}</p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Days Overdue</p>
                                                <p className={`text-sm font-semibold ${selectedCapa.daysOverdue > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                                    {selectedCapa.daysOverdue > 0 ? `${selectedCapa.daysOverdue} days` : 'On Track'}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Action Buttons */}
                                        <div className="flex gap-2 pt-4 border-t">
                                            {getAccessLevel("CAPA_LIST_PAGE", "INITIATE_CAPA_BUTTON") === "FULL" && (
                                                <Button
                                                    size="sm"
                                                    className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                                                    onClick={() => {
                                                        setIsCalculatingRiskScore(true);
                                                        // Simulate backend calculation delay
                                                        setTimeout(() => {
                                                            setIsCalculatingRiskScore(false);
                                                            setStageIndex(visibleStages.findIndex(s => s.id === "RISK_SCORE_ANALYSIS"));
                                                        }, 2500); // 2.5 second delay
                                                    }}
                                                >
                                                    Review & Initiate CAPA
                                                </Button>
                                            )}
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                className="flex-1"
                                                onClick={() => {
                                                    // Navigate based on CAPA status
                                                    if (selectedCapa.status === "New") {
                                                        // New CAPA - go to Risk Score Analysis
                                                        setStageIndex(visibleStages.findIndex(s => s.id === "RISK_SCORE_ANALYSIS"));
                                                    } else if (selectedCapa.status === "In Progress") {
                                                        // In Progress - go to Action Plan Implementation
                                                        setStageIndex(visibleStages.findIndex(s => s.id === "ACTION_PLAN_IMPLEMENTATION"));
                                                    } else if (selectedCapa.status === "Completed") {
                                                        // Completed - go to Effectiveness page
                                                        setStageIndex(visibleStages.findIndex(s => s.id === "ACTION_PLAN_EFFECTIVENESS"));
                                                    }
                                                }}
                                            >
                                                View Status / Continue
                                            </Button>
                                        </div>

                                        {/* View CAPA Summary Button */}
                                        <Button
                                            variant="ghost"
                                            className="w-full text-xs text-primary"
                                            onClick={() => setShowCapaSummary(!showCapaSummary)}
                                        >
                                            {showCapaSummary ? "Hide CAPA Summary" : "View CAPA Summary"}
                                        </Button>

                                        {/* CAPA Summary Expandable Section */}
                                        {showCapaSummary && (
                                            <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-4">
                                                <h3 className="text-sm font-bold text-slate-700 mb-3">Complete Complaint Journey</h3>

                                                {/* Complaint Stage */}
                                                <div className="p-3 bg-white rounded-lg border border-blue-200">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Badge className="bg-blue-500">Stage 1: Complaint</Badge>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Complaint ID</p>
                                                            <p className="font-semibold">{selectedCapa.complaintId}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Reported By</p>
                                                            <p className="font-semibold">John Doe (Customer)</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Date Raised</p>
                                                            <p className="font-semibold">2024-03-15</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Severity</p>
                                                            <Badge variant="outline" className="text-[9px]">{selectedCapa.severity}</Badge>
                                                        </div>
                                                        <div className="col-span-2">
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Description</p>
                                                            <p className="text-xs">Device malfunction during operation causing safety concern</p>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* NC Stage */}
                                                <div className="p-3 bg-white rounded-lg border border-orange-200">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Badge className="bg-orange-500">Stage 2: Non-Conformance</Badge>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">NC ID</p>
                                                            <p className="font-semibold">{selectedCapa.ncId}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Validation Status</p>
                                                            <Badge variant="outline" className="text-[9px] bg-green-50">Valid</Badge>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">CAPA Needed</p>
                                                            <p className="font-semibold text-green-600">Yes</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Validated By</p>
                                                            <p className="font-semibold">Jane Smith (QA Lead)</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Validation Date</p>
                                                            <p className="font-semibold">2024-03-18</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Evidence Completeness</p>
                                                            <p className="font-semibold">90%</p>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* CAPA Stage */}
                                                <div className="p-3 bg-white rounded-lg border border-slate-300">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Badge className="bg-slate-600">Stage 3: CAPA</Badge>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">CAPA ID</p>
                                                            <p className="font-semibold">{selectedCapa.capaId}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Status</p>
                                                            <Badge variant="outline" className="text-[9px]">{selectedCapa.status}</Badge>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Priority</p>
                                                            <p className="font-semibold">{selectedCapa.priority}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Criticality</p>
                                                            <Badge className={selectedCapa.criticality === "High" ? "bg-red-500 text-[9px]" : "bg-blue-500 text-[9px]"}>{selectedCapa.criticality}</Badge>
                                                        </div>
                                                        <div className="col-span-2">
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Owner</p>
                                                            <p className="font-semibold">{selectedCapa.owner}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Target Date</p>
                                                            <p className="font-semibold">{selectedCapa.targetDate}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-slate-400 uppercase text-[9px] font-bold">Days Overdue</p>
                                                            <p className={`font-semibold ${selectedCapa.daysOverdue > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                                                {selectedCapa.daysOverdue > 0 ? `${selectedCapa.daysOverdue} days` : 'On Track'}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </div>
                );
            case "RISK_SCORE_ANALYSIS":
                const riskAccess = getAccessLevel("RISK_SCORE_ANALYSIS");
                if (riskAccess === "HIDDEN") return null;
                const isRiskReadOnly = riskAccess === "READ_ONLY";

                return (
                    <div className="space-y-8">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <Card className="border-slate-200 shadow-lg">
                                <CardHeader className="bg-slate-50/50 py-4">
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <BarChart3 className="h-5 w-5 text-primary" /> Risk Score Details
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="pt-6 space-y-6">
                                    <div className="flex items-center justify-between p-6 bg-red-50 rounded-2xl border border-red-100">
                                        <div>
                                            <p className="text-xs font-bold text-red-600 uppercase tracking-widest mb-1">Calculated Risk Score</p>
                                            <p className="text-4xl font-black text-red-700">85 / 100</p>
                                        </div>
                                        <Badge className="bg-red-600 text-white px-4 py-2 text-lg">CRITICAL</Badge>
                                    </div>

                                    <div className="grid grid-cols-3 gap-4 text-center">
                                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Severity</p>
                                            <p className="text-xl font-bold">9</p>
                                        </div>
                                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Occurrence</p>
                                            <p className="text-xl font-bold">7</p>
                                        </div>
                                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Detection</p>
                                            <p className="text-xl font-bold">3</p>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Collaborating AI Agents</p>
                                            <div className="flex flex-wrap gap-2">
                                                {[
                                                    "CAPA Validator Agent",
                                                    "FMEA Mapping Agent",
                                                    "Risk Score Calculator",
                                                    "Regulatory Agent",
                                                    "AI Reasoning Agent",
                                                    "Confidence Score Agent",
                                                    "CAPA Needed Agent"
                                                ].map((agent, i) => (
                                                    <Badge key={i} variant="outline" className="bg-white border-slate-200 text-slate-500 text-[9px] font-bold py-0.5">
                                                        {agent}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-xl space-y-3">
                                            <div className="flex justify-between items-center">
                                                <p className="text-xs font-bold text-blue-800 uppercase">AI Reasoning & Confidence</p>
                                                <Badge className="bg-blue-600 text-white text-[10px]">98% Confidence</Badge>
                                            </div>
                                            <p className="text-xs text-blue-700 leading-relaxed italic">
                                                "Severity score of 9 is driven by potential for complete system downtime at customer sites. Occurrence is rare but detection is currently low (3) which justifies formal CAPA initiation."
                                            </p>
                                        </div>

                                        {/* Threshold Reference */}
                                        <div className="p-4 bg-amber-50/50 border border-amber-200 rounded-xl space-y-2">
                                            <p className="text-xs font-bold text-amber-800 uppercase">Threshold Reference</p>
                                            <p className="text-xs text-amber-700 leading-relaxed">
                                                <strong>Why this is HIGH:</strong> Risk score of 85/100 exceeds the critical threshold of 80. Scores above 80 require immediate CAPA initiation due to high severity (9/10) and low detection capability (3/10), indicating significant potential impact with limited early warning systems.
                                            </p>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="p-3 border rounded-xl bg-white shadow-sm">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">FMEA Mapping</p>
                                                <p className="text-xs font-semibold">FMEA-2024-H-102</p>
                                            </div>
                                            <div className="p-3 border rounded-xl bg-white shadow-sm">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Regulatory Impact</p>
                                                <div className="flex gap-1">
                                                    <Badge className="bg-red-100 text-red-600 border-none text-[8px]">MDR</Badge>
                                                    <Badge className="bg-red-100 text-red-600 border-none text-[8px]">FDA</Badge>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <div className="space-y-6">
                                <Card className="border-slate-200">
                                    <CardHeader className="py-4">
                                        <CardTitle className="text-sm uppercase font-bold tracking-widest text-slate-400">Risk Matrix Visualization</CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-6 flex items-center justify-center min-h-[300px] bg-slate-50 rounded-b-xl">
                                        <div className="grid grid-cols-5 gap-1 w-full max-w-[250px] aspect-square">
                                            {Array.from({ length: 25 }).map((_, i) => {
                                                const row = Math.floor(i / 5);
                                                const col = i % 5;
                                                const isHot = row < 2 && col > 2;
                                                return (
                                                    <div
                                                        key={i}
                                                        className={`rounded-sm flex items-center justify-center ${isHot ? 'bg-red-500/80 animate-pulse' :
                                                            (row < 3 && col > 1) ? 'bg-amber-400/60' : 'bg-green-400/40'
                                                            }`}
                                                    >
                                                        {row === 0 && col === 4 && <Circle className="h-3 w-3 fill-white text-white" />}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </CardContent>
                                </Card>

                                <div className="flex gap-4">
                                    <Button
                                        className="flex-1 gradient-primary text-white h-12 shadow-lg shadow-primary/25"
                                        onClick={() => setStageIndex(visibleStages.findIndex(s => s.id === "CAPA_INTAKE"))}
                                        disabled={getAccessLevel("RISK_SCORE_ANALYSIS", "CAPA_INTAKE_BUTTON") !== "FULL"}
                                    >
                                        CAPA Intake
                                    </Button>
                                    <Button
                                        variant="destructive"
                                        className="flex-1 h-12 shadow-lg shadow-destructive/25"
                                        onClick={() => setShowRejectModal(!showRejectModal)}
                                        disabled={getAccessLevel("RISK_SCORE_ANALYSIS", "CAPA_REJECT_BUTTON") !== "FULL"}
                                    >
                                        {showRejectModal ? "Hide Rejection Form" : "Reject CAPA"}
                                    </Button>
                                </div>

                                {/* Rejection Modal/Section */}
                                {showRejectModal && (
                                    <Card className="border-red-200 bg-red-50/30">
                                        <CardHeader className="py-4 bg-red-50">
                                            <CardTitle className="text-lg text-red-700">CAPA Rejection</CardTitle>
                                        </CardHeader>
                                        <CardContent className="pt-6 space-y-4">
                                            {/* Risk Score Analysis Report */}
                                            <div className="p-4 bg-white rounded-lg border border-slate-200">
                                                <h4 className="text-sm font-bold text-slate-700 mb-3">Risk Score Analysis Report</h4>
                                                <div className="space-y-2 text-xs text-slate-600">
                                                    <p><strong>Risk Score:</strong> 85/100 (CRITICAL)</p>
                                                    <p><strong>Severity:</strong> 9 - Potential for complete system downtime</p>
                                                    <p><strong>Occurrence:</strong> 7 - Rare but documented incidents</p>
                                                    <p><strong>Detection:</strong> 3 - Low detection capability</p>
                                                    <p><strong>FMEA Reference:</strong> FMEA-2024-H-102</p>
                                                    <p><strong>Regulatory Impact:</strong> MDR, FDA</p>
                                                    <p className="pt-2 italic">"Severity score of 9 is driven by potential for complete system downtime at customer sites. Occurrence is rare but detection is currently low (3) which justifies formal CAPA initiation."</p>
                                                </div>
                                            </div>

                                            {/* Download Report Button */}
                                            <Button variant="outline" className="w-full gap-2">
                                                <Download className="h-4 w-4" /> Download Risk Score Report
                                            </Button>

                                            {/* Mandatory Reviewer Comment */}
                                            <div className="space-y-2">
                                                <label className="text-sm font-bold text-slate-700">
                                                    Reviewer Comment <span className="text-red-600">*</span>
                                                </label>
                                                <textarea
                                                    className="w-full min-h-[100px] p-3 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none"
                                                    placeholder="Enter mandatory rejection reason and comments..."
                                                    value={reviewerComment}
                                                    onChange={(e) => setReviewerComment(e.target.value)}
                                                />
                                            </div>

                                            {/* Submit Rejection Button */}
                                            <Button
                                                variant="destructive"
                                                className="w-full"
                                                disabled={!reviewerComment.trim()}
                                                onClick={() => {
                                                    if (reviewerComment.trim()) {
                                                        alert("CAPA Rejected with comment: " + reviewerComment);
                                                        setShowRejectModal(false);
                                                        setReviewerComment("");
                                                    }
                                                }}
                                            >
                                                Submit Rejection
                                            </Button>
                                        </CardContent>
                                    </Card>
                                )}
                            </div>
                        </div>
                    </div>
                );
            case "CAPA_INTAKE":
                const intakeAccess = getAccessLevel("CAPA_INTAKE");
                if (intakeAccess === "HIDDEN") return null;
                const isIntakeReadOnly = intakeAccess === "READ_ONLY";

                return (
                    <div className="space-y-6">
                        {/* Header with Auto-Generated CAPA ID and Target Date */}
                        <div className="flex justify-between items-center bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 shadow-sm">
                            <div>
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Auto-Generated CAPA ID</p>
                                <p className="text-2xl font-bold text-primary">CAPA-2024-8892</p>
                                <div className="flex items-center gap-2 mt-2">
                                    <Badge className="bg-green-500 text-white text-[9px]">Read-Only</Badge>
                                    <Badge className="bg-indigo-500 text-white text-[9px] flex items-center gap-1.5 border-none">
                                        <Bot className="h-3 w-3" />
                                        AI Assistant (Intake Form)
                                    </Badge>
                                </div>
                            </div>
                            <div className="flex items-end gap-4">
                                <div className="text-right">
                                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2">Target Completion Date *</label>
                                    <Input
                                        type="date"
                                        value={intakeFormData.targetDate}
                                        onChange={(e) => handleIntakeChange("targetDate", e.target.value)}
                                        className="w-48 text-sm font-semibold"
                                        disabled={isIntakeReadOnly}
                                    />
                                </div>
                                <Button
                                    variant="outline"
                                    className="h-10 gap-2 bg-white hover:bg-blue-50 border-blue-300"
                                    onClick={handleAutofillIntake}
                                    disabled={isIntakeReadOnly}
                                >
                                    <Download className="h-4 w-4" />
                                    Autofill from Complaint
                                </Button>
                            </div>
                        </div>

                        {/* Autofill Info Banner */}
                        <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <Info className="h-4 w-4 text-blue-600" />
                            <p className="text-xs text-blue-700">
                                <strong>Autofill Available:</strong> Click "Autofill from Complaint" to automatically populate form fields with data from Complaint ID: CP-9902 and NC ID: NC-2024-001
                            </p>
                        </div>

                        {/* Main Form Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                            {/* Sub-division 1: Problem Identification */}
                            <Card className="border-blue-200 shadow-md">
                                <CardHeader className="bg-blue-50/50 py-4">
                                    <CardTitle className="text-sm font-bold uppercase text-blue-700 flex items-center gap-2">
                                        <div className="h-2 w-2 rounded-full bg-blue-600" />
                                        Sub-division 1: Problem Identification
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="pt-6 space-y-4">
                                    <div>
                                        <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                            Cause of Issue (Preliminary) *
                                        </label>
                                        <textarea
                                            className="w-full min-h-[80px] p-3 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                            value={intakeFormData.causeOfIssue}
                                            onChange={(e) => handleIntakeChange("causeOfIssue", e.target.value)}
                                            placeholder="Describe the preliminary cause of the issue..."
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                                Date & Time Registered
                                            </label>
                                            <Input
                                                type="datetime-local"
                                                value={intakeFormData.dateRegistered}
                                                onChange={(e) => handleIntakeChange("dateRegistered", e.target.value)}
                                                className="text-xs"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                                Registered By
                                            </label>
                                            <Input
                                                type="text"
                                                value={intakeFormData.registeredBy}
                                                onChange={(e) => handleIntakeChange("registeredBy", e.target.value)}
                                                className="text-xs"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                            Document Details from Complaint
                                        </label>
                                        <Input
                                            type="text"
                                            value={intakeFormData.documentDetails}
                                            onChange={(e) => handleIntakeChange("documentDetails", e.target.value)}
                                            className="text-xs"
                                        />
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Sub-division 2: Problem Description */}
                            <Card className="border-orange-200 shadow-md">
                                <CardHeader className="bg-orange-50/50 py-4">
                                    <CardTitle className="text-sm font-bold uppercase text-orange-700 flex items-center gap-2">
                                        <div className="h-2 w-2 rounded-full bg-orange-600" />
                                        Sub-division 2: Problem Description
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="pt-6 space-y-4">
                                    <div>
                                        <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                            Detailed Description of Complaint *
                                        </label>
                                        <textarea
                                            className="w-full min-h-[80px] p-3 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                            value={intakeFormData.detailedDescription}
                                            onChange={(e) => handleIntakeChange("detailedDescription", e.target.value)}
                                            placeholder="Provide detailed description of the complaint..."
                                        />
                                    </div>

                                    <div>
                                        <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                            Who Registered the Complaint
                                        </label>
                                        <Input
                                            type="text"
                                            value={intakeFormData.whoRegistered}
                                            onChange={(e) => handleIntakeChange("whoRegistered", e.target.value)}
                                            className="text-xs"
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                                Category
                                            </label>
                                            <select
                                                className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-orange-500 outline-none"
                                                value={intakeFormData.category}
                                                onChange={(e) => handleIntakeChange("category", e.target.value)}
                                            >
                                                <option value="" disabled>Select Category...</option>
                                                <option>Hardware Failure</option>
                                                <option>Software Issue</option>
                                                <option>Safety Concern</option>
                                                <option>Quality Issue</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                                When Recorded
                                            </label>
                                            <Input
                                                type="date"
                                                value={intakeFormData.whenRecorded}
                                                onChange={(e) => handleIntakeChange("whenRecorded", e.target.value)}
                                                className="text-xs"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                            Where Recorded (Location)
                                        </label>
                                        <Input
                                            type="text"
                                            value={intakeFormData.whereRecorded}
                                            onChange={(e) => handleIntakeChange("whereRecorded", e.target.value)}
                                            className="text-xs"
                                        />
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Sub-division 3: Risk Assessment */}
                            <Card className="border-red-200 shadow-md">
                                <CardHeader className="bg-red-50/50 py-4">
                                    <CardTitle className="text-sm font-bold uppercase text-red-700 flex items-center gap-2">
                                        <div className="h-2 w-2 rounded-full bg-red-600" />
                                        Sub-division 3: Risk Assessment
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="pt-6 space-y-4">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                                Severity *
                                            </label>
                                            <select
                                                className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-red-500 outline-none"
                                                value={intakeFormData.severity}
                                                onChange={(e) => handleIntakeChange("severity", e.target.value)}
                                            >
                                                <option value="" disabled>Select...</option>
                                                <option value="9">High (9)</option>
                                                <option value="7">Medium (7)</option>
                                                <option value="5">Medium (5)</option>
                                                <option value="3">Low (3)</option>
                                                <option value="1">Very Low (1)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                                Occurrence *
                                            </label>
                                            <select
                                                className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-red-500 outline-none"
                                                value={intakeFormData.occurrence}
                                                onChange={(e) => handleIntakeChange("occurrence", e.target.value)}
                                            >
                                                <option value="" disabled>Select...</option>
                                                <option value="7">Frequent (7)</option>
                                                <option value="5">Occasional (5)</option>
                                                <option value="3">Rare (3)</option>
                                                <option value="2">Very Rare (2)</option>
                                                <option value="1">Remote (1)</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                                Detection *
                                            </label>
                                            <select
                                                className="w-full p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-red-500 outline-none"
                                                value={intakeFormData.detection}
                                                onChange={(e) => handleIntakeChange("detection", e.target.value)}
                                            >
                                                <option value="" disabled>Select...</option>
                                                <option value="1">High (1)</option>
                                                <option value="3">Medium (3)</option>
                                                <option value="5">Low (5)</option>
                                                <option value="7">Very Low (7)</option>
                                                <option value="9">Almost Impossible (9)</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                                        <p className="text-[10px] font-bold text-red-700 uppercase mb-2">Risk Score Details</p>
                                        <div className="text-xs text-red-600 space-y-1">
                                            <p><strong>Severity:</strong> Potential for complete system downtime</p>
                                            <p><strong>Occurrence:</strong> Rare but documented incidents</p>
                                            <p><strong>Detection:</strong> High detection capability with current controls</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Sub-division 4: Regulatory Linkage */}
                            <Card className="border-indigo-200 shadow-md">
                                <CardHeader className="bg-indigo-50/50 py-4">
                                    <CardTitle className="text-sm font-bold uppercase text-indigo-700 flex items-center gap-2">
                                        <div className="h-2 w-2 rounded-full bg-indigo-600" />
                                        Sub-division 4: Regulatory Linkage
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="pt-6 space-y-4">
                                    <div>
                                        <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                            Regulatory Industry Linkage *
                                        </label>
                                        <textarea
                                            className="w-full min-h-[100px] p-3 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                            value={intakeFormData.regulatoryLinkage}
                                            onChange={(e) => handleIntakeChange("regulatoryLinkage", e.target.value)}
                                            placeholder="Describe regulatory linkage with complaint details..."
                                        />
                                    </div>

                                    <div className="p-3 bg-white rounded-lg border border-indigo-200 flex justify-between items-center">
                                        <span className="text-xs text-slate-600">Reference: MD-2024-REG-012</span>
                                        <Badge className="bg-green-500 text-white text-[9px]">Validated by AI</Badge>
                                    </div>

                                    <div>
                                        <label className="text-[10px] font-bold text-slate-600 uppercase block mb-2">
                                            Linked SOP/Policy References
                                        </label>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2 p-2 bg-slate-50 rounded border border-slate-200">
                                                <Paperclip className="h-3 w-3 text-slate-400" />
                                                <span className="text-xs text-slate-600">SOP-QM-001 (CAPA Management)</span>
                                            </div>
                                            <div className="flex items-center gap-2 p-2 bg-slate-50 rounded border border-slate-200">
                                                <Paperclip className="h-3 w-3 text-slate-400" />
                                                <span className="text-xs text-slate-600">SOP-EN-042 (Material Verification)</span>
                                            </div>
                                            <Button variant="outline" size="sm" className="w-full text-xs">
                                                + Add SOP Reference
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        <div className="flex gap-4 pt-6 border-t border-slate-200">
                            <Button
                                className="flex-1 gradient-primary text-white h-12 shadow-lg text-base font-semibold"
                                onClick={handleMoveToRCA}
                                disabled={isIntakeReadOnly}
                            >
                                Submit CAPA - Move to RCA
                            </Button>
                            <Button variant="outline" className="flex-1 h-12 text-base" disabled={isIntakeReadOnly}>
                                Save as Draft
                            </Button>
                        </div>
                    </div>
                );
            case "INVESTIGATION_RCA":
                const rcaAccess = getAccessLevel("INVESTIGATION_RCA");
                if (rcaAccess === "HIDDEN") return null;
                const isRcaReadOnly = rcaAccess === "READ_ONLY";

                return (
                    <div className="space-y-8 animate-in fade-in duration-500">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <Card className="md:col-span-2 border-slate-200 shadow-xl overflow-hidden flex flex-col min-h-[600px]">
                                <CardHeader className="bg-slate-900 text-white flex-row justify-between items-center py-4">
                                    <div>
                                        <CardTitle className="text-lg">RCA Analysis Output</CardTitle>
                                        <CardDescription className="text-white/60 text-[10px] uppercase font-bold">Comprehensive Root Cause Investigation</CardDescription>
                                    </div>
                                    <div className="flex gap-2">
                                        <Badge
                                            variant="outline"
                                            className={`cursor-pointer transition-all duration-300 hover:scale-105 ${rcaMethodology === "5-Why" ? "bg-blue-600 border-blue-400 text-white" : "text-white/40 border-white/10 hover:border-white/30"}`}
                                            onClick={() => setRcaMethodology("5-Why")}
                                        >
                                            5-Why Methodology
                                        </Badge>
                                        <Badge
                                            variant="outline"
                                            className={`cursor-pointer transition-all duration-300 hover:scale-105 ${rcaMethodology === "Fishbone" ? "bg-orange-600 border-orange-400 text-white" : "text-white/40 border-white/10 hover:border-white/30"}`}
                                            onClick={() => setRcaMethodology("Fishbone")}
                                        >
                                            Fishbone Analysis
                                        </Badge>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-0 bg-white flex-1 relative">
                                    {isGeneratingRCA && (
                                        <div className="absolute inset-0 bg-white/90 backdrop-blur-sm z-10 flex flex-col items-center justify-center animate-in fade-in duration-300">
                                            <div className="w-16 h-16 relative">
                                                <div className="w-16 h-16 border-4 border-slate-100 rounded-full"></div>
                                                <div className="w-16 h-16 border-4 border-slate-900 rounded-full animate-spin border-t-transparent absolute top-0 left-0"></div>
                                            </div>
                                            <p className="mt-6 text-sm font-bold text-slate-900 tracking-widest uppercase animate-pulse">AI Agent: Regenerating RCA...</p>
                                        </div>
                                    )}

                                    <div className="p-8 space-y-8">
                                        {/* Orchestration Agents Status Bar */}
                                        <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex flex-col gap-3">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Orchestration Agents In-Use</p>
                                            <div className="flex flex-wrap gap-2">
                                                {(rcaMethodology === "5-Why"
                                                    ? ["Question Agent", "Answer/List Agent", "Validate Agent", "Ranking Agent", "Validator Ranking", "Loop Control", "Guardrails", "Zero Evidence Mode"]
                                                    : ["List of Causes", "Categorize Agent", "Validator Agent", "Ranking Agent", "Validator Ranking", "Zero Evidence", "Guardrails"]
                                                ).map((agent, i) => (
                                                    <Badge key={i} variant="outline" className="bg-white border-slate-200 text-indigo-500 text-[8px] font-bold py-0 h-5 px-2">
                                                        {agent}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Complaint Details Summary */}
                                        <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 shadow-inner">
                                            <div className="flex items-center gap-2 mb-3">
                                                <Info className="h-4 w-4 text-slate-400" />
                                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Details of the Complaint</span>
                                            </div>
                                            <p className="text-sm text-slate-700 leading-relaxed font-medium">
                                                Unexpected noise and vibration occurring after 200 cycles of operation in Module B analyzers. Initial assessment points to material fatigue in the sensor housing components reported from Customer Site 4.
                                            </p>
                                        </div>

                                        {/* Methodology Justification */}
                                        <div className="p-5 bg-indigo-50/50 rounded-2xl border border-indigo-100">
                                            <p className="text-[10px] font-bold uppercase text-indigo-400 mb-4 ml-1 tracking-widest">RCA Method Justification</p>
                                            <div className="flex gap-5">
                                                <div className="h-12 w-12 shrink-0 rounded-2xl bg-indigo-100 flex items-center justify-center shadow-sm">
                                                    <Search className="h-6 w-6 text-indigo-600" />
                                                </div>
                                                <div>
                                                    <p className="text-sm text-slate-700 leading-relaxed italic">
                                                        "{rcaMethodology === "5-Why"
                                                            ? "5-Why was selected to trace the linear causal chain of the physical failure, identifying the systemic design gate bypass."
                                                            : "Fishbone analysis was selected to evaluate the multidimensional factors including Material, Machine, and Method involved in the vibration issue."}"
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Methodology Result */}
                                        <div className="space-y-6">
                                            <p className="text-[10px] font-bold uppercase text-slate-400 mb-4 ml-1 tracking-widest">Result of the {rcaMethodology} Methodology</p>
                                            {rcaMethodology === "5-Why" ? (
                                                <div className="space-y-5 px-4">
                                                    {[
                                                        { q: "Why did the analyzer make noise?", a: "The internal cooling fan was vibrating wildly." },
                                                        { q: "Why was the fan vibrating?", a: "The mounting bracket had cracked under stress." },
                                                        { q: "Why did the bracket crack?", a: "The material thickness was insufficient for the RPM load." },
                                                        { q: "Why was the thickness insufficient?", a: "Design revision v2.1 optimized for weight without re-testing load." },
                                                        { q: "Why was load testing skipped?", a: "Root Cause: Quality gate for 'minor' material changes was bypassable." }
                                                    ].map((item, i) => (
                                                        <div key={i} className="flex gap-6 group">
                                                            <div className="flex flex-col items-center">
                                                                <div className="h-8 w-8 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px] font-bold z-10 shadow-lg group-hover:scale-110 transition-transform tracking-tighter">{i + 1}</div>
                                                                {i < 4 && <div className="w-0.5 flex-1 bg-slate-200 my-1" />}
                                                            </div>
                                                            <div className="flex-1 pb-4">
                                                                <p className="text-[10px] font-bold text-primary mb-1 uppercase tracking-wider opacity-60 group-hover:opacity-100 transition-opacity">{item.q}</p>
                                                                <p className="text-sm text-slate-700 bg-white p-4 rounded-xl border border-slate-100 shadow-sm group-hover:border-primary/20 group-hover:shadow-md transition-all">{item.a}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <div className="grid grid-cols-2 gap-4">
                                                    {[
                                                        { cat: "Material", val: "Substandard alloy thickness (0.8mm vs 1.2mm) in v2.1 sensor housing components.", icon: <ClipboardList className="h-4 w-4" /> },
                                                        { cat: "Machine", val: "High-frequency resonance at 4500 RPM exceeds simulated tolerances for lightweight brackets.", icon: <AlertCircle className="h-4 w-4" /> },
                                                        { cat: "Method", val: "Design review bypass implemented for 'minor' hardware revisions in PLM system.", icon: <FileSearch className="h-4 w-4" /> },
                                                        { cat: "Personnel", val: "Lack of specific training for material fatigue testing in the rapid revision team.", icon: <Users className="h-4 w-4" /> }
                                                    ].map((item, i) => (
                                                        <div key={i} className="p-5 bg-slate-50 border border-slate-100 rounded-2xl hover:bg-white hover:shadow-md transition-all cursor-default group">
                                                            <div className="flex items-center gap-2 mb-3">
                                                                <div className="p-2 bg-white rounded-lg text-slate-400 group-hover:text-primary transition-colors">
                                                                    {item.icon}
                                                                </div>
                                                                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{item.cat}</p>
                                                            </div>
                                                            <p className="text-xs text-slate-700 leading-relaxed font-medium">{item.val}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                                <CardFooter className="bg-slate-50 border-t py-6 px-8 flex justify-between items-center mt-auto">
                                    <div className="flex gap-4">
                                        <Button
                                            className="h-10 gap-2 bg-white hover:bg-slate-50 text-xs shadow-sm px-5 border-slate-200"
                                            onClick={handleRegenerateRCA}
                                            disabled={isGeneratingRCA || isRcaReadOnly}
                                        >
                                            <RefreshCw className={`h-4 w-4 ${isGeneratingRCA ? 'animate-spin' : ''}`} />
                                            Regenerate RCA
                                        </Button>
                                    </div>
                                    <div className="flex gap-3">
                                        <Button
                                            className="h-10 gradient-primary text-white border-none shadow-lg px-8 text-xs font-bold uppercase tracking-widest hover:scale-105 transition-transform"
                                            onClick={handleGenerateActionPlan}
                                            disabled={isRcaReadOnly}
                                        >
                                            Generate Action Plan
                                        </Button>
                                    </div>
                                </CardFooter>
                            </Card>

                            <div className="space-y-6">
                                <Card className="border-slate-200 shadow-sm">
                                    <CardHeader className="py-4">
                                        <CardTitle className="text-xs font-bold uppercase text-slate-400">Cause Identification</CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-6 space-y-6">
                                        <div className="space-y-4">
                                            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl group hover:border-red-200 transition-colors">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Identified Cause (Initial)</p>
                                                <div className="flex items-start gap-3">
                                                    <div className="p-2 bg-white rounded-lg border border-slate-100 shadow-sm text-red-500">
                                                        <AlertCircle className="h-4 w-4" />
                                                    </div>
                                                    <p className="text-sm font-bold text-slate-700">Inadequate Material Specifications</p>
                                                </div>
                                            </div>

                                            <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-2xl group hover:border-blue-200 transition-colors shadow-inner">
                                                <p className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-2">Actual Verified Cause (AI)</p>
                                                <div className="flex items-start gap-3">
                                                    <div className="p-2 bg-white rounded-lg border border-blue-50 shadow-sm text-blue-600">
                                                        <CheckCircle2 className="h-4 w-4" />
                                                    </div>
                                                    <p className="text-sm font-medium text-slate-700 leading-relaxed italic">Systemic failure in design review process for minor hardware revisions.</p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-3">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-1">Linked Evidence</p>
                                            <div className="space-y-2">
                                                {['Design_Spec_v2.1.pdf', 'Load_Test_Report_Q1.xlsx'].map((file, i) => (
                                                    <div key={i} className="flex items-center justify-between p-3 bg-white border border-slate-100 rounded-xl hover:border-primary/20 hover:shadow-sm transition-all cursor-pointer group">
                                                        <div className="flex items-center gap-3">
                                                            <FileText className="h-4 w-4 text-slate-400 group-hover:text-primary" />
                                                            <span className="text-xs font-medium text-slate-600">{file}</span>
                                                        </div>
                                                        <Eye className="h-3 w-3 text-slate-300 group-hover:text-primary" />
                                                    </div>
                                                ))}
                                            </div>
                                            <Button variant="outline" className="w-full text-[10px] h-10 border-dashed border-slate-300 bg-slate-50/50 hover:bg-white hover:border-slate-400 text-slate-500 uppercase font-bold tracking-widest">
                                                <Paperclip className="h-3 w-3 mr-2" /> Attach Evidence
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card className="border-slate-200 shadow-xl overflow-hidden rounded-3xl bg-white">
                                    <div className="bg-slate-900 border-b border-white/5 py-4 px-6">
                                        <CardTitle className="text-[10px] font-bold uppercase text-white/40 tracking-[0.2em]">Review Governance</CardTitle>
                                    </div>
                                    <CardContent className="p-6 space-y-6">
                                        <div className="flex items-center justify-between">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">RCA Approval Status</p>
                                            <Badge variant="outline" className="text-amber-600 bg-amber-50 border-amber-200 text-[10px] px-3 font-bold">Pending Review</Badge>
                                        </div>

                                        <div className="space-y-3">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Reviewer Feedback</p>
                                            <div className="p-5 bg-slate-50 border border-slate-100 rounded-2xl relative">
                                                <div className="absolute -top-3 left-4 px-2 bg-white border border-slate-100 rounded-full flex items-center gap-1.5 shadow-sm">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                                                    <span className="text-[9px] font-bold uppercase text-slate-500">Quality Manager</span>
                                                </div>
                                                <p className="text-xs text-slate-600 leading-relaxed italic font-medium">
                                                    "The tracing of the design review bypass is critical. Ensure the action plan covers the PLM system modification to prevent future bypasses."
                                                </p>
                                            </div>
                                        </div>

                                        {getAccessLevel("INVESTIGATION_RCA", "APPROVE_BUTTON") === "FULL" && (
                                            <div className="grid grid-cols-2 gap-3 pt-2">
                                                <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white text-[10px] font-bold h-10 uppercase tracking-wider shadow-lg shadow-green-900/10">Approve RCA</Button>
                                                <Button size="sm" variant="outline" className="text-[10px] font-bold h-10 uppercase tracking-wider border-slate-200">Request Revision</Button>
                                            </div>
                                        )}
                                    </CardContent>
                                    <CardFooter className="py-4 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between px-6">
                                        <div className="flex items-center gap-2">
                                            <div className="w-6 h-6 rounded-full bg-slate-900 flex items-center justify-center">
                                                <History className="h-3 w-3 text-white" />
                                            </div>
                                            <span className="text-[10px] font-bold text-slate-900 uppercase tracking-widest">Audit Trail</span>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-7 text-[9px] uppercase font-bold text-primary hover:bg-white hover:shadow-sm px-4 rounded-full border border-transparent hover:border-slate-100"
                                            onClick={() => setShowAuditTrailModal(true)}
                                        >
                                            View Full Trace
                                        </Button>
                                    </CardFooter>
                                </Card>
                            </div>
                        </div>
                    </div >
                );
            case "ACTION_PLAN_GENERATION":
                const genAccess = getAccessLevel("ACTION_PLAN_GENERATION");
                if (genAccess === "HIDDEN") return null;
                const isGenReadOnly = genAccess === "READ_ONLY";

                return (
                    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
                        <div className="flex justify-between items-center mb-6">
                            <div className="flex items-center gap-3">
                                <div>
                                    <h4 className="text-xl font-bold text-slate-900 tracking-tight">AI Generated Action Plans</h4>
                                    <div className="flex items-center gap-2 mt-1">
                                        <Badge variant="outline" className="bg-slate-100 text-slate-500 border-slate-200 uppercase text-[9px] font-bold tracking-widest px-2">Ready for Verification</Badge>
                                        <Badge className="bg-indigo-500 text-white text-[9px] flex items-center gap-1.5 border-none">
                                            <Bot className="h-3 w-3" />
                                            Action Planner Agent
                                        </Badge>
                                        <span className="text-[10px] text-slate-400 font-medium">Drafted based on Verified Root Cause</span>
                                    </div>
                                </div>
                            </div>
                            <Button variant="outline" size="sm" className="gap-2 bg-white border-slate-200 shadow-sm" onClick={handleRejectActionPlan} disabled={isGenReadOnly}>
                                <RefreshCw className="h-4 w-4" /> Regenerated All
                            </Button>
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            {[
                                {
                                    capaId: "CAPA-2024-8892",
                                    id: "AP-001",
                                    type: "Corrective",
                                    owner: "Design Engineering",
                                    ownerName: "Sarah Jenkins / Principal Engineer",
                                    method: "Design Review / Physical Stress Test",
                                    desc: "Update cooling fan bracket material specifications to Grade 5 Titanium to withstand high-frequency resonance at 4500 RPM.",
                                    status: "Pending",
                                    evidence: null
                                },
                                {
                                    capaId: "CAPA-2024-8892",
                                    id: "AP-002",
                                    type: "Preventive",
                                    owner: "Manufacturing QA",
                                    ownerName: "Michael Chen / Quality Assurance Lead",
                                    method: "Automated PLM Gate Audit",
                                    desc: "Modify PLM system to prevent 'minor' revision labeling for any component change involving structural material density.",
                                    status: "Pending",
                                    evidence: null
                                }
                            ].map((plan, i) => (
                                <Card key={i} className="border-slate-200 shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden flex flex-col rounded-2xl group">
                                    <div className="bg-slate-900 px-6 py-4 flex justify-between items-center text-white">
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg ${plan.type === 'Corrective' ? 'bg-orange-500' : 'bg-blue-500'} shadow-lg`}>
                                                <ClipboardList className="h-4 w-4 text-white" />
                                            </div>
                                            <div>
                                                <p className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] leading-none mb-1">Action Plan</p>
                                                <p className="text-sm font-bold tracking-tight">{plan.id}</p>
                                            </div>
                                        </div>
                                        <Badge className={`${plan.status === 'Pending' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-green-500/10 text-green-500 border-green-500/20'} text-[10px] font-bold px-3`}>
                                            {plan.status}
                                        </Badge>
                                    </div>

                                    <CardContent className="p-8 space-y-6 flex-1 bg-white">
                                        <div className="grid grid-cols-2 gap-6">
                                            <div className="space-y-1">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Linked CAPA ID</p>
                                                <p className="text-xs font-bold text-slate-900">{plan.capaId}</p>
                                            </div>
                                            <div className="space-y-1">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Action Type</p>
                                                <Badge variant="outline" className={`${plan.type === 'Corrective' ? 'border-orange-200 text-orange-600 bg-orange-50' : 'border-blue-200 text-blue-600 bg-blue-50'} text-[10px] px-2`}>
                                                    {plan.type} Action
                                                </Badge>
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Proposed Action Plan</p>
                                            <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl">
                                                <p className="text-sm text-slate-700 leading-relaxed font-medium">
                                                    {plan.desc}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Action Owner / Designation</p>
                                                <div className="flex items-center gap-3">
                                                    <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200">
                                                        <Users className="h-4 w-4 text-slate-400" />
                                                    </div>
                                                    <p className="text-xs font-bold text-slate-700 leading-tight">{plan.ownerName}</p>
                                                </div>
                                            </div>
                                            <div className="space-y-2">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Verification Method</p>
                                                <div className="p-3 bg-indigo-50/50 border border-indigo-100/50 rounded-xl">
                                                    <p className="text-[11px] text-indigo-700 font-medium italic">{plan.method}</p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-2 pt-2 border-t border-slate-100">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Evidence Submission</p>
                                            <Button variant="outline" className="w-full h-12 border-dashed border-slate-300 bg-slate-50 hover:bg-white hover:border-primary/40 text-slate-500 hover:text-primary transition-all rounded-2xl flex items-center justify-between px-5">
                                                <div className="flex items-center gap-3">
                                                    <Paperclip className="h-4 w-4" />
                                                    <span className="text-xs font-bold uppercase tracking-widest">Upload Execution Evidence</span>
                                                </div>
                                                <Badge variant="outline" className="text-[9px] font-bold opacity-60 border-slate-200">PDF/JPG/XLSX</Badge>
                                            </Button>
                                        </div>
                                    </CardContent>

                                    <CardFooter className="bg-slate-50 border-t py-4 px-6 flex justify-between items-center gap-4">
                                        <p className="text-[9px] font-bold text-slate-400 italic">Created by AI Agent at {new Date().toLocaleTimeString()}</p>
                                        <div className="flex gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="h-9 px-4 text-red-600 border-red-200 hover:bg-red-50 text-[10px] font-bold uppercase tracking-wider"
                                                onClick={handleRejectActionPlan}
                                                disabled={isGenReadOnly}
                                            >
                                                Reject & Regenerate
                                            </Button>
                                            <Button
                                                size="sm"
                                                className="h-9 px-6 gradient-primary text-white text-[10px] font-bold uppercase tracking-wider shadow-lg shadow-primary/20"
                                                onClick={nextStage}
                                                disabled={isGenReadOnly}
                                            >
                                                Approve Action
                                            </Button>
                                        </div>
                                    </CardFooter>
                                </Card>
                            ))}
                        </div>

                        <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-100 flex items-center justify-between shadow-inner">
                            <div className="flex gap-3 items-center">
                                <div className="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-black italic">AI</div>
                                <div>
                                    <p className="text-xs font-bold text-indigo-900">Agent Recommendation</p>
                                    <p className="text-[10px] text-indigo-700">Add an effectiveness monitoring check after 30 days of implementation.</p>
                                </div>
                            </div>
                            <Button
                                size="sm"
                                className="bg-indigo-600 hover:bg-indigo-700 text-white text-[10px]"
                                onClick={() => setStageIndex(visibleStages.findIndex(s => s.id === "ACTION_PLAN_IMPLEMENTATION"))}
                                disabled={isGenReadOnly}
                            >
                                Accept Add & Proceed
                            </Button>
                        </div>
                    </div>
                );
            case "ACTION_PLAN_IMPLEMENTATION":
                const implAccess = getAccessLevel("ACTION_PLAN_IMPLEMENTATION");
                if (implAccess === "HIDDEN") return null;
                const isImplReadOnly = implAccess === "READ_ONLY";

                return (
                    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
                        <div className="flex justify-between items-center mb-6">
                            <div>
                                <h4 className="text-xl font-bold text-slate-900 tracking-tight">Implementation & Tracking</h4>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge className="bg-blue-600 uppercase text-[9px] font-bold tracking-widest px-2">Execution Phase</Badge>
                                    <span className="text-[10px] text-slate-400 font-medium">Monitoring Action Plan Lifecycle & Evidence Validation</span>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <Button variant="outline" size="sm" className="bg-white border-slate-200" disabled={isImplReadOnly}>
                                    <Download className="h-4 w-4 mr-2" /> Export Report
                                </Button>
                                <Button
                                    className="gradient-primary text-white border-none shadow-lg px-6 text-xs font-bold uppercase tracking-widest"
                                    onClick={() => setStageIndex(visibleStages.findIndex(s => s.id === "ACTION_PLAN_EFFECTIVENESS"))}
                                    disabled={isImplReadOnly}
                                >
                                    Proceed to Effectiveness
                                </Button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            {[
                                {
                                    capaId: "CAPA-2024-8892",
                                    id: "AP-001",
                                    type: "Corrective",
                                    owner: "Design Engineering",
                                    ownerName: "Sarah Jenkins / Principal Engineer",
                                    method: "Design Review / Physical Stress Test",
                                    desc: "Update cooling fan bracket material specifications to Grade 5 Titanium to withstand high-frequency resonance.",
                                    status: "Completed",
                                    evidence: "MatCert_REV_Final.pdf",
                                    reviewStatus: "Accepted",
                                    reviewedBy: "Robert Ford (Quality Director)",
                                    reviewDate: "Feb 11, 2026",
                                    rework: false
                                },
                                {
                                    capaId: "CAPA-2024-8892",
                                    id: "AP-002",
                                    type: "Preventive",
                                    owner: "Manufacturing QA",
                                    ownerName: "Michael Chen / Quality Assurance Lead",
                                    method: "Automated PLM Gate Audit",
                                    desc: "Modify PLM system to prevent 'minor' revision labeling for any component change involving structural material density.",
                                    status: "Pending",
                                    evidence: "System_Log_Export.xlsx",
                                    reviewStatus: "Rejected",
                                    reviewedBy: "Sarah Jenkins (Reviewer)",
                                    reviewDate: "Feb 10, 2026",
                                    rework: true
                                }
                            ].map((plan, i) => (
                                <Card key={i} className="border-slate-200 shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden flex flex-col rounded-3xl group bg-white">
                                    {/* Header Section */}
                                    <div className="bg-slate-900 px-8 py-5 flex justify-between items-center text-white">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-2.5 rounded-xl ${plan.type === 'Corrective' ? 'bg-orange-500' : 'bg-blue-500'} shadow-lg shadow-black/20`}>
                                                <History className="h-5 w-5 text-white" />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2 mb-1">
                                                    <p className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] leading-none">Plan Tracking</p>
                                                    {plan.rework && (
                                                        <Badge className="bg-red-500 text-white border-none text-[8px] h-4 px-1.5 animate-pulse">REWORK REQUIRED</Badge>
                                                    )}
                                                </div>
                                                <p className="text-base font-bold tracking-tight">{plan.id}</p>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end gap-1">
                                            <Badge className={`${plan.status === 'Completed' ? 'bg-green-500' : 'bg-amber-500'} text-white text-[9px] font-bold px-3 py-1 rounded-full border-none`}>
                                                {plan.status.toUpperCase()}
                                            </Badge>
                                            <span className="text-[10px] text-white/40 font-bold uppercase tracking-widest">{plan.capaId}</span>
                                        </div>
                                    </div>

                                    {/* Content Section */}
                                    <CardContent className="p-8 space-y-6 flex-1">
                                        {/* Row 1: Type and Owner */}
                                        <div className="grid grid-cols-2 gap-8">
                                            <div className="space-y-2">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Action Type</p>
                                                <Badge variant="outline" className={`${plan.type === 'Corrective' ? 'border-orange-200 text-orange-600 bg-orange-50' : 'border-blue-200 text-blue-600 bg-blue-50'} text-[10px] font-bold px-3`}>
                                                    {plan.type}
                                                </Badge>
                                            </div>
                                            <div className="space-y-2">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Action Owner / Designation</p>
                                                <div className="flex items-center gap-3">
                                                    <div className="h-9 w-9 rounded-full bg-slate-50 flex items-center justify-center border border-slate-100 shadow-inner">
                                                        <Users className="h-4 w-4 text-slate-400" />
                                                    </div>
                                                    <p className="text-xs font-bold text-slate-700 leading-tight">{plan.ownerName}</p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Row 2: Description */}
                                        <div className="space-y-2">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Action Description</p>
                                            <div className="p-5 bg-slate-50/80 border border-slate-100 rounded-2xl shadow-inner">
                                                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                                                    {plan.desc}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Row 3: Verification Method */}
                                        <div className="space-y-2">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Verification Method</p>
                                            <div className="p-4 bg-indigo-50/30 border border-indigo-100/50 rounded-2xl flex items-center gap-3">
                                                <ListChecks className="h-4 w-4 text-indigo-400" />
                                                <p className="text-xs text-indigo-900 font-semibold italic">{plan.method}</p>
                                            </div>
                                        </div>

                                        {/* Row 4: Evidence & Review (Dual Section) */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-slate-100">
                                            <div className="space-y-3">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Implementation Evidence</p>
                                                {plan.evidence ? (
                                                    <div className="p-3 bg-green-50 border border-green-100 rounded-xl flex items-center justify-between group/ev">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-2 bg-white rounded-lg shadow-sm">
                                                                <FileText className="h-4 w-4 text-green-600" />
                                                            </div>
                                                            <span className="text-[11px] font-bold text-green-800 truncate max-w-[120px]">{plan.evidence}</span>
                                                        </div>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-green-400 hover:text-green-600 hover:bg-green-100/50" disabled={getAccessLevel("ACTION_PLAN_IMPLEMENTATION", "MANAGE_EVIDENCE") !== "FULL"}>
                                                            <Eye className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                ) : (
                                                    <Button variant="outline" className="w-full h-11 border-dashed border-slate-200 text-slate-400 text-[10px] font-bold uppercase tracking-widest hover:bg-slate-50" disabled={getAccessLevel("ACTION_PLAN_IMPLEMENTATION", "MANAGE_EVIDENCE") !== "FULL"}>
                                                        <Paperclip className="h-4 w-4 mr-2" /> Upload Evidence
                                                    </Button>
                                                )}
                                            </div>
                                            <div className="space-y-3">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Review Governance</p>
                                                <div className={`p-3 rounded-xl border ${plan.reviewStatus === 'Accepted' ? 'bg-emerald-50 border-emerald-100' : plan.reviewStatus === 'Rejected' ? 'bg-rose-50 border-rose-100' : 'bg-slate-50 border-slate-100'}`}>
                                                    <div className="flex items-center justify-between mb-2">
                                                        <span className="text-[9px] font-bold uppercase text-slate-400">Status</span>
                                                        <Badge className={`${plan.reviewStatus === 'Accepted' ? 'bg-emerald-600' : plan.reviewStatus === 'Rejected' ? 'bg-rose-600' : 'bg-slate-400'} text-white border-none h-4 px-2 text-[8px]`}>
                                                            {plan.reviewStatus.toUpperCase()}
                                                        </Badge>
                                                    </div>
                                                    <div className="space-y-1">
                                                        <p className="text-[10px] font-bold text-slate-700 leading-none">{plan.reviewedBy}</p>
                                                        <p className="text-[9px] text-slate-400 font-medium">Verified on {plan.reviewDate}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>

                                    {/* Footer Section */}
                                    <CardFooter className="bg-slate-50 border-t py-4 px-8 flex justify-between items-center group-hover:bg-slate-100/50 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="w-2 h-2 rounded-full bg-slate-300 animate-pulse" />
                                            <p className="text-[9px] font-bold text-slate-400 italic">Last tracked: {new Date().toLocaleDateString()}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            {persona === 'CAPA_OWNER' && (
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    className="h-8 px-4 text-[10px] font-bold uppercase tracking-wider bg-white border-slate-200 hover:bg-slate-50 transition-all active:scale-95"
                                                    onClick={() => setShowManageAccessModal(true)}
                                                >
                                                    Manage Access
                                                </Button>
                                            )}
                                            <Button
                                                size="sm"
                                                className="h-8 px-5 bg-slate-900 text-white hover:bg-slate-800 text-[10px] font-bold uppercase tracking-wider shadow-md transition-all active:scale-95"
                                                onClick={() => setShowViewMetricsModal(true)}
                                            >
                                                View Metrics
                                            </Button>
                                        </div>
                                    </CardFooter>
                                </Card>
                            ))}
                        </div>
                    </div>
                );
            case "ACTION_PLAN_EFFECTIVENESS":
                const effAccess = getAccessLevel("ACTION_PLAN_EFFECTIVENESS");
                if (effAccess === "HIDDEN") return null;

                if (effAccess === "STATUS_ONLY") {
                    return (
                        <div className="space-y-6">
                            <div className="border rounded-xl p-8 bg-slate-900 text-center text-white">
                                <CheckCircle2 className="h-12 w-12 text-primary mx-auto mb-4" />
                                <h3 className="text-xl font-bold mb-2">Resolution Tracking</h3>
                                <p className="text-white/60 mb-6">Corrective actions are being finalized and verified for effectiveness.</p>
                                <div className="max-w-md mx-auto bg-white/5 p-4 rounded-lg border border-white/10">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-xs font-bold text-white/40 uppercase">Overall Progress</span>
                                        <Badge className="bg-primary text-white border-none">95% Complete</Badge>
                                    </div>
                                    <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                                        <div className="bg-primary h-full w-[95%]" />
                                    </div>
                                </div>
                            </div>
                            <p className="text-[10px] text-slate-400 italic text-center">Technical effectiveness data and internal audit trails are restricted from external view.</p>
                        </div>
                    );
                }
                return (
                    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
                        {/* Summary Header */}
                        <div className="flex justify-between items-end mb-2">
                            <div>
                                <h4 className="text-2xl font-black text-slate-900 tracking-tight">Effectiveness Tracking</h4>
                                <div className="flex items-center gap-2 mt-1">
                                    <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">AI Agent: Performance Synthesis & Validation</p>
                                    <Badge className="bg-indigo-500 text-white text-[9px] flex items-center gap-1.5 border-none">
                                        <Bot className="h-3 w-3" />
                                        Summary Report Agent
                                    </Badge>
                                    <Badge className="bg-indigo-100 text-indigo-600 text-[9px] flex items-center gap-1.5 border-none">
                                        <RefreshCw className="h-3 w-3" />
                                        Regenerate Action Plan Agent
                                    </Badge>
                                </div>
                            </div>
                            <Badge className="bg-green-600 text-white font-bold px-4 py-1.5 rounded-full text-[10px] tracking-widest uppercase">Closure Phase</Badge>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Left Column: AI Analysis */}
                            <div className="lg:col-span-2 space-y-6">
                                <Card className="border-none shadow-2xl shadow-indigo-500/10 overflow-hidden rounded-[2.5rem] bg-white ring-1 ring-slate-100">
                                    <CardHeader className="bg-slate-900 px-8 py-6">
                                        <div className="flex items-center gap-4">
                                            <div className="h-12 w-12 rounded-2xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                                                <Zap className="h-6 w-6 text-white" />
                                            </div>
                                            <div>
                                                <CardTitle className="text-white text-lg">AI Analysis Output</CardTitle>
                                                <CardDescription className="text-white/40 text-[10px] font-bold uppercase tracking-widest">Conducted by AGENTIC-COE-7</CardDescription>
                                            </div>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="p-8 space-y-8">
                                        {/* Comparison 1: Evidence vs Action Plan */}
                                        <div className="p-6 bg-slate-50 rounded-3xl border border-slate-100 space-y-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Comparison: Evidence vs. Action Plan</span>
                                            </div>
                                            <p className="text-sm text-slate-700 leading-relaxed font-medium italic">
                                                "AI Agent cross-referenced Material Certification (MatCert_REV_Final.pdf) with Action AP-001. Technical specifications of Grade 5 Titanium (density 4.43g/cm³) perfectly align with the proposed mitigation strategy for frequency resonance suppression."
                                            </p>
                                        </div>

                                        {/* Comparison 2: Progress vs Complaint */}
                                        <div className="p-6 bg-indigo-50/30 rounded-3xl border border-indigo-100/50 space-y-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Search className="h-4 w-4 text-indigo-400" />
                                                <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Comparison: Progress vs. Complaint</span>
                                            </div>
                                            <p className="text-sm text-slate-700 leading-relaxed font-medium italic">
                                                "Comparing historical vibration logs (CP-9902: 85dB @ 4200RPM) against current batch metrics (62dB @ 4200RPM). The data points confirm a 27% reduction in vibrational amplitude, directly addressing the original reported hazard."
                                            </p>
                                        </div>

                                        {/* Evidence Gathered So Far */}
                                        <div className="space-y-4">
                                            <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">Evidence Gathered So Far</p>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {[
                                                    { name: "MatCert_REV_Final.pdf", type: "PDF", date: "Feb 11, 2026" },
                                                    { name: "Stress_Test_Logs.xlsx", type: "XLSX", date: "Feb 10, 2026" },
                                                    { name: "PLM_Gate_Snapshot.png", type: "IMG", date: "Feb 09, 2026" },
                                                    { name: "Closure_Summary.docx", type: "DOCX", date: "Feb 11, 2026" }
                                                ].map((file, i) => (
                                                    <div key={i} className="flex items-center gap-3 p-3 bg-white border border-slate-100 rounded-2xl hover:border-indigo-200 hover:shadow-lg hover:shadow-indigo-500/5 transition-all group pointer-events-none">
                                                        <div className="h-10 w-10 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                                                            <FileText className="h-5 w-5" />
                                                        </div>
                                                        <div className="min-w-0 flex-1">
                                                            <p className="text-xs font-bold text-slate-700 truncate">{file.name}</p>
                                                            <p className="text-[9px] text-slate-400 font-medium uppercase">{file.date}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Right Column: Tracking Elements */}
                            <div className="space-y-6">
                                <Card className="border-slate-200 shadow-xl rounded-[2rem] overflow-hidden bg-white">
                                    <CardHeader className="border-b bg-slate-50/50 py-5">
                                        <CardTitle className="text-sm font-bold uppercase tracking-widest text-slate-600">Tracking Elements</CardTitle>
                                    </CardHeader>
                                    <CardContent className="p-8 space-y-8">
                                        {/* Monitoring Period */}
                                        <div className="space-y-3">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Monitoring Period</p>
                                            <div className="flex items-center gap-4 p-4 bg-slate-900 rounded-3xl text-white shadow-xl">
                                                <div className="h-10 w-10 rounded-2xl bg-white/10 flex items-center justify-center">
                                                    <Calendar className="h-5 w-5 text-indigo-400" />
                                                </div>
                                                <div>
                                                    <p className="text-xs font-bold font-mono tracking-tighter">FEB 11, 2026 — MAR 12, 2026</p>
                                                    <p className="text-[9px] text-white/40 uppercase font-black">30-Day Evaluation window</p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Metrics Observed */}
                                        <div className="space-y-4">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Metrics Observed</p>
                                            <div className="space-y-4">
                                                {[
                                                    { label: "Vibration Amplitude", target: "< 65dB", actual: "62dB", status: "pass" },
                                                    { label: "Material Strain Index", target: "< 0.05", actual: "0.032", status: "pass" },
                                                    { label: "Gate Override Count", target: "0", actual: "0", status: "pass" }
                                                ].map((metric, i) => (
                                                    <div key={i} className="flex justify-between items-center p-3 border-b border-slate-50">
                                                        <div>
                                                            <p className="text-xs font-bold text-slate-700">{metric.label}</p>
                                                            <p className="text-[9px] text-slate-400 font-medium">Target: {metric.target}</p>
                                                        </div>
                                                        <div className="text-right">
                                                            <p className="text-xs font-black text-indigo-600">{metric.actual}</p>
                                                            <Badge className="bg-emerald-500/10 text-emerald-600 border-none text-[8px] h-3.5 mt-1 px-1.5">PASS</Badge>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Conclusion */}
                                        <div className="space-y-3">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Effectiveness Conclusion</p>
                                            <div className="p-6 bg-emerald-50 border-2 border-emerald-500/20 rounded-[2rem] flex items-center gap-5">
                                                <div className="h-12 w-12 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/40">
                                                    <ShieldCheck className="h-6 w-6 text-white" />
                                                </div>
                                                <div>
                                                    <p className="text-lg font-black text-emerald-900 tracking-tight leading-none mb-1">EFFECTIVE</p>
                                                    <p className="text-[10px] text-emerald-700/60 font-bold uppercase tracking-widest leading-none">Mitigation Strategy Validated</p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Reviewer Approval */}
                                        <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                                            <div>
                                                <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Approved by</p>
                                                <p className="text-xs font-bold text-slate-900 leading-none">Robert Ford</p>
                                                <p className="text-[10px] text-slate-400 font-medium">Quality Director</p>
                                            </div>
                                            <div className="text-right flex flex-col items-end">
                                                <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Date Certified</p>
                                                <Badge variant="outline" className="bg-slate-50 border-slate-200 text-slate-600 text-[10px] font-mono">2026-02-11</Badge>
                                            </div>
                                        </div>

                                        {((persona === 'REVIEWER' || persona === 'CAPA_OWNER') && getAccessLevel("ACTION_PLAN_EFFECTIVENESS") === "FULL") ? (
                                            <Button
                                                className="w-full h-14 gradient-primary text-white border-none shadow-2xl shadow-primary/30 rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] transition-all hover:-translate-y-1 active:scale-95"
                                                onClick={() => setStageIndex(-1)}
                                            >
                                                Close & Sign CAPA Case
                                            </Button>
                                        ) : (
                                            <div className="text-center p-4 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                                                <p className="text-[10px] text-slate-400 font-bold uppercase italic tracking-widest">
                                                    {getAccessLevel("ACTION_PLAN_EFFECTIVENESS") === "STATUS_ONLY" ? "Viewing Certified Effectiveness Report" : "Awaiting Final Executive Review"}
                                                </p>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen flex flex-col bg-slate-50">
            <Header />
            <main className="flex-1 container py-10">
                <div className="max-w-full mx-auto flex flex-col lg:flex-row gap-8">

                    {/* Main Content Area */}
                    <div className="flex-1 order-2 lg:order-1">
                        <div className="mb-8">
                            <h2 className="text-3xl font-bold text-slate-900">CAPA Enterprise Navigator</h2>
                        </div>

                        {/* Main Content Card */}
                        <Card className="shadow-2xl border-none ring-1 ring-slate-200 overflow-hidden">
                            <CardHeader className="bg-white border-b border-slate-100 py-6">
                                <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-2xl ${stageIndex === -1 ? 'bg-success text-success-foreground' : `${currentStageInfo.color} text-white`}`}>
                                            {stageIndex === -1 ? <CheckCircle2 className="h-6 w-6" /> : <currentStageInfo.icon className="h-6 w-6" />}
                                        </div>
                                        <div>
                                            <CardTitle className="text-2xl">{stageIndex === -1 ? "Process Complete" : currentStageInfo.label}</CardTitle>
                                            <CardDescription className="max-w-md">{stageIndex === -1 ? "All required actions have been documented and verified." : currentStageInfo.purpose}</CardDescription>
                                        </div>
                                    </div>
                                    {stageIndex !== -1 && (
                                        <div className="flex flex-col items-end gap-2">
                                            <Badge variant="outline" className="w-fit h-fit px-3 py-1 bg-slate-50 border-slate-200 text-slate-600 font-semibold">
                                                Step {stageIndex + 1} of {visibleStages.length}
                                            </Badge>
                                            {!config.editableStages.includes(currentStageInfo.id) && (
                                                <Badge variant="destructive" className="text-[10px] bg-red-100 text-red-600 border-none">Read-Only Access</Badge>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="py-8 bg-white min-h-[400px]">
                                {renderStageContent()}
                            </CardContent>
                            {stageIndex !== -1 && (
                                <CardFooter className="flex justify-between border-t bg-slate-50 py-4 px-6">
                                    <Button
                                        variant="ghost"
                                        onClick={prevStage}
                                        disabled={stageIndex === 0}
                                        className="gap-2 text-slate-500"
                                    >
                                        <ChevronLeft className="h-4 w-4" /> Back
                                    </Button>
                                    <Button
                                        onClick={nextStage}
                                        className="gap-2 bg-slate-900 hover:bg-slate-800 text-white px-8"
                                    >
                                        {stageIndex === visibleStages.length - 1 ? "Close Process" : "Continue"} <ChevronRight className="h-4 w-4" />
                                    </Button>
                                </CardFooter>
                            )}
                        </Card>
                    </div>

                </div>
            </main>
            <Footer />

            {/* Risk Score Calculation Loading Modal */}
            {isCalculatingRiskScore && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
                    <Card className="w-full max-w-md mx-4 shadow-2xl border-none">
                        <CardContent className="pt-8 pb-8 text-center space-y-6">
                            <div className="flex justify-center">
                                <div className="relative">
                                    <div className="w-20 h-20 border-4 border-blue-200 rounded-full"></div>
                                    <div className="w-20 h-20 border-4 border-blue-600 rounded-full animate-spin border-t-transparent absolute top-0 left-0"></div>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold text-slate-900">Calculating Risk Score</h3>
                                <p className="text-sm text-slate-600">
                                    Backend agent is analyzing severity, occurrence, and detection parameters...
                                </p>
                            </div>
                            <div className="flex items-center justify-center gap-1">
                                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Action Plan Generation Loading Modal */}
            {showGeneratingActionPlanModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
                    <Card className="w-full max-w-md mx-4 shadow-2xl border-none">
                        <CardContent className="pt-8 pb-8 text-center space-y-6">
                            <div className="flex justify-center">
                                <div className="relative">
                                    <div className="w-20 h-20 border-4 border-indigo-200 rounded-full"></div>
                                    <div className="w-20 h-20 border-4 border-indigo-600 rounded-full animate-spin border-t-transparent absolute top-0 left-0"></div>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold text-slate-900">AI is generating the Action Plan...</h3>
                                <p className="text-slate-500 text-sm">Our persona-driven agents are synthesizing the optimal corrective and preventive actions based on the verified root cause.</p>
                            </div>
                            <div className="pt-4 flex flex-col items-center gap-2">
                                <div className="flex gap-1">
                                    <div className="h-1.5 w-1.5 bg-indigo-600 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    <div className="h-1.5 w-1.5 bg-indigo-600 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                    <div className="h-1.5 w-1.5 bg-indigo-600 rounded-full animate-bounce"></div>
                                </div>
                                <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-widest">Synthesis in Progress</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* RCA Finding Loading Modal */}
            {showFindingRCAModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
                    <Card className="w-full max-w-md mx-4 shadow-2xl border-none">
                        <CardContent className="pt-8 pb-8 text-center space-y-6">
                            <div className="flex justify-center">
                                <div className="relative">
                                    <div className="w-20 h-20 border-4 border-slate-100 rounded-full"></div>
                                    <div className="w-20 h-20 border-4 border-slate-900 rounded-full animate-spin border-t-transparent absolute top-0 left-0"></div>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold text-slate-900">AI Agent is finding the RCA...</h3>
                                <p className="text-slate-500 text-sm">Synthesizing investigation data and identifying the verified root cause through physics-based reasoning.</p>
                            </div>
                            <div className="pt-4 flex flex-col items-center gap-2">
                                <div className="flex gap-1">
                                    <div className="h-1.5 w-1.5 bg-slate-900 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    <div className="h-1.5 w-1.5 bg-slate-900 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                    <div className="h-1.5 w-1.5 bg-slate-900 rounded-full animate-bounce"></div>
                                </div>
                                <span className="text-[10px] font-bold text-slate-900 uppercase tracking-widest">Investigation in Progress</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Audit Trail Modal */}
            {showAuditTrailModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center animate-in fade-in duration-300">
                    <Card className="w-full max-w-2xl mx-4 shadow-2xl border-none overflow-hidden rounded-3xl">
                        <CardHeader className="bg-slate-900 text-white flex-row justify-between items-center py-4 px-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white/10 rounded-lg">
                                    <History className="h-4 w-4 text-white" />
                                </div>
                                <div>
                                    <CardTitle className="text-sm font-bold tracking-tight uppercase">Full Audit Trace</CardTitle>
                                    <CardDescription className="text-white/40 text-[9px] uppercase font-bold tracking-widest">CAPA-2024-8892 Lifecycle History</CardDescription>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 rounded-full hover:bg-white/10 text-white"
                                onClick={() => setShowAuditTrailModal(false)}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="p-0 bg-slate-50 max-h-[60vh] overflow-y-auto">
                            <div className="p-8">
                                <div className="relative space-y-8 before:absolute before:inset-0 before:ml-4 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
                                    {[
                                        { date: "Feb 11, 2026 - 15:45", user: "AI Agent", action: "RCA Generation", desc: "Synthesized investigation reports and verified 'Systemic failure in design review' as root cause.", type: "system" },
                                        { date: "Feb 11, 2026 - 14:20", user: "Alexander (CAPA Owner)", action: "CAPA Intake Submission", desc: "Formally initiated CAPA-2024-8892 following high-risk score validation.", type: "user" },
                                        { date: "Feb 10, 2026 - 09:15", user: "Quality Manager", action: "NC Approval", desc: "Validated complaint CP-9902 and confirmed material fatigue requires CAPA.", type: "user" },
                                        { date: "Feb 09, 2026 - 11:30", user: "AI Agent", action: "Risk Assessment", desc: "Calculated RPN score of 18 (9x2x1) - High Criticality flagged.", type: "system" },
                                        { date: "Feb 08, 2026 - 16:45", user: "External Reporter", action: "Complaint Created", desc: "Reported unexpected vibration in Module B analyzers at Site 4.", type: "user" }
                                    ].map((event, i) => (
                                        <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                                            <div className="flex items-center justify-center w-8 h-8 rounded-full border border-white bg-slate-100 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                                                {event.type === 'system' ? <Search className="h-3 w-3 text-indigo-600" /> : <Users className="h-3 w-3 text-slate-600" />}
                                            </div>
                                            <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2rem)] p-4 rounded-2xl border border-slate-100 bg-white shadow-sm group-hover:shadow-md transition-shadow">
                                                <div className="flex items-center justify-between space-x-2 mb-1">
                                                    <div className="font-bold text-slate-900 text-[10px] uppercase tracking-wider">{event.action}</div>
                                                    <time className="text-[9px] font-medium text-slate-400">{event.date}</time>
                                                </div>
                                                <div className="text-[10px] font-bold text-primary mb-2">{event.user}</div>
                                                <div className="text-xs text-slate-600 leading-relaxed">{event.desc}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="py-4 bg-white border-t border-slate-100 flex justify-end px-6">
                            <Button
                                variant="outline"
                                className="text-[10px] font-bold uppercase tracking-widest h-10 px-6 border-slate-200"
                                onClick={() => setShowAuditTrailModal(false)}
                            >
                                Close Trace
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            )}

            {/* Manage Access Modal */}
            {showManageAccessModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center animate-in fade-in duration-300">
                    <Card className="w-full max-w-md mx-4 shadow-2xl border-none overflow-hidden rounded-3xl bg-white focus-within:ring-2 ring-primary/20 transition-all">
                        <CardHeader className="bg-slate-900 text-white flex-row justify-between items-center py-5 px-8">
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 bg-white/10 rounded-xl">
                                    <ShieldCheck className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <CardTitle className="text-sm font-bold tracking-tight uppercase">Access Control</CardTitle>
                                    <CardDescription className="text-white/40 text-[9px] uppercase font-bold tracking-widest">Authorized Personas & Roles</CardDescription>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 rounded-full hover:bg-white/10 text-white shrink-0"
                                onClick={() => setShowManageAccessModal(false)}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="p-8 space-y-6">
                            <div className="space-y-4">
                                {[
                                    { name: "Sarah Jenkins", role: "Principal Engineer", access: "Full Edit", active: true },
                                    { name: "Robert Ford", role: "Quality Director", access: "Review Only", active: true },
                                    { name: "Michael Chen", role: "QA Lead", access: "Evidence Upload", active: true },
                                    { name: "Alexander G.", role: "CAPA Owner", access: "Administrator", active: true }
                                ].map((user, i) => (
                                    <div key={i} className="flex items-center justify-between p-4 rounded-2xl bg-slate-50 border border-slate-100 group hover:border-primary/20 hover:bg-white hover:shadow-lg hover:shadow-primary/5 transition-all duration-300">
                                        <div className="flex items-center gap-4">
                                            <div className="h-10 w-10 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-400 group-hover:text-primary transition-colors">
                                                <Users className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <p className="text-xs font-bold text-slate-900">{user.name}</p>
                                                <p className="text-[10px] text-slate-400 font-medium uppercase tracking-widest">{user.role}</p>
                                            </div>
                                        </div>
                                        <Badge variant="outline" className="text-[9px] font-bold px-3 border-slate-200 bg-white shadow-sm">
                                            {user.access}
                                        </Badge>
                                    </div>
                                ))}
                            </div>
                            <div className="pt-4 border-t border-slate-100">
                                <Button className="w-full gradient-primary text-white border-none shadow-lg shadow-primary/20 text-[10px] font-bold uppercase tracking-widest h-12 rounded-2xl">
                                    Invite New Contributor
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* View Metrics Modal */}
            {showViewMetricsModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center animate-in fade-in duration-300">
                    <Card className="w-full max-w-lg mx-4 shadow-2xl border-none overflow-hidden rounded-3xl bg-white">
                        <CardHeader className="bg-slate-900 text-white flex-row justify-between items-center py-5 px-8">
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 bg-white/10 rounded-xl">
                                    <BarChart3 className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <CardTitle className="text-sm font-bold tracking-tight uppercase">Execution Metrics</CardTitle>
                                    <CardDescription className="text-white/40 text-[9px] uppercase font-bold tracking-widest">Real-time Performance Data</CardDescription>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 rounded-full hover:bg-white/10 text-white shrink-0"
                                onClick={() => setShowViewMetricsModal(false)}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="p-8 space-y-8">
                            {/* Implementation Health */}
                            <div className="grid grid-cols-2 gap-6">
                                <div className="p-5 bg-emerald-50 border border-emerald-100 rounded-3xl space-y-2">
                                    <div className="flex items-center justify-between">
                                        <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                                        <Badge className="bg-emerald-600 text-white border-none text-[8px] h-4">ON TRACK</Badge>
                                    </div>
                                    <p className="text-2xl font-black text-emerald-900 tracking-tight">85%</p>
                                    <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">Evidence Confirmed</p>
                                </div>
                                <div className="p-5 bg-slate-900 border border-slate-800 rounded-3xl space-y-2">
                                    <div className="flex items-center justify-between">
                                        <Clock className="h-5 w-5 text-indigo-400" />
                                        <Badge className="bg-indigo-600 text-white border-none text-[8px] h-4">SLA: 12D</Badge>
                                    </div>
                                    <p className="text-2xl font-black text-white tracking-tight">4.2<span className="text-sm font-normal text-white/40 ml-1">Days</span></p>
                                    <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Avg. Completion</p>
                                </div>
                            </div>

                            {/* Detailed Stats */}
                            <div className="space-y-4">
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Milestone Breakdown</p>
                                <div className="space-y-4">
                                    {[
                                        { label: "Material Sourcing", status: "Verified", progress: 100 },
                                        { label: "Stress Test Verification", status: "In Progress", progress: 65 },
                                        { label: "Regulatory Log Submission", status: "Pending", progress: 0 }
                                    ].map((stat, i) => (
                                        <div key={i} className="space-y-2">
                                            <div className="flex justify-between items-center text-[10px] font-bold">
                                                <span className="text-slate-700">{stat.label}</span>
                                                <span className={stat.status === 'Verified' ? 'text-emerald-600' : 'text-slate-400'}>{stat.status.toUpperCase()}</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full transition-all duration-1000 ${stat.status === 'Verified' ? 'bg-emerald-500' : 'bg-slate-300'}`}
                                                    style={{ width: `${stat.progress}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="py-5 bg-slate-50 border-t border-slate-100 px-8">
                            <Button variant="outline" className="w-full text-[10px] font-bold uppercase tracking-widest h-11 border-slate-200 bg-white" onClick={() => setShowViewMetricsModal(false)}>
                                Close Dashboard
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default CapaWorkflow;
