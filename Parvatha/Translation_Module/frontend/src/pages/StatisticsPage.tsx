import { useTranslationStore } from "@/store/useTranslationStore";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const StatisticsPage = () => {
  const files = useTranslationStore((s) => s.files);
  const completed = files.filter((f) => f.status === "Completed").length;
  const totalWords = files.reduce((a, f) => a + f.wordCount, 0);
  const languages = new Set(files.map((f) => f.targetLanguage));
  const active = files.filter((f) => f.status !== "Completed").length;

  // Build chart data from files
  const langCounts: Record<string, number> = {};
  files.forEach((f) => {
    langCounts[f.targetLanguage] = (langCounts[f.targetLanguage] || 0) + 1;
  });
  const chartData = Object.entries(langCounts).map(([lang, count]) => ({
    language: lang,
    documents: count,
  }));

  const stats = [
    { label: "Documents Translated", value: completed },
    { label: "Words Processed", value: totalWords.toLocaleString() },
    { label: "Languages Used", value: languages.size },
    { label: "Active Projects", value: active },
  ];

  return (
    <div className="p-6 lg:p-10 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Statistics</h1>
        <p className="text-muted-foreground">Usage metrics and analytics</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="rounded-lg border bg-card p-5 shadow-sm">
            <p className="text-sm text-muted-foreground mb-1">{s.label}</p>
            <p className="text-2xl font-semibold text-foreground">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground mb-4">Translation Usage by Language</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="language" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "0.5rem",
                  color: "hsl(var(--foreground))",
                }}
              />
              <Bar dataKey="documents" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default StatisticsPage;
