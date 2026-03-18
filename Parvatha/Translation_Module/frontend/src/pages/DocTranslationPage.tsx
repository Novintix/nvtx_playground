import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Download, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useTranslationStore } from "@/store/useTranslationStore";
import { uploadDocument, translateSegments, generatePdf, updateGlossary } from "@/lib/api";
import type { Segment, TranslatedSegment, ValidationSummary } from "@/lib/api";
import { SegmentViewer } from "@/components/doc-translation/SegmentViewer";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

const LANGUAGES = [
  { code: 'fr', name: 'French' },
  { code: 'es', name: 'Spanish' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'nl', name: 'Dutch' },
  { code: 'pl', name: 'Polish' },
  { code: 'tr', name: 'Turkish' },
  { code: 'ru', name: 'Russian' },
  { code: 'ja', name: 'Japanese' },
  { code: 'zh', name: 'Chinese (Simplified)' },
  { code: 'zh-TW', name: 'Chinese (Traditional)' },
  { code: 'ko', name: 'Korean' },
  { code: 'ar', name: 'Arabic' },
  { code: 'bg', name: 'Bulgarian' },
  { code: 'cs', name: 'Czech' },
  { code: 'ro', name: 'Romanian' },
  { code: 'da', name: 'Danish' },
  { code: 'sk', name: 'Slovak' },
  { code: 'el', name: 'Greek' },
  { code: 'sl', name: 'Slovenian' },
  { code: 'sr', name: 'Serbian' },
  { code: 'et', name: 'Estonian' },
  { code: 'sv', name: 'Swedish' },
  { code: 'fi', name: 'Finnish' },
  { code: 'vi', name: 'Vietnamese' },
  { code: 'hr', name: 'Croatian' },
  { code: 'ga', name: 'Irish' },
  { code: 'hu', name: 'Hungarian' },
  { code: 'mt', name: 'Maltese' },
  { code: 'id', name: 'Indonesian' },
  { code: 'is', name: 'Icelandic' },
  { code: 'kk', name: 'Kazakh' },
  { code: 'lt', name: 'Lithuanian' },
  { code: 'lv', name: 'Latvian' },
  { code: 'no', name: 'Norwegian' },
  { code: 'th', name: 'Thai' },
  { code: 'ms', name: 'Malay' },
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
  const [validationSummary, setValidationSummary] = useState<ValidationSummary | null>(null);
  
  // Glossary Review State
  const [showGlossaryModal, setShowGlossaryModal] = useState(false);
  const [allCorrections, setAllCorrections] = useState<Array<{original: string, mistranslated: string, correct: string, context: string}>>([]);
  const [selectedCorrections, setSelectedCorrections] = useState<Set<number>>(new Set());
  const [savingGlossary, setSavingGlossary] = useState(false);

  const [activeTab, setActiveTab] = useState<"original" | "translated">("original");
  const [fileName, setFileName] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addFile, updateFileStatus, updateFileTranslation, updatePdfGenerated } = useTranslationStore();
  const [lastFileId, setLastFileId] = useState<string>("");

  const handleFiles = async (fileList: FileList) => {
    console.log("Files received:", fileList);
    const file = fileList[0];
    if (!file) {
      console.log("No file selected");
      return;
    }
    const ext = file.name.split(".").pop()?.toLowerCase();
    console.log("File:", file.name, "Extension:", ext);
    if (ext !== "docx") {
      alert("Please upload a .docx file");
      return;
    }

    setFileName(file.name);
    setUploading(true);
    setTranslated([]);
    setActiveTab("original");

    try {
      console.log("Uploading document...");
      const parsed = await uploadDocument(file);
      console.log("Document parsed:", parsed);
      setSegments(parsed);
      setUploadedFile(file);
      const wordCount = parsed.reduce((a, s) => a + s.text.split(/\s+/).length, 0);
      const fileId = addFile({
        name: file.name,
        sourceLanguage: "English",
        targetLanguage: targetLang || "Unselected",
        status: "Pending",
        wordCount: wordCount,
      });
      setLastFileId(fileId);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Failed to upload: " + error);
    } finally {
      setUploading(false);
    }
  };

  const handleTranslate = async () => {
    if (!targetLang || segments.length === 0 || !uploadedFile) return;
    setTranslating(true);
    setProgress({ done: 0, total: segments.length });
    setActiveTab("translated");
    setValidationSummary(null);

    // Update status to processing
    if (lastFileId) {
      updateFileStatus(lastFileId, "Processing");
    }

    try {
      const result = await translateSegments(segments, targetLang, uploadedFile, (done, total) => {
        setProgress({ done, total });
      });
      setTranslated(result.segments);
      setValidationSummary(result.validationSummary || null);
      
      // Extract all corrections from segments
      const corrections: Array<{original: string, mistranslated: string, correct: string, context: string}> = [];
      result.segments.forEach(seg => {
        if (seg.validation && seg.validation.corrections) {
          corrections.push(...seg.validation.corrections);
        }
      });
      setAllCorrections(corrections);
      setSelectedCorrections(new Set(corrections.map((_, i) => i))); // Select all by default
      
      // Update status to completed and store translations
      if (lastFileId) {
        const langName = LANGUAGES.find(l => l.code === targetLang)?.name || targetLang;
        updateFileTranslation(lastFileId, result.segments, langName);
      }
    } finally {
      setTranslating(false);
    }
  };

  const handleGeneratePdf = async () => {
    if (translated.length === 0 || !uploadedFile) return;
    setGenerating(true);
    try {
      // The generatePdf api wrapper actually hits /export-frozen-pdf
      // and now returns a DOCX file that was converted to PDF server-side.
      const blob = await generatePdf(
        uploadedFile,
        translated,
        targetLang,
        fileName.replace(/\.[^.]+$/, ""),
        `IFU-${Date.now()}`
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${fileName.replace(/\.[^.]+$/, "")}_${targetLang}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      
      // Track translation generation
      if (lastFileId) {
        updatePdfGenerated(lastFileId);
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveToGlossary = async () => {
    if (selectedCorrections.size === 0) return;
    
    setSavingGlossary(true);
    try {
      const selectedItems = allCorrections.filter((_, i) => selectedCorrections.has(i));
      const res = await updateGlossary(selectedItems, targetLang);
      alert(`Successfully added ${res.added} items to the ${LANGUAGES.find(l => l.code === targetLang)?.name} glossary!`);
      setShowGlossaryModal(false);
    } catch (error) {
      console.error("Failed to update glossary:", error);
      alert("Failed to update glossary: " + error);
    } finally {
      setSavingGlossary(false);
    }
  };

  const toggleCorrection = (index: number) => {
    const newSelected = new Set(selectedCorrections);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedCorrections(newSelected);
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
              <option key={l.code} value={l.code}>{l.name}</option>
            ))}
          </select>
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
          <>
            <Button onClick={handleGeneratePdf} disabled={generating} variant="outline">
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating PDF...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Download PDF
                </>
              )}
            </Button>
          </>
        )}
      </div>

      {/* Translation progress */}
      {translating && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Translating and validating segments...</span>
            <span>{progress.done}/{progress.total}</span>
          </div>
          <Progress value={progressPct} className="h-2" />
        </div>
      )}

      {/* Validation Summary */}
      {validationSummary && (
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <h3 className="font-semibold mb-3">Validation Summary</h3>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="p-3 rounded-lg bg-muted">
              <div className="text-2xl font-bold">{validationSummary.total}</div>
              <div className="text-xs text-muted-foreground">Validated</div>
            </div>
            <div className="p-3 rounded-lg bg-green-50">
              <div className="text-2xl font-bold text-green-600">{validationSummary.passed}</div>
              <div className="text-xs text-green-600">PASS</div>
            </div>
            <div className="p-3 rounded-lg bg-red-50">
              <div className="text-2xl font-bold text-red-600">{validationSummary.failed}</div>
              <div className="text-xs text-red-600">FAIL</div>
            </div>
            <div className="p-3 rounded-lg bg-yellow-50">
              <div className="text-2xl font-bold text-yellow-600">{validationSummary.errors}</div>
              <div className="text-xs text-yellow-600">Errors</div>
            </div>
          </div>
          
          {allCorrections.length > 0 && (
            <div className="mt-4 flex justify-end">
              <Button onClick={() => setShowGlossaryModal(true)} variant="secondary">
                Review {allCorrections.length} Corrections
              </Button>
            </div>
          )}
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

      {/* Glossary Review Modal */}
      <Dialog open={showGlossaryModal} onOpenChange={setShowGlossaryModal}>
        <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Review Translation Corrections</DialogTitle>
            <DialogDescription>
              The AI validation flagged the following terminology issues. Select the corrections you want to save to the global glossary to improve future translations.
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto py-4 space-y-4">
            {allCorrections.map((correction, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 rounded-lg border bg-muted/50">
                <Checkbox 
                  id={`correction-${index}`} 
                  checked={selectedCorrections.has(index)}
                  onCheckedChange={() => toggleCorrection(index)}
                  className="mt-1"
                />
                <div className="space-y-1 w-full">
                  <Label htmlFor={`correction-${index}`} className="flex flex-col space-y-2 cursor-pointer">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="font-semibold text-muted-foreground mr-2">Original:</span>
                        {correction.original}
                      </div>
                      <div>
                        <span className="font-semibold text-destructive mr-2">Mistranslated:</span>
                        <span className="line-through text-destructive/80">{correction.mistranslated || "N/A"}</span>
                      </div>
                      <div className="col-span-2">
                        <span className="font-semibold text-green-600 mr-2">Correction:</span>
                        <span className="font-medium text-foreground">{correction.correct}</span>
                      </div>
                    </div>
                    {correction.context && (
                      <p className="text-xs text-muted-foreground italic bg-background p-2 rounded">
                        Note: {correction.context}
                      </p>
                    )}
                  </Label>
                </div>
              </div>
            ))}
          </div>
          
          <DialogFooter className="sm:justify-between border-t pt-4">
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="select-all" 
                checked={selectedCorrections.size === allCorrections.length && allCorrections.length > 0}
                onCheckedChange={(checked) => {
                  if (checked) {
                    setSelectedCorrections(new Set(allCorrections.map((_, i) => i)));
                  } else {
                    setSelectedCorrections(new Set());
                  }
                }}
              />
              <Label htmlFor="select-all" className="text-sm text-muted-foreground">Select All</Label>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowGlossaryModal(false)}>Cancel</Button>
              <Button onClick={handleSaveToGlossary} disabled={savingGlossary || selectedCorrections.size === 0}>
                {savingGlossary ? "Saving..." : `Add ${selectedCorrections.size} to Glossary`}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DocTranslationPage;
