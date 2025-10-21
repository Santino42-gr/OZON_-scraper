// Types для CRUD страниц

export interface Article {
  id: string;
  articleNumber: string;
  userId: string;
  userName: string;
  userInitials: string;
  createdAt: string;
  updatedAt: string;
  lastCheck: string | null;
  status: 'active' | 'inactive' | 'error';
  isProblematic: boolean;
  lastCheckData: Record<string, unknown> | null;
  spp1?: number | null;
  spp2?: number | null;
  spp_total?: number | null;
}

export interface User {
  id: string;
  telegramId: string;
  username: string;
  initials: string;
  createdAt: string;
  isBlocked: boolean;
  lastActiveAt: string;
  articlesCount: number;
  requestsCount: number;
}

export interface Log {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  eventType: string;
  message: string;
  userId?: string;
  userName?: string;
  userInitials?: string;
  articleId?: string;
  metadata?: Record<string, unknown>;
}

export interface PaginationData<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

