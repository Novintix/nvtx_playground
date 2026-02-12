import { useState } from "react";
import { Network, ChevronDown, ChevronUp, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const AgentsSection = () => {
    const [expandedOrchestrators, setExpandedOrchestrators] = useState<Set<string>>(new Set());

    const toggleOrchestrator = (id: string) => {
        const newExpanded = new Set(expandedOrchestrators);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedOrchestrators(newExpanded);
    };

    const orchestrators = [
        {
            id: "risk-score",
            name: "Risk Score Agent",
            description: "Generates risk score using SOD (Severity, Occurrence, Detection) technique according to company policy",
            color: "from-purple-500 to-pink-500",
            subAgents: [
                { name: "Mapping from FMEA Agent", description: "Maps complaint to FMEA database" },
                { name: "Risk Score Calculator", description: "Creates risk score according to policy" }
            ]
        },
        {
            id: "why-analysis",
            name: "Why Analysis",
            description: "Uses the 5-Why methodology to find the root cause for the CAPA initialized",
            color: "from-orange-500 to-red-500",
            subAgents: [
                { name: "Question Agent", description: "Generates the 'why' questions" },
                { name: "Answer/List of Causes Agent", description: "Provides answers and lists potential causes" },
                { name: "Validate Agent with Evidence", description: "Validates causes with supporting evidence" },
                { name: "Ranking Agent", description: "Ranks causes by likelihood and impact" },
                { name: "Validator Ranking Agent", description: "Validates the ranking methodology" },
                { name: "Loop Control Agent", description: "Controls when to stop the why iteration" },
                { name: "Guardrails Agent", description: "Ensures questions remain relevant and logical" },
                { name: "Zero Evidence Mode Agent", description: "Handles scenarios with no supporting evidence" }
            ]
        },
        {
            id: "fishbone-analysis",
            name: "Fishbone Analysis",
            description: "Uses Fishbone methodology to find the root cause for the CAPA",
            color: "from-blue-500 to-cyan-500",
            subAgents: [
                { name: "List of Causes Agent", description: "Generates potential causes" },
                { name: "Categorize Agent", description: "Maps causes to 6 Fishbone categories (Man, Machine, Material, Method, Measurement, Environment)" },
                { name: "Validator Agent with Evidence", description: "Validates categorization with evidence" },
                { name: "Ranking Agent", description: "Ranks causes by priority" },
                { name: "Validator Ranking Agent", description: "Validates the ranking logic" },
                { name: "Zero Evidence Agent", description: "Handles causes without evidence" },
                { name: "Guardrails Agent", description: "Ensures proper categorization and relevance" }
            ]
        }
    ];

    const standaloneCategories = [
        {
            id: "complaint-ingestion",
            title: "Complaint Ingestion",
            agents: [
                { name: "Complaint Ingestor", description: "Ingests complaints and determines if OCR is needed or not" }
            ]
        },
        {
            id: "capa-validation",
            title: "CAPA Validation & Risk Assessment",
            agents: [
                { name: "CAPA Validator - Similar Cases", description: "Identifies similar cases of the same type of CAPA in the PLM system. Analyzes patterns to inform current CAPA decision" },
                { name: "Regulatory Agent", description: "Assesses regulatory impact and compliance requirements for the CAPA" },
                { name: "AI Reasoning Agent", description: "Provides a summary of why the CAPA is recommended or not" },
                { name: "AI Confidence Score Agent", description: "Indicates how sure the AI is on recommending the CAPA requirement" },
                { name: "CAPA Needed Agent", description: "Determines if CAPA is needed using threshold-based decision making" }
            ]
        },
        {
            id: "capa-intake",
            title: "CAPA Intake Form",
            agents: [
                { name: "AI Assistant (Intake Form)", description: "Asks for mandatory details and validates them for CAPA intake form completion" }
            ]
        },
        {
            id: "action-planning",
            title: "Action Planning",
            agents: [
                { name: "Action Planner Agent", description: "Gets the organization details, matches the RCA findings, and identifies steps from QMS. Generates the action plan by department, resource required, and timeline allocated" }
            ]
        },
        {
            id: "plan-effectiveness",
            title: "Plan Effectiveness",
            agents: [
                { name: "Summary Report Agent", description: "Generates the CAPA summary report and evaluates plan effectiveness" }
            ]
        },
        {
            id: "agent-replanning",
            title: "Agent Replanning",
            agents: [
                { name: "Regenerate Action Plan Agent", description: "Regenerates the action plan based on new inputs, feedback, or changed circumstances" }
            ]
        }
    ];

    return (
        <section id="agents" className="py-24 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(139,92,246,0.1),transparent)] pointer-events-none" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.1),transparent)] pointer-events-none" />

            <div className="container relative z-10">
                {/* Header */}
                <div className="text-center mb-20">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
                        <Network className="h-4 w-4 text-purple-400" />
                        <span className="text-sm font-medium text-white/90">AI-Powered Intelligence</span>
                    </div>

                    <h2 className="text-4xl md:text-5xl font-black text-white mb-6 tracking-tight">
                        AI <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">Agents</span> Architecture
                    </h2>
                    <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
                        30 specialized AI agents: 3 orchestrators with 17 sub-agents, plus 10 standalone agents
                    </p>
                </div>

                {/* Orchestration Agents */}
                <div className="mb-16">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="h-1 flex-1 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent" />
                        <h3 className="text-2xl font-black text-white uppercase tracking-wider">
                            Orchestration Agents
                        </h3>
                        <div className="h-1 flex-1 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent" />
                    </div>

                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
                        {orchestrators.map((orchestrator) => {
                            const isExpanded = expandedOrchestrators.has(orchestrator.id);
                            return (
                                <div
                                    key={orchestrator.id}
                                    className="group relative bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 overflow-hidden transition-all duration-300 hover:border-white/20"
                                >
                                    {/* Orchestrator Header */}
                                    <button
                                        onClick={() => toggleOrchestrator(orchestrator.id)}
                                        className="w-full p-6 text-left transition-colors hover:bg-white/5"
                                    >
                                        <div className="flex items-start justify-between gap-3 mb-3">
                                            <Badge className="bg-purple-500/20 text-purple-300 border-purple-400/30 text-[10px] shrink-0">
                                                ORCHESTRATOR
                                            </Badge>
                                            {isExpanded ? (
                                                <ChevronUp className="h-5 w-5 text-slate-400 shrink-0" />
                                            ) : (
                                                <ChevronDown className="h-5 w-5 text-slate-400 shrink-0" />
                                            )}
                                        </div>

                                        <h4 className="text-lg font-bold text-white mb-2 leading-tight">{orchestrator.name}</h4>
                                        <p className="text-sm text-slate-400 leading-relaxed">{orchestrator.description}</p>

                                        <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                                            <Zap className="h-3 w-3" />
                                            <span>{orchestrator.subAgents.length} sub-agents</span>
                                        </div>
                                    </button>

                                    {/* Sub-agents (Expandable) */}
                                    {isExpanded && (
                                        <div className="border-t border-white/10 bg-black/20 p-6 space-y-3">
                                            {orchestrator.subAgents.map((subAgent, idx) => (
                                                <div key={idx} className="flex items-start gap-3 group/sub">
                                                    <div className="h-1.5 w-1.5 rounded-full bg-purple-400 shrink-0 mt-2" />
                                                    <div className="flex-1 min-w-0">
                                                        <h5 className="text-sm font-semibold text-white/90 leading-tight">{subAgent.name}</h5>
                                                        <p className="text-xs text-slate-500 mt-1">{subAgent.description}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Standalone Agents */}
                <div className="mb-16">
                    <div className="flex items-center gap-3 mb-8">
                        <div className="h-1 flex-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
                        <h3 className="text-2xl font-black text-white uppercase tracking-wider">
                            Standalone Agents
                        </h3>
                        <div className="h-1 flex-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
                    </div>

                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
                        {standaloneCategories.map((category) => {
                            const isExpanded = expandedOrchestrators.has(category.id);
                            return (
                                <div
                                    key={category.id}
                                    className="group relative bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 overflow-hidden transition-all duration-300 hover:border-white/20"
                                >
                                    {/* Category Header */}
                                    <button
                                        onClick={() => toggleOrchestrator(category.id)}
                                        className="w-full p-6 text-left transition-colors hover:bg-white/5"
                                    >
                                        <div className="flex items-start justify-between gap-3 mb-3">
                                            <Badge className="bg-blue-500/20 text-blue-300 border-blue-400/30 text-[10px] shrink-0">
                                                CATEGORY
                                            </Badge>
                                            {isExpanded ? (
                                                <ChevronUp className="h-5 w-5 text-slate-400 shrink-0" />
                                            ) : (
                                                <ChevronDown className="h-5 w-5 text-slate-400 shrink-0" />
                                            )}
                                        </div>

                                        <h4 className="text-lg font-bold text-white mb-2 leading-tight">{category.title}</h4>

                                        <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                                            <Zap className="h-3 w-3" />
                                            <span>{category.agents.length} agent{category.agents.length > 1 ? 's' : ''}</span>
                                        </div>
                                    </button>

                                    {/* Agents (Expandable) */}
                                    {isExpanded && (
                                        <div className="border-t border-white/10 bg-black/20 p-6 space-y-3">
                                            {category.agents.map((agent, idx) => (
                                                <div key={idx} className="flex items-start gap-3 group/agent">
                                                    <div className="h-1.5 w-1.5 rounded-full bg-blue-400 shrink-0 mt-2" />
                                                    <div className="flex-1 min-w-0">
                                                        <h5 className="text-sm font-semibold text-white/90 leading-tight">{agent.name}</h5>
                                                        <p className="text-xs text-slate-500 mt-1">{agent.description}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
                    <div className="text-center p-6 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                        <div className="text-3xl font-black text-purple-400 mb-2">3</div>
                        <div className="text-sm text-slate-400 font-medium">Orchestrators</div>
                    </div>
                    <div className="text-center p-6 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                        <div className="text-3xl font-black text-blue-400 mb-2">10</div>
                        <div className="text-sm text-slate-400 font-medium">Standalone</div>
                    </div>
                    <div className="text-center p-6 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                        <div className="text-3xl font-black text-pink-400 mb-2">17</div>
                        <div className="text-sm text-slate-400 font-medium">Sub-Agents</div>
                    </div>
                    <div className="text-center p-6 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                        <div className="text-3xl font-black text-emerald-400 mb-2">30</div>
                        <div className="text-sm text-slate-400 font-medium">Total Agents</div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default AgentsSection;
