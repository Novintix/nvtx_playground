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
}

interface TranslationStore {
  files: TranslationFile[];
  addFile: (file: Omit<TranslationFile, 'id' | 'createdDate'>) => void;
  updateFileStatus: (id: string, status: FileStatus) => void;
  updateFileSegments: (id: string, segments: Segment[]) => void;
  updateFileTranslation: (id: string, translatedSegments: TranslatedSegment[]) => void;
  removeFile: (id: string) => void;
}

export const useTranslationStore = create<TranslationStore>((set) => ({
  files: [],
  addFile: (file) =>
    set((state) => ({
      files: [
        ...state.files,
        {
          ...file,
          id: Date.now().toString(),
          createdDate: new Date().toISOString().split('T')[0],
        },
      ],
    })),
  updateFileStatus: (id, status) =>
    set((state) => ({
      files: state.files.map((f) => (f.id === id ? { ...f, status } : f)),
    })),
  updateFileSegments: (id, segments) =>
    set((state) => ({
      files: state.files.map((f) => (f.id === id ? { ...f, segments } : f)),
    })),
  updateFileTranslation: (id, translatedSegments) =>
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id ? { ...f, translatedSegments, status: 'Completed' as FileStatus } : f
      ),
    })),
  removeFile: (id) =>
    set((state) => ({
      files: state.files.filter((f) => f.id !== id),
    })),
}));
