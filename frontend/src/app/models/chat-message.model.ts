export interface ChatSource {
  type: 'vector' | 'sql';
  detail: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  sources?: ChatSource[];
  isError?: boolean;
  timestamp: Date;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export interface UploadedFileSummary {
  filename: string;
  chunks_indexed: number;
  status: 'ok' | 'error';
  error?: string | null;
}

export interface UploadResponse {
  files: UploadedFileSummary[];
  total_chunks_indexed: number;
}
