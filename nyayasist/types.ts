
export interface User {
  fullName: string;
  email: string;
  phone: string;
  passwordHash: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type?: 'text' | 'cases';  // For rendering different message types
  cases?: CaseResult[];     // For Kanoon search results
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
  KANOON_SEARCH = 'KANOON_SEARCH'
}
