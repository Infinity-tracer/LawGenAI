

export interface User {
  fullName: string;
  email: string;
  phone: string;
  passwordHash: string;
}

export interface LawComparison {
  old_law: string;
  old_section: string;
  old_title: string;
  new_law: string;
  new_section: string;
  new_title: string;
  changes: string;
  original_text?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type?: 'text' | 'cases' | 'comparisons';
  cases?: CaseResult[];
  law_comparisons?: LawComparison[];
}

export interface CaseResult {
  title: string;
  doc_id: string;
  snippet: string;
  case_link: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  folder?: string;
}

export enum View {
  LANDING = 'LANDING',
  AUTH = 'AUTH',
  CHAT = 'CHAT'
}

export enum ChatMode {
  PDF_CHAT = 'PDF_CHAT',
  KANOON_SEARCH = 'KANOON_SEARCH',
  LAW_COMPARISON = 'LAW_COMPARISON'
}
