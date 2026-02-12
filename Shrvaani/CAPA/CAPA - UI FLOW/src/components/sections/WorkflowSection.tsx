import { ArrowRight, AlertCircle, CheckSquare, FileSearch, Search, ClipboardList, PlayCircle, BarChart3 } from "lucide-react";

const WorkflowSection = () => {
  const steps = [
    {
      icon: AlertCircle,
      title: "Complaint",
      description: "Capture quality issues",
      color: "bg-destructive/10 text-destructive",
    },
    {
      icon: CheckSquare,
      title: "Validation",
      description: "Verify legitimacy",
      color: "bg-warning/10 text-warning",
    },
    {
      icon: FileSearch,
      title: "CAPA Intake",
      description: "Initiate formally",
      color: "bg-info/10 text-info",
    },
    {
      icon: Search,
      title: "Investigation",
      description: "Root cause analysis",
      color: "bg-accent/10 text-accent",
    },
    {
      icon: ClipboardList,
      title: "Action Plan",
      description: "Define actions",
      color: "bg-primary/10 text-primary",
    },
    {
      icon: PlayCircle,
      title: "Execution",
      description: "Track progress",
      color: "bg-success/10 text-success",
    },
    {
      icon: BarChart3,
      title: "Reports",
      description: "Audit & compliance",
      color: "bg-muted text-muted-foreground",
    },
  ];

  return (
    <section id="workflow" className="py-20 bg-background">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            CAPA Workflow
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            A structured approach to quality management from complaint to resolution
          </p>
        </div>

        <div className="flex flex-wrap justify-center items-center gap-4 md:gap-2">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div className="flex flex-col items-center text-center group">
                <div
                  className={`flex h-16 w-16 items-center justify-center rounded-2xl ${step.color} transition-transform group-hover:scale-110 mb-3`}
                >
                  <step.icon className="h-7 w-7" />
                </div>
                <h3 className="font-semibold text-foreground text-sm mb-1">{step.title}</h3>
                <p className="text-xs text-muted-foreground max-w-[100px]">{step.description}</p>
              </div>
              {index < steps.length - 1 && (
                <ArrowRight className="h-5 w-5 text-border mx-2 hidden md:block" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default WorkflowSection;
