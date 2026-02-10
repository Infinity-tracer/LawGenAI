const API_BASE_URL = 'http://localhost:8000';

// ---------------------- TYPES ----------------------

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

export interface ChatResponse {
  answer: string;
  success: boolean;
  law_comparisons?: LawComparison[];
}

export interface CaseResult {
  title: string;
  doc_id: string;
  snippet: string;
  case_link: string;
}

export interface KanoonSearchResponse {
  cases: CaseResult[];
  total_found: number;
  success: boolean;
  law_comparisons?: LawComparison[];
}

export interface UploadResponse {
  message: string;
  chunks_processed: number;
  success: boolean;
}

export interface UserResponse {
  user_uuid: string;
  full_name: string;
  email: string;
  success: boolean;
}

export interface UserRegisterData {
  full_name: string;
  email: string;
  phone: string;
  password: string;
  otp: string;
}

export interface UserLoginData {
  email: string;
  password: string;
}

// ---------------------- USER API FUNCTIONS ----------------------

export async function sendVerificationOTP(email: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/users/send-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to send verification code');
  }

  return response.json();
}

export async function registerUser(userData: UserRegisterData): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/api/users/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to register user');
  }

  return response.json();
}

export async function loginUser(credentials: UserLoginData): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/api/users/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Invalid email or password');
  }

  return response.json();
}

// ---------------------- API FUNCTIONS ----------------------

export async function uploadPDF(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE_URL}/api/pdf/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload PDF');
  }

  return response.json();
}

export async function chatWithPDF(question: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/pdf/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get response');
  }

  return response.json();
}

export async function searchKanoon(query: string, page: number = 0): Promise<KanoonSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/kanoon/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, page }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to search cases');
  }

  return response.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// ---------------------- LAW COMPARISON API ----------------------

export interface LawCompareRequest {
  law_type: string;
  section: string;
}

export interface LawCompareResponse {
  success: boolean;
  comparison?: LawComparison;
  error?: string;
}

export async function compareLawSection(
  lawType: string,
  section: string
): Promise<LawCompareResponse> {
  const response = await fetch(`${API_BASE_URL}/api/law/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ law_type: lawType, section }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to compare law section');
  }

  return response.json();
}

export interface LawSectionsResponse {
  success: boolean;
  law_type: string;
  total_sections: number;
  sections: Array<{
    section: string;
    title: string;
    new_section: string;
    new_law: string;
  }>;
}

export async function getLawSections(lawType: string): Promise<LawSectionsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/law/sections/${lawType}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get law sections');
  }

  return response.json();
}
