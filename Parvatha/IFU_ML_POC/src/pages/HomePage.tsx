import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { ArrowRight, FolderOpen } from "lucide-react";
import { useTranslationStore } from "@/store/useTranslationStore";

const HomePage = () => {
  const navigate = useNavigate();
  const files = useTranslationStore((s) => s.files);
  const completed = files.filter((f) => f.status === "Completed").length;
  const totalWords = files.reduce((a, f) => a + f.wordCount, 0);

  return (
    <div className="p-6 lg:p-10 space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-primary to-primary/70 p-10 lg:p-14">
        <div className="relative z-10 max-w-2xl">
          <h1 className="text-3xl lg:text-4xl font-bold text-primary-foreground leading-tight mb-4">
            Delivering Precision in Large-Scale Technical Document Translation
          </h1>
          <p className="text-primary-foreground/80 text-lg mb-8">
            Upload and translate technical documents into multiple languages with AI-powered batch translation.
          </p>
          <div className="flex gap-3">
            <Button
              variant="hero"
              size="lg"
              className="bg-card text-foreground hover:bg-card/90"
              onClick={() => navigate("/doc-translation")}
            >
              Start Translation
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button
              variant="hero-outline"
              size="lg"
              className="border-primary-foreground/40 text-primary-foreground hover:bg-primary-foreground/10"
              onClick={() => navigate("/files")}
            >
              <FolderOpen className="mr-2 h-4 w-4" />
              View Files
            </Button>
          </div>
        </div>
        {/* Decorative circles */}
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-primary-foreground/5" />
        <div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-primary-foreground/5" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Documents Translated", value: completed },
          { label: "Words Processed", value: totalWords.toLocaleString() },
          { label: "Languages Used", value: new Set(files.map((f) => f.targetLanguage)).size },
          { label: "Active Projects", value: files.filter((f) => f.status !== "Completed").length },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border bg-card p-5 shadow-sm"
          >
            <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
            <p className="text-2xl font-semibold text-foreground">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Recent files */}
      <div>
        <h2 className="text-lg font-semibold mb-3 text-foreground">Recent Files</h2>
        <div className="rounded-lg border bg-card shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-3 font-medium text-muted-foreground">File Name</th>
                <th className="text-left p-3 font-medium text-muted-foreground">Target</th>
                <th className="text-left p-3 font-medium text-muted-foreground">Status</th>
                <th className="text-left p-3 font-medium text-muted-foreground">Date</th>
              </tr>
            </thead>
            <tbody>
              {files.slice(0, 3).map((f) => (
                <tr key={f.id} className="border-b last:border-0">
                  <td className="p-3 text-foreground">{f.name}</td>
                  <td className="p-3 text-muted-foreground">{f.targetLanguage}</td>
                  <td className="p-3">
                    <StatusBadge status={f.status} />
                  </td>
                  <td className="p-3 text-muted-foreground">{f.createdDate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    Pending: "bg-secondary text-muted-foreground",
    Processing: "bg-accent text-accent-foreground",
    Completed: "bg-primary/10 text-primary",
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || ""}`}>
      {status}
    </span>
  );
}

export default HomePage;
