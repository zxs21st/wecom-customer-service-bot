// --- Auth ---
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// --- Analytics ---
export interface DashboardStats {
  total_consultations: number;
  resolved: number;
  escalated: number;
  avg_confidence: number;
  resolution_rate: number;
  today_consultations: number;
}

export interface DailyStat {
  stat_date: string;
  total_queries: number;
  resolved_queries: number;
  escalated_queries: number;
  avg_confidence: number;
}

export interface ConsultationRecord {
  id: string;
  question: string;
  answer: string;
  intent_type: string;
  confidence: number;
  is_resolved: boolean;
  session_id: string;
  created_at: string;
}

// --- Knowledge ---
export interface KnowledgeDocument {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  is_active: boolean;
  created_at: string;
}

export interface KnowledgeDocumentCreate {
  title: string;
  content: string;
  category: string;
  tags?: string[];
}

export interface KnowledgeSearchResult {
  id: string;
  title: string;
  content: string;
  category: string;
  similarity: number;
}

// --- Quotes ---
export interface Quote {
  id: string;
  quote_number: string;
  customer_name: string;
  customer_contact: string;
  total_amount: number;
  status: string;
  valid_until: string;
  created_at: string;
}

export interface QuoteItem {
  product_name: string;
  quantity: number;
  unit_price: number;
  discount: number;
}

// --- After Sales ---
export interface AfterSalesTicket {
  id: string;
  ticket_number: string;
  customer_name: string;
  issue_type: string;
  description: string;
  status: string;
  priority: string;
  created_at: string;
}

export interface Order {
  id: string;
  order_number: string;
  customer_name: string;
  total_amount: number;
  status: string;
  created_at: string;
}
