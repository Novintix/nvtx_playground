import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Download, FileText, Loader2, CheckCircle2, X, Globe } from "lucide-react";
import { useTranslationStore } from "@/store/useTranslationStore";
import { uploadDocument, translateSegments, generatePdf, generateMultilingualPdf, updateGlossary } from "@/lib/api";
import type { Segment, TranslatedSegment, ValidationSummary } from "@/lib/api";
import { SegmentViewer } from "@/components/doc-translation/SegmentViewer";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

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

interface LanguageTranslation {
  langCode: string;
  langName: string;
  segments: TranslatedSegment[];
  validationSummary?: ValidationSummary;
  completed: boolean;
}

const DocTranslationPage = () => {
  const [targetLangs, setTargetLangs] = useState<string[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [translating, setTranslating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0, currentLang: '' });
  const [segments, setSegments] = useState<Segment[]>([]);
  const [languageTranslations, setLanguageTranslations] = useState<LanguageTranslation[]>([]);
  
  // Glossary Review State
  const [showGlossaryModal, setShowGlossaryModal] = useState(false);
  const [allCorrections, setAllCorrections] = useState<Array<{original: string, mistranslated: string, correct: string, context: string}>>([]);
  const [selectedCorrections, setSelectedCorrections] = useState<Set<number>>(new Set());
  const [savingGlossary, setSavingGlossary] = useState(false);

  // Active tab state - can be "original" or any language code
  const [activeTab, setActiveTab] = useState<string>("original");
  const [fileName, setFileName] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addFile, updateFileStatus, updatePdfGenerated } = useTranslationStore();
  const [lastFileId, setLastFileId] = useState<string>("");

  // Handle multi-language selection
  const toggleLanguage = (code: string) => {
    setTargetLangs(prev => 
      prev.includes(code) 
        ? prev.filter(c => c !== code)
        : [...prev, code]
    );
  };

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
    setLanguageTranslations([]);
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
        targetLanguage: targetLangs.length > 0 ? targetLangs.map(c => LANGUAGES.find(l => l.code === c)?.name || c).join(", ") : "Unselected",
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
    if (targetLangs.length === 0 || segments.length === 0 || !uploadedFile) return;
    setTranslating(true);
    setProgress({ done: 0, total: segments.length * targetLangs.length, currentLang: targetLangs[0] });
    setActiveTab("original");
    setLanguageTranslations([]);

    // Initialize language translation objects
    const langTranslations: LanguageTranslation[] = targetLangs.map(code => ({
      langCode: code,
      langName: LANGUAGES.find(l => l.code === code)?.name || code,
      segments: [],
      completed: false
    }));
    setLanguageTranslations(langTranslations);

    // Update status to processing
    if (lastFileId) {
      updateFileStatus(lastFileId, "Processing");
    }

    try {
      // Translate to each selected language sequentially
      for (let i = 0; i < targetLangs.length; i++) {
        const targetLang = targetLangs[i];
        const langName = LANGUAGES.find(l => l.code === targetLang)?.name || targetLang;
        
        setProgress(prev => ({ ...prev, currentLang: langName }));
        
        const result = await translateSegments(segments, targetLang, uploadedFile, (done, total) => {
          const langIndex = targetLangs.indexOf(targetLang);
          const completedSoFar = langIndex * segments.length + done;
          setProgress({ done: completedSoFar, total: segments.length * targetLangs.length, currentLang: langName });
        });
        
        // Update the language translation with results
        setLanguageTranslations(prev => prev.map((lang, idx) => 
          idx === i 
            ? { ...lang, segments: result.segments, validationSummary: result.validationSummary || undefined, completed: true }
            : lang
        ));
      }
      
      // Extract all corrections from all translations
      const corrections: Array<{original: string, mistranslated: string, correct: string, context: string}> = [];
      langTranslations.forEach(lang => {
        lang.segments.forEach(seg => {
          if (seg.validation && seg.validation.corrections) {
            corrections.push(...seg.validation.corrections);
          }
        });
      });
      setAllCorrections(corrections);
      setSelectedCorrections(new Set(corrections.map((_, i) => i)));
      
      // Set first completed language as active tab
      if (langTranslations.length > 0 && langTranslations[0].completed) {
        setActiveTab(langTranslations[0].langCode);
      }
      
      // Update status to completed
      if (lastFileId) {
        updateFileStatus(lastFileId, "Completed");
      }
    } finally {
      setTranslating(false);
    }
  };

  const handleGeneratePdf = async () => {
    if (languageTranslations.length === 0 || !uploadedFile) return;
    
    // Check if we have single or multiple translations
    const completedTranslations = languageTranslations.filter(l => l.completed);
    
    if (completedTranslations.length === 1) {
      // Single language - use original PDF generation
      const lang = completedTranslations[0];
      setGenerating(true);
      try {
        const blob = await generatePdf(
          uploadedFile,
          lang.segments,
          lang.langCode,
          fileName.replace(/\.[^.]+$/, ""),
          `IFU-${Date.now()}`
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${fileName.replace(/\.[^.]+$/, "")}_${lang.langCode}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        
        if (lastFileId) {
          updatePdfGenerated(lastFileId);
        }
      } finally {
        setGenerating(false);
      }
    } else if (completedTranslations.length > 1) {
      // Multiple languages - use multilingual PDF generation
      setGenerating(true);
      try {
        const translationsMap: Record<string, TranslatedSegment[]> = {};
        completedTranslations.forEach(lang => {
          translationsMap[lang.langCode] = lang.segments;
        });
        
        const blob = await generateMultilingualPdf(
          uploadedFile,
          translationsMap,
          fileName.replace(/\.[^.]+$/, ""),
          `IFU-${Date.now()}`
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${fileName.replace(/\.[^.]+$/, "")}_multilingual.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        
        if (lastFileId) {
          updatePdfGenerated(lastFileId);
        }
      } finally {
        setGenerating(false);
      }
    }
  };

  const handleSaveToGlossary = async () => {
    if (selectedCorrections.size === 0) return;
    
    setSavingGlossary(true);
    try {
      const selectedItems = allCorrections.filter((_, i) => selectedCorrections.has(i));
      // Save to the currently active language's glossary
      const currentLang = activeTab === "original" 
        ? targetLangs[0] 
        : activeTab;
      const res = await updateGlossary(selectedItems, currentLang);
      alert(`Successfully added ${res.added} items to the ${LANGUAGES.find(l => l.code === currentLang)?.name} glossary!`);
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
  const completedTranslations = languageTranslations.filter(l => l.completed);
  const hasTranslation = completedTranslations.length > 0;
  const isMultilingual = completedTranslations.length > 1;
  const progressPct = progress.total > 0 ? (progress.done / progress.total) * 100 : 0;

  // Get current language translation for display
  const currentLangTranslation = activeTab !== "original" 
    ? languageTranslations.find(l => l.langCode === activeTab)
    : null;

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
          <label className="text-xs font-medium text-muted-foreground">Target Languages (select multiple)</label>
          <div className="flex flex-wrap gap-2">
            {LANGUAGES.map((lang) => (
              <Button
                key={lang.code}
                variant={targetLangs.includes(lang.code) ? "default" : "outline"}
                size="sm"
                onClick={() => toggleLanguage(lang.code)}
                className="text-xs"
                disabled={translating}
              >
                {lang.name}
                {targetLangs.includes(lang.code) && <CheckCircle2 className="ml-1 h-3 w-3" />}
              </Button>
            ))}
          </div>
        </div>
        <Button
          onClick={handleTranslate}
          disabled={translating || targetLangs.length === 0 || !hasSegments}
        >
          {translating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Translating...
            </>
          ) : (
            <>
              <Globe className="mr-2 h-4 w-4" />
              Translate to {targetLangs.length} {targetLangs.length === 1 ? 'Language' : 'Languages'}
            </>
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
                  {isMultilingual ? 'Download Multilingual PDF' : 'Download PDF'}
                </>
              )}
            </Button>
          </>
        )}
      </div>

      {/* Selected languages display */}
      {targetLangs.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Selected:</span>
          {targetLangs.map(code => (
            <Badge key={code} variant="secondary" className="gap-1">
              {LANGUAGES.find(l => l.code === code)?.name}
              <X 
                className="h-3 w-3 cursor-pointer" 
                onClick={() => !translating && toggleLanguage(code)}
              />
            </Badge>
          ))}
        </div>
      )}

      {/* Translation progress */}
      {translating && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Translating to {progress.currentLang}... ({progress.done}/{progress.total} segments)</span>
            <span>{Math.round(progressPct)}%</span>
          </div>
          <Progress value={progressPct} className="h-2" />
        </div>
      )}

      {/* Validation Summary */}
      {hasTranslation && !translating && (
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <h3 className="font-semibold mb-3">Translation Status</h3>
          <div className="flex flex-wrap gap-3">
            {languageTranslations.map(lang => (
              <div key={lang.langCode} className={`p-3 rounded-lg ${lang.completed ? 'bg-green-50 border border-green-200' : 'bg-muted'}`}>
                <div className="flex items-center gap-2">
                  {lang.completed ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                  <span className="font-medium">{lang.langName}</span>
                </div>
                {lang.validationSummary && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {lang.validationSummary.passed}/{lang.validationSummary.total} passed
                  </div>
                )}
              </div>
            ))}
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
          {/* Tab headers - Dynamic tabs that can be switched during translation */}
          <div className="border-b flex flex-wrap">
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
            {/* Language tabs - can be switched during translation */}
            {languageTranslations.map(lang => (
              <button
                key={lang.langCode}
                onClick={() => setActiveTab(lang.langCode)}
                disabled={!lang.completed && translating}
                className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === lang.langCode
                    ? "border-primary text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {lang.completed ? (
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                ) : translating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Globe className="h-4 w-4" />
                )}
                {lang.langName} {lang.segments.length > 0 ? `(${lang.segments.length})` : ""}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="p-6 max-h-[60vh] overflow-auto">
            {activeTab === "original" ? (
              <SegmentViewer segments={segments} />
            ) : currentLangTranslation && currentLangTranslation.segments.length > 0 ? (
              <SegmentViewer
                segments={segments}
                translations={currentLangTranslation.segments}
              />
            ) : (
              <p className="text-muted-foreground text-sm italic py-8 text-center">
                {translating
                  ? "Translation in progress..."
                  : "Translation not yet available for this language."}
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
