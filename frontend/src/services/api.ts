import axios from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  DashboardStats,
  DailyStat,
  ConsultationRecord,
  KnowledgeDocument,
  KnowledgeDocumentCreate,
  Quote,
  AfterSalesTicket,
  Order,
} from './types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// JWT interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Auth ---
export const login = (data: LoginRequest) =>
  api.post<LoginResponse>('/auth/login', data);

// --- Analytics ---
export const getDashboardStats = () =>
  api.get<DashboardStats>('/analytics/dashboard');

export const getDailyTrends = (days = 30) =>
  api.get<DailyStat[]>('/analytics/daily', { params: { days } });

export const getConsultationRecords = (page = 1, pageSize = 20) =>
  api.get<ConsultationRecord[]>('/analytics/records', {
    params: { page, page_size: pageSize },
  });

// --- Knowledge ---
export const getKnowledgeDocuments = (page = 1, pageSize = 20) =>
  api.get<KnowledgeDocument[]>('/knowledge/documents', {
    params: { page, page_size: pageSize },
  });

export const createKnowledgeDocument = (data: KnowledgeDocumentCreate) =>
  api.post<KnowledgeDocument>('/knowledge/documents', data);

export const updateKnowledgeDocument = (id: string, data: Partial<KnowledgeDocumentCreate>) =>
  api.put<KnowledgeDocument>(`/knowledge/documents/${id}`, data);

export const deleteKnowledgeDocument = (id: string) =>
  api.delete(`/knowledge/documents/${id}`);

// --- Quotes ---
export const getQuotes = (page = 1, pageSize = 20) =>
  api.get<Quote[]>('/quoting/quotes', {
    params: { page, page_size: pageSize },
  });

// --- After Sales ---
export const getTickets = (page = 1, pageSize = 20) =>
  api.get<AfterSalesTicket[]>('/after-sales/tickets', {
    params: { page, page_size: pageSize },
  });

export const getOrders = (page = 1, pageSize = 20) =>
  api.get<Order[]>('/after-sales/orders', {
    params: { page, page_size: pageSize },
  });

export default api;
