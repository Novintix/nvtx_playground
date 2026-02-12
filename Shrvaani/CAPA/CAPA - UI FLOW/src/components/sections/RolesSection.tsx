import { Users, Shield, Eye, ClipboardCheck, UserCog, FileSearch } from "lucide-react";

const RolesSection = () => {
  const roles = [
    {
      icon: Users,
      title: "External Reporter",
      description: "External users (Clients/Customers) who raise complaints.",
      permissions: ["Submit complaints", "Upload supporting docs", "Track complaint status"],
      color: "bg-destructive/10 text-destructive",
    },
    {
      icon: Shield,
      title: "CAPA Owner",
      description: "Responsible for managing the CAPA lifecycle from validation to execution tracking.",
      permissions: ["Validate complaints/NCs", "Initiate CAPA", "Perform RCA", "Create action plans"],
      color: "bg-accent/10 text-accent",
    },
    {
      icon: ClipboardCheck,
      title: "Reviewer / Approver",
      description: "Provides governance and approval authority at critical decision points.",
      permissions: ["Approve/Reject NCs", "Mark CAPA needed", "Approve RCA & Closure"],
      color: "bg-warning/10 text-warning",
    },
    {
      icon: UserCog,
      title: "Action Owner",
      description: "Responsible for executing assigned corrective or preventive actions.",
      permissions: ["Complete assigned actions", "Upload evidence", "Update action status"],
      color: "bg-success/10 text-success",
    },
    {
      icon: Eye,
      title: "Viewer / Auditor",
      description: "Provides read-only access for audit and oversight purposes.",
      permissions: ["Review CAPA records", "Verify audit trail", "Verify compliance"],
      color: "bg-muted text-muted-foreground",
    },
    {
      icon: FileSearch,
      title: "External Action Owner",
      description: "Supplier or vendor responsible for executing assigned actions.",
      permissions: ["Complete supplier actions", "Upload evidence", "Report to CAPA Owner"],
      color: "bg-info/10 text-info",
    },
  ];

  return (
    <section id="roles" className="py-20 bg-background">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            User Roles
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Role-based access control ensures the right people have the right permissions
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {roles.map((role, index) => (
            <div
              key={index}
              className="bg-card rounded-xl border border-border p-6 shadow-card hover:shadow-elevated transition-all duration-300 animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-4 mb-4">
                <div
                  className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${role.color}`}
                >
                  <role.icon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg text-foreground">{role.title}</h3>
                  <p className="text-sm text-muted-foreground">{role.description}</p>
                </div>
              </div>

              <div className="space-y-2">
                {role.permissions.map((permission, permIndex) => (
                  <div
                    key={permIndex}
                    className="flex items-center gap-2 text-sm text-foreground"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                    {permission}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default RolesSection;
