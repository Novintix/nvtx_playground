import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Download, FileText, Loader2, CheckCircle2, X } from "lucide-react";
import { useTranslationStore } from "@/store/useTranslationStore";
import { uploadDocument, translateSegments, generateMultilingualPdf } from "@/lib/api";
import type { Segment, TranslatedSegment } from "@/lib/api";
import { SegmentViewer } from "@/components/doc-translation/SegmentViewer";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent } from "@/components/ui/tabs";

// All 24 EU MDR/FDA languages in alphabetical order
const LANGUAGES = [
  "Arabic",
  "Bulgarian",
  "Chinese",
  "Croatian",
  "Czech",
  "Danish",
  "Dutch",
  "English",
  "Estonian",
  "Finnish",
  "French",
  "German",
  "Greek",
  "Hungarian",
  "Irish",
  "Italian",
  "Japanese",
  "Korean",
  "Latvian",
  "Lithuanian",
  "Maltese",
  "Polish",
  "Portuguese",
  "Romanian",
  "Russian",
  "Slovak",
  "Slovenian",
  "Spanish",
  "Swedish",
];

interface TranslationProgress {
  language: string;
  done: number;
  total: number;
  status: 'pending' | 'translating' | 'completed' | 'error';
  translatedSegments?: TranslatedSegment[];
}

