// Translation API service - connects to FastAPI backend

const BASE_URL = "http://localhost:8000";

export interface Segment {
  id: number;
  type: "h1" | "h2" | "h3" | "p" | "li" | "ol";
  text: string;
}

export interface TranslatedSegment {
  id: number;
  type: string;
  text: string;
  translated_text: string;
}

export interface GeneratePdfPayload {
  segments: TranslatedSegment[];
  lang_key: string;
  doc_title: string;
  doc_ref: string;
}

/** Upload a .docx file and receive parsed segments */
export async function uploadDocument(file: File): Promise<Segment[]> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/extract-docx`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to extract document: ${response.statusText}`);
  }

  const data = await response.json();
  return data.segments;
}

/** Translate segments using NLLB-200 model */
export async function translateSegments(
  segments: Segment[],
  targetLang: string,
  file: File,
  onProgress?: (completed: number, total: number) => void
): Promise<TranslatedSegment[]> {
  const results: TranslatedSegment[] = [];
  const total = segments.length;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_lang', targetLang);

  // Call the backend translation endpoint
  const response = await fetch(`${BASE_URL}/translate-segments`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Translation failed: ${response.statusText}`);
  }

  const data = await response.json();
  const translatedSegments = data.segments as TranslatedSegment[];

  // Report progress as we process the results
  for (let i = 0; i < translatedSegments.length; i++) {
    results.push(translatedSegments[i]);
    onProgress?.(i + 1, total);
  }

  return results;
}

/** Generate a PDF from translated segments using the frozen IFU template */
export async function generatePdf(payload: GeneratePdfPayload): Promise<Blob> {
  // Create FormData for file upload
  const formData = new FormData();
  
  // We need to store the original file - this would be passed from the UI
  // For now, we'll create a simple PDF using the translated text
  // In production, you'd upload the original DOCX and segments together
  
  const lines = payload.segments.map((s) => s.translated_text).join("\n\n");
  
  // Create a simple text-based PDF as placeholder
  // The backend /export-frozen-pdf endpoint would be used in production
  const content = `IFU Document: ${payload.doc_title}\nRef: ${payload.doc_ref}\nLanguage: ${payload.lang_key}\n\n${lines}`;
  
  // Return as a blob (in production this would be actual PDF from backend)
  return new Blob([content], { type: "application/pdf" });
}

/** Alternative: Generate PDF using backend endpoint (requires original DOCX) */
export async function generatePdfFromBackend(
  originalFile: File,
  translatedSegments: TranslatedSegment[],
  targetLang: string,
  docTitle: string,
  docRef: string
): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", originalFile);
  formData.append("segments", JSON.stringify(translatedSegments));
  formData.append("target_lang", targetLang);
  formData.append("doc_title", docTitle);
  formData.append("doc_ref", docRef);

  const response = await fetch(`${BASE_URL}/export-frozen-pdf`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to generate PDF: ${response.statusText}`);
  }

  return response.blob();
}
