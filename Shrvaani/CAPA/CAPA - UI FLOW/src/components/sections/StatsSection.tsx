const StatsSection = () => {
  const stats = [
    { value: "8", label: "Workflow Pages" },
    { value: "6", label: "User Roles" },
    { value: "100%", label: "Audit Trail Coverage" },
    { value: "24/7", label: "Compliance Tracking" },
  ];

  return (
    <section className="py-16 bg-card border-y border-border">
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-4xl md:text-5xl font-bold text-accent mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground font-medium">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
