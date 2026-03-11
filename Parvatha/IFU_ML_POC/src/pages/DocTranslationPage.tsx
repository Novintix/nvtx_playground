import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Download, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { useTranslationStore } from "@/store/useTranslationStore";
import { uploadDocument, translateSegments, generatePdf } from "@/lib/api";
import type { Segment, TranslatedSegment } from "@/lib/api";
import { SegmentViewer } from "@/components/doc-translation/SegmentViewer";
import { Progress } from "@/components/ui/progress";

const LANGUAGES = [
  "French", "German", "Spanish", "Japanese", "Chinese", "Korean",
  "Portuguese", "Italian", "Russian", "Arabic", "Dutch", "Finnish",
];

const DocTranslationPage = () => {
  const [targetLang, setTargetLang] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [translating, setTranslating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [segments, setSegments] = useState<Segment[]>([]);
  const [translated, setTranslated] = useState<TranslatedSegment[]>([]);
  const [activeTab, setActiveTab] = useState<"original" | "translated">("original");
  const [fileName, setFileName] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addFile } = useTranslationStore();

  const handleFiles = async (fileList: FileList) => {
    const file = fileList[0];
    if (!file) return;
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "docx") return;

    setFileName(file.name);
    setUploading(true);
    setTranslated([]);
    setActiveTab("original");

    try {
      const parsed = await uploadDocument(file);
      setSegments(parsed);
      setUploadedFile(file); // Store the file for translation
      addFile({
        name: file.name,
        sourceLanguage: "English",
        targetLanguage: targetLang || "Unselected",
        status: "Pending",
        wordCount: parsed.reduce((a, s) => a + s.text.split(/\s+/).length, 0),
      });
    } finally {
      setUploading(false);
    }
  };

  const handleTranslate = async () => {
    if (!targetLang || segments.length === 0 || !uploadedFile) return;
    setTranslating(true);
    setProgress({ done: 0, total: segments.length });
    setActiveTab("translated");

    try {
      const result = await translateSegments(segments, targetLang, uploadedFile, (done, total) => {
        setProgress({ done, total });
      });
      setTranslated(result);
    } finally {
      setTranslating(false);
    }
  };

  const handleGeneratePdf = async () => {
    if (translated.length === 0) return;
    setGenerating(true);
    try {
      const blob = await generatePdf({
        segments: translated,
        lang_key: targetLang,
        doc_title: fileName.replace(/\.[^.]+$/, ""),
        doc_ref: `IFU-${Date.now()}`,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileName.replace(/\.[^.]+$/, "")}_${targetLang}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setGenerating(false);
    }
  };

  const hasSegments = segments.length > 0;
  const hasTranslation = translated.length > 0;
  const progressPct = progress.total > 0 ? (progress.done / progress.total) * 100 : 0;

  return (
    <div className="p-6 lg:p-10 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">IFU Document Translation</h1>
      </div>

      {/* Settings bar */}
      <div className="flex flex-wrap items-end gap-4 rounded-lg border bg-card p-4 shadow-sm">
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Source Language</label>
          <div className="block w-44 rounded-md border bg-muted px-3 py-2 text-sm text-muted-foreground">
            English (locked)
          </div>
        </div>
        <div className="text-muted-foreground text-lg pb-2">→</div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Target Language</label>
          <select
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
            className="block w-44 rounded-md border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Select language</option>
            {LANGUAGES.map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Model</label>
          <div className="block w-44 rounded-md border bg-muted px-3 py-2 text-sm text-muted-foreground">
            Translation Engine
          </div>
        </div>
        <Button
          onClick={handleTranslate}
          disabled={translating || !targetLang || !hasSegments}
        >
          {translating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Translating...
            </>
          ) : (
            "Translate"
          )}
        </Button>
        {hasTranslation && (
          <Button onClick={handleGeneratePdf} disabled={generating} variant="outline">
            {generating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating PDF...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Generate PDF
              </>
            )}
          </Button>
        )}
      </div>

      {/* Translation progress */}
      {translating && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Translating segments...</span>
            <span>{progress.done}/{progress.total}</span>
          </div>
          <Progress value={progressPct} className="h-2" />
        </div>
      )}

      {/* Upload area */}
      {!hasSegments && !uploading && (
        <div
          className={`rounded-lg border-2 border-dashed bg-card p-16 text-center transition-colors cursor-pointer ${
            dragOver ? "border-primary bg-accent" : "border-border"
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".docx"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
          <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-4" />
          <p className="text-foreground font-medium mb-1">Upload IFU Document (.docx)</p>
          <p className="text-sm text-muted-foreground">Drag & drop or click to browse</p>
          <span className="mt-3 inline-block rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">DOCX</span>
        </div>
      )}

      {uploading && (
        <div className="flex items-center justify-center gap-3 py-16">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="text-muted-foreground">Parsing document...</span>
        </div>
      )}

      {/* Document workspace */}
      {hasSegments && (
        <div className="rounded-lg border bg-card shadow-sm overflow-hidden">
          {/* Tab headers */}
          <div className="border-b flex">
            <button
              onClick={() => setActiveTab("original")}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "original"
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="h-4 w-4" />
              Original ({segments.length} segments)
            </button>
            <button
              onClick={() => setActiveTab("translated")}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "translated"
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {hasTranslation && <CheckCircle2 className="h-4 w-4 text-primary" />}
              Translated {hasTranslation ? `(${translated.length})` : ""}
            </button>
          </div>

          {/* Content */}
          <div className="p-6 max-h-[60vh] overflow-auto">
            {activeTab === "original" ? (
              <SegmentViewer segments={segments} />
            ) : hasTranslation ? (
              <SegmentViewer
                segments={segments}
                translations={translated}
              />
            ) : (
              <p className="text-muted-foreground text-sm italic py-8 text-center">
                {translating
                  ? "Translation in progress..."
                  : "Select a target language and click Translate to begin."}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocTranslationPage;
