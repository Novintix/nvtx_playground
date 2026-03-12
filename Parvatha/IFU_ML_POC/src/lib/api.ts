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
  // Create FormData to send to backend
  const formData = new FormData();
  
  // Send segments with type information for proper formatting
  const segmentsJson = JSON.stringify(payload.segments);
  formData.append("segments_json", segmentsJson);
  
  // Also include the text for fallback
  const text = payload.segments.map((s) => s.translated_text).join("\n\n");
  formData.append("text", text);
  formData.append("filename", `${payload.doc_title}_${payload.lang_key}`);
  
  const response = await fetch(`${BASE_URL}/export-pdf`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to generate PDF: ${response.statusText}`);
  }

  return response.blob();
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
