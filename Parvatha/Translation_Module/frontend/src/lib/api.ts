// Translation API service - connects to FastAPI backend

const BASE_URL = "http://localhost:8000";

export interface Segment {
  id: number;
  type: "h1" | "h2" | "h3" | "p" | "li" | "ol";
  text: string;
}

export interface ValidationResult {
  result: "PASS" | "FAIL" | "ERROR";
  accuracy_note: string;
  terminology_note: string;
  corrections: Array<{
    original: string;
    mistranslated: string;
    correct: string;
    context: string;
  }>;
}

export interface TranslatedSegment {
  id: number;
  type: string;
  text: string;
  translated_text: string;
  validation?: ValidationResult;
}

export interface ValidationSummary {
  total: number;
  passed: number;
  failed: number;
  errors: number;
}

export interface TranslateResponse {
  segments: TranslatedSegment[];
  validation_summary: ValidationSummary;
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

/** Translate segments using NLLB-200 model with validation */
export async function translateSegments(
  segments: Segment[],
  targetLang: string,
  file: File,
  onProgress?: (completed: number, total: number) => void
): Promise<{ segments: TranslatedSegment[]; validationSummary?: ValidationSummary }> {
  const results: TranslatedSegment[] = [];
  let validationSummary: ValidationSummary | undefined;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_lang', targetLang);
  formData.append('run_validation', 'true'); // Enable validation

  // Call the backend translation endpoint
  const response = await fetch(`${BASE_URL}/translate-segments`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Translation failed: ${response.statusText}`);
  }

  // Check if response is standard JSON
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const data = await response.json();
    return { 
      segments: data.segments || [], 
      validationSummary: data.validation_summary || data.validationSummary 
    };
  }

  // Handle streaming NDJSON response
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  if (!reader) {
    throw new Error('No response body');
  }

  while (true) {
    const { done, value } = await reader.read();
    
    if (value) {
      buffer += decoder.decode(value, { stream: !done });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.type === 'progress' && onProgress) {
            onProgress(msg.completed, msg.total);
          } else if (msg.type === 'done') {
            return { segments: msg.segments, validationSummary: msg.validation_summary };
          } else if (msg.type === 'error') {
            throw new Error(msg.detail);
          }
        } catch (e) {
          console.warn('Failed to parse line:', line);
        }
      }
    }

    if (done) {
      if (buffer.trim()) {
        try {
          const msg = JSON.parse(buffer);
          if (msg.type === 'done') {
            return { segments: msg.segments, validationSummary: msg.validation_summary };
          }
        } catch (e) {
          console.warn('Failed to parse final buffer:', buffer);
        }
      }
      break;
    }
  }

  return { segments: results, validationSummary };
}

/** Generate a PDF from translated segments using the backend */
export async function generatePdf(
  originalFile: File,
  translatedSegments: TranslatedSegment[],
  targetLang: string,
  docTitle: string,
  docRef: string
): Promise<Blob> {
  const formData = new FormData();
  formData.append('file', originalFile);
  formData.append('segments', JSON.stringify(translatedSegments));
  formData.append('target_lang', targetLang);
  formData.append('doc_title', docTitle);
  formData.append('doc_ref', docRef);

  const response = await fetch(`${BASE_URL}/export-frozen-pdf`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to generate PDF: ${response.statusText}`);
  }

  return response.blob();
}

/** Update the backend glossary with new term corrections */
export async function updateGlossary(
  corrections: Array<{original: string, mistranslated: string, correct: string, context: string}>,
  targetLang: string
): Promise<{added: number}> {
  const response = await fetch(`${BASE_URL}/glossary/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ corrections, target_lang: targetLang })
  });

  if (!response.ok) {
    throw new Error(`Failed to update glossary: ${response.statusText}`);
  }

  return response.json();
}

/** Generate a multilingual PDF with multiple target languages */
export async function generateMultilingualPdf(
  originalFile: File,
  translationsMap: Record<string, TranslatedSegment[]>, // langCode -> segments
  docTitle: string,
  docRef: string
): Promise<Blob> {
  const formData = new FormData();
  formData.append('file', originalFile);
  formData.append('translations_map', JSON.stringify(translationsMap));
  formData.append('doc_title', docTitle);
  formData.append('doc_ref', docRef);

  const response = await fetch(`${BASE_URL}/export-multilingual-pdf`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to generate multilingual PDF: ${response.statusText}`);
  }

  return response.blob();
}