const DocTranslationPage = () => {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [fileName, setFileName] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [activePreviewTab, setActivePreviewTab] = useState<string>("original");
  const [translationProgress, setTranslationProgress] = useState<TranslationProgress[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addFile, updateFileStatus, updateFileTranslation, files } = useTranslationStore();

  // Get the latest uploaded file from store
  const currentFile = files.length > 0 ? files[files.length - 1] : null;

  const handleFiles = async (fileList: FileList) => {
    const file = fileList[0];
    if (!file) return;
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "docx") return;

    setFileName(file.name);
    setUploading(true);
    setSegments([]);
    setSelectedLanguages([]);
    setTranslationProgress([]);
    setActivePreviewTab("original");

    try {
      const parsed = await uploadDocument(file);
      setSegments(parsed);
      setUploadedFile(file);
      addFile({
        name: file.name,
        sourceLanguage: "English",
        targetLanguage: "Multiple",
        status: "Pending",
        wordCount: parsed.reduce((a, s) => a + s.text.split(/\s+/).length, 0),
      });
    } finally {
      setUploading(false);
    }
  };

  const toggleLanguage = (lang: string) => {
    setSelectedLanguages(prev => 
      prev.includes(lang) 
        ? prev.filter(l => l !== lang)
        : [...prev, lang]
    );
  };

  const handleTranslate = async () => {
    if (selectedLanguages.length === 0 || segments.length === 0 || !uploadedFile) return;
    if (!currentFile) return;

    // Initialize progress for all selected languages
    const progress: TranslationProgress[] = selectedLanguages.map(lang => ({
      language: lang,
      done: 0,
      total: segments.length,
      status: 'pending' as const,
    }));
    setTranslationProgress(progress);
    updateFileStatus(currentFile.id, "Processing");

    // Translate for each language sequentially
    for (let i = 0; i < selectedLanguages.length; i++) {
      const targetLang = selectedLanguages[i];
      
      // Update status to translating
      setTranslationProgress(prev => prev.map((p, idx) => 
        idx === i ? { ...p, status: 'translating' } : p
      ));

      try {
        const result = await translateSegments(segments, targetLang, uploadedFile, (done, total) => {
          setTranslationProgress(prev => prev.map((p, idx) => 
            idx === i ? { ...p, done, total } : p
          ));
        });

        setTranslationProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'completed', translatedSegments: result, done: segments.length } : p
        ));

        // Update store with translation
        updateFileTranslation(currentFile.id, result);
      } catch (error) {
        setTranslationProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'error' } : p
        ));
      }
    }

    updateFileStatus(currentFile.id, "Completed");
    // Set first translated language as preview tab
    if (selectedLanguages.length > 0) {
      setActivePreviewTab(selectedLanguages[0]);
    }
  };

  const handleGeneratePdf = async () => {
    if (translationProgress.length === 0 || !uploadedFile) return;
    
    const completedTranslations = translationProgress.filter(p => p.status === 'completed');
    if (completedTranslations.length === 0) return;

    setGenerating(true);
    try {
      // Generate PDF with all translations
      const blob = await generateMultilingualPdf(
        segments,
        completedTranslations.map(t => ({ language: t.language, segments: t.translatedSegments! })),
        fileName.replace(/\.[^.]+$/, ""),
        `IFU-${Date.now()}`
      );
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileName.replace(/\.[^.]+$/, "")}_multilingual.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setGenerating(false);
    }
  };

  const [generating, setGenerating] = useState(false);

  const hasSegments = segments.length > 0;
  const hasTranslations = translationProgress.some(p => p.status === 'completed');
  const allCompleted = translationProgress.length > 0 && translationProgress.every(p => p.status === 'completed');
  const anyTranslating = translationProgress.some(p => p.status === 'translating');
  const atLeastOneCompleted = translationProgress.some(p => p.status === 'completed');

  // Calculate overall progress
  const totalProgress = translationProgress.reduce((acc, p) => acc + p.done, 0);
  const totalSegments = translationProgress.reduce((acc, p) => acc + p.total, 0) * selectedLanguages.length;
  const progressPct = totalSegments > 0 ? (totalProgress / totalSegments) * 100 : 0;

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
          <label className="text-xs font-medium text-muted-foreground">Target Languages</label>
          <div className="flex flex-wrap gap-2 w-full max-w-2xl">
            {LANGUAGES.map(lang => (
              <button
                key={lang}
                onClick={() => toggleLanguage(lang)}
                disabled={hasTranslations}
                className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
                  selectedLanguages.includes(lang)
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-background text-foreground border-border hover:bg-muted"
                } ${hasTranslations ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                {lang}
              </button>
            ))}
          </div>
        </div>
        <Button
          onClick={handleTranslate}
          disabled={anyTranslating || selectedLanguages.length === 0 || !hasSegments}
        >
          {anyTranslating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Translating...
            </>
          ) : (
            "Translate"
          )}
        </Button>
        {atLeastOneCompleted && (
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
      {translationProgress.length > 0 && (
        <div className="space-y-3">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Translating to {selectedLanguages.length} language(s)...</span>
            <span>{Math.round(progressPct)}%</span>
          </div>
          <Progress value={progressPct} className="h-2" />
          <div className="flex flex-wrap gap-2">
            {translationProgress.map(p => (
              <div 
                key={p.language}
                className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs ${
                  p.status === 'completed' 
                    ? 'bg-primary/10 text-primary'
                    : p.status === 'translating'
                    ? 'bg-accent text-accent-foreground'
                    : p.status === 'error'
                    ? 'bg-destructive/10 text-destructive'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {p.status === 'completed' && <CheckCircle2 className="h-3 w-3" />}
                {p.status === 'translating' && <Loader2 className="h-3 w-3 animate-spin" />}
                {p.status === 'error' && <X className="h-3 w-3" />}
                {p.language}: {p.done}/{p.total}
              </div>
            ))}
          </div>
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

      {/* Document workspace with tabs */}
      {hasSegments && (
        <div className="rounded-lg border bg-card shadow-sm overflow-hidden">
          <Tabs value={activePreviewTab} onValueChange={setActivePreviewTab}>
            {/* Tab headers - always clickable for dynamic switching */}
            <div className="border-b flex">
              <button
                onClick={() => setActivePreviewTab("original")}
                className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activePreviewTab === "original"
                    ? "border-primary text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <FileText className="h-4 w-4" />
                Original ({segments.length} segments)
              </button>
              {selectedLanguages.map(lang => {
                const progress = translationProgress.find(p => p.language === lang);
                const isCompleted = progress?.status === 'completed';
                const isTranslating = progress?.status === 'translating';
                
                return (
                  <button
                    key={lang}
                    onClick={() => setActivePreviewTab(lang)}
                    className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activePreviewTab === lang
                        ? "border-primary text-foreground"
                        : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {isCompleted && <CheckCircle2 className="h-4 w-4 text-primary" />}
                    {isTranslating && <Loader2 className="h-4 w-4 animate-spin" />}
                    {lang} {isCompleted ? `(${progress?.translatedSegments?.length || 0})` : ""}
                  </button>
                );
              })}
            </div>

            {/* Content */}
            <div className="p-6 max-h-[60vh] overflow-auto">
              <TabsContent value="original">
                <SegmentViewer segments={segments} />
              </TabsContent>
              
              {selectedLanguages.map(lang => {
                const progress = translationProgress.find(p => p.language === lang);
                const translatedSegments = progress?.translatedSegments;
                
                return (
                  <TabsContent key={lang} value={lang}>
                    {translatedSegments && translatedSegments.length > 0 ? (
                      <SegmentViewer
                        segments={segments}
                        translations={translatedSegments}
                      />
                    ) : progress?.status === 'translating' ? (
                      <div className="flex items-center justify-center gap-3 py-16">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                        <span className="text-muted-foreground">Translating to {lang}...</span>
                      </div>
                    ) : progress?.status === 'error' ? (
                      <p className="text-destructive text-center py-8">
                        Translation failed for {lang}. Please try again.
                      </p>
                    ) : (
                      <p className="text-muted-foreground text-sm italic py-8 text-center">
                        Translation pending for {lang}. Click Translate to begin.
                      </p>
                    )}
                  </TabsContent>
                );
              })}
            </div>
          </Tabs>
        </div>
      )}
    </div>
  );
};


export default DocTranslationPage;
