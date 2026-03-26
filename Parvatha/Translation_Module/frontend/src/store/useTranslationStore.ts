import { create } from 'zustand';
import type { Segment, TranslatedSegment } from '@/lib/api';

export type FileStatus = 'Pending' | 'Processing' | 'Completed';

export interface TranslationFile {
  id: string;
  name: string;
  sourceLanguage: string;
  targetLanguage: string;
  status: FileStatus;
  wordCount: number;
  createdDate: string;
  segments?: Segment[];
  translatedSegments?: TranslatedSegment[];
  pdfGenerated?: boolean;
  pdfGeneratedDate?: string;
}

interface TranslationStore {
  files: TranslationFile[];
  addFile: (file: Omit<TranslationFile, 'id' | 'createdDate'>) => string;
  updateFileStatus: (id: string, status: FileStatus) => void;
  updateFileSegments: (id: string, segments: Segment[]) => void;
  updateFileTranslation: (id: string, translatedSegments: TranslatedSegment[], targetLanguage: string) => void;
  updatePdfGenerated: (id: string) => void;
  removeFile: (id: string) => void;
}

export const useTranslationStore = create<TranslationStore>((set) => ({
  files: [],
  addFile: (file) => {
    const id = Date.now().toString();
    set((state) => ({
      files: [
        ...state.files,
        {
          ...file,
          id,
          createdDate: new Date().toISOString().split('T')[0],
        },
      ],
    }));
    return id;
  },
  updateFileStatus: (id, status) =>
    set((state) => ({
      files: state.files.map((f) => (f.id === id ? { ...f, status } : f)),
    })),
  updateFileSegments: (id, segments) =>
    set((state) => ({
      files: state.files.map((f) => (f.id === id ? { ...f, segments } : f)),
    })),
  updateFileTranslation: (id, translatedSegments, targetLanguage) =>
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id 
          ? { ...f, translatedSegments, status: 'Completed' as FileStatus, targetLanguage } 
          : f
      ),
    })),
  updatePdfGenerated: (id) =>
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id 
          ? { ...f, pdfGenerated: true, pdfGeneratedDate: new Date().toISOString().split('T')[0] } 
          : f
      ),
    })),
  removeFile: (id) =>
    set((state) => ({
      files: state.files.filter((f) => f.id !== id),
    })),
}));
