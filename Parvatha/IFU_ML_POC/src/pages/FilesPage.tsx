import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Eye, Download, Trash2, CheckSquare, X } from "lucide-react";
import { useTranslationStore } from "@/store/useTranslationStore";

const FilesPage = () => {
  const { files, removeFile } = useTranslationStore();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [batchOption, setBatchOption] = useState<"original" | "translated" | "both">("translated");

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="p-6 lg:p-10 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Files</h1>
          <p className="text-muted-foreground">Manage your uploaded documents</p>
        </div>
        {selected.size > 1 && (
          <Button onClick={() => setShowBatchModal(true)}>
            <Download className="mr-2 h-4 w-4" />
            Batch Download ({selected.size})
          </Button>
        )}
      </div>

      <div className="rounded-lg border bg-card shadow-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-3 w-10">
                <input
                  type="checkbox"
                  checked={selected.size === files.length && files.length > 0}
                  onChange={() =>
                    setSelected(
                      selected.size === files.length
                        ? new Set()
                        : new Set(files.map((f) => f.id))
                    )
                  }
                  className="accent-primary"
                />
              </th>
              <th className="text-left p-3 font-medium text-muted-foreground">File Name</th>
              <th className="text-left p-3 font-medium text-muted-foreground">Source</th>
              <th className="text-left p-3 font-medium text-muted-foreground">Target</th>
              <th className="text-left p-3 font-medium text-muted-foreground">Status</th>
              <th className="text-left p-3 font-medium text-muted-foreground">Words</th>
              <th className="text-left p-3 font-medium text-muted-foreground">Created</th>
              <th className="text-left p-3 font-medium text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.id} className="border-b last:border-0 hover:bg-muted/30">
                <td className="p-3">
                  <input
                    type="checkbox"
                    checked={selected.has(f.id)}
                    onChange={() => toggleSelect(f.id)}
                    className="accent-primary"
                  />
                </td>
                <td className="p-3 text-foreground font-medium">{f.name}</td>
                <td className="p-3 text-muted-foreground">{f.sourceLanguage}</td>
                <td className="p-3 text-muted-foreground">{f.targetLanguage}</td>
                <td className="p-3">
                  <StatusBadge status={f.status} />
                </td>
                <td className="p-3 text-muted-foreground">{f.wordCount.toLocaleString()}</td>
                <td className="p-3 text-muted-foreground">{f.createdDate}</td>
                <td className="p-3">
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Eye className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Download className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive"
                      onClick={() => removeFile(f.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
            {files.length === 0 && (
              <tr>
                <td colSpan={8} className="p-8 text-center text-muted-foreground">
                  No files uploaded yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Batch Download Modal */}
      {showBatchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm">
          <div className="rounded-lg bg-card border shadow-lg w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-foreground">Batch Download</h2>
              <Button variant="ghost" size="icon" onClick={() => setShowBatchModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-3">
              {(
                [
                  ["original", "Download original files"],
                  ["translated", "Download translated files"],
                  ["both", "Download both"],
                ] as const
              ).map(([val, label]) => (
                <label
                  key={val}
                  className={`flex items-center gap-3 rounded-md border p-3 cursor-pointer transition-colors ${
                    batchOption === val ? "border-primary bg-accent" : "border-border"
                  }`}
                >
                  <input
                    type="radio"
                    name="batch"
                    checked={batchOption === val}
                    onChange={() => setBatchOption(val)}
                    className="accent-primary"
                  />
                  <span className="text-sm text-foreground">{label}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowBatchModal(false)}>
                Cancel
              </Button>
              <Button onClick={() => setShowBatchModal(false)}>Download</Button>
            </div>
          </div>
        </div>
      )}
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

export default FilesPage;
