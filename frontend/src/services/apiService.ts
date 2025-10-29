import axios, { AxiosInstance } from 'axios';
import {
  DashboardStats,
  ActivityDataPoint,
  RequestsDataPoint,
  LogEntry,
} from '@/types/dashboard.ts';
import { Article, User, Log, PaginationData } from '@/types/crud.ts';

// Создаем axios instance с базовым URL
const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

// ==================== Dashboard API ====================

export const dashboardApi = {
  async getStats(): Promise<DashboardStats> {
    const { data } = await apiClient.get('/stats/dashboard');
    return {
      users: {
        total: data.users.total,
        activeToday: data.users.active,
        weeklyChange: 0, // TODO: Backend должен возвращать это
      },
      articles: {
        total: data.articles.total,
        addedThisWeek: 0, // TODO: Backend должен возвращать это
        weeklyChange: 0,
      },
      requests: {
        total: data.activity.total_requests_24h,
        successful: data.activity.total_requests_24h - data.activity.errors_24h,
        failed: data.activity.errors_24h,
        successRate: data.activity.success_rate,
      },
      parsing: {
        successRate: data.activity.success_rate,
        last24h: data.activity.total_requests_24h,
        trend: 0,
      },
    };
  },

  async getActivityData(): Promise<ActivityDataPoint[]> {
    // TODO: Добавить endpoint в Backend для activity data
    // Временно возвращаем пустой массив
    return [];
  },

  async getRequestsData(): Promise<RequestsDataPoint[]> {
    // TODO: Добавить endpoint в Backend для requests data
    // Временно возвращаем пустой массив
    return [];
  },

  async getRecentLogs(): Promise<LogEntry[]> {
    const { data } = await apiClient.get('/logs', {
      params: { limit: 10 },
    });

    return data.items.map((log: any) => ({
      id: log.id,
      level: log.level as LogEntry['level'],
      message: log.message,
      timestamp: log.created_at,
      userName: log.user_name,
      userId: log.user_id,
    }));
  },
};

// ==================== Articles CRUD API ====================

export const articlesApi = {
  async getArticles(params: {
    page: number;
    pageSize: number;
    search?: string;
    status?: string;
    userId?: string;
  }): Promise<PaginationData<Article>> {
    const { data } = await apiClient.get('/articles', {
      params: {
        skip: (params.page - 1) * params.pageSize,
        limit: params.pageSize,
        search: params.search,
        status: params.status !== 'all' ? params.status : undefined,
        user_id: params.userId,
      },
    });

    return {
      data: data.items.map((item: any) => ({
        id: item.id,
        articleNumber: item.article_number,
        userId: item.user_id,
        userName: item.user?.username || 'Unknown',
        userInitials: item.user?.username?.split(' ').map((n: string) => n[0]).join('') || '??',
        createdAt: item.created_at,
        updatedAt: item.updated_at,
        lastCheck: item.last_checked_at,
        status: item.status || 'active',
        isProblematic: item.status === 'error',
        lastCheckData: item.last_price ? { price: item.last_price, stock: item.stock } : null,
      })),
      total: data.total,
      page: params.page,
      pageSize: params.pageSize,
      totalPages: Math.ceil(data.total / params.pageSize),
    };
  },

  async getArticleById(id: string): Promise<Article | null> {
    try {
      const { data } = await apiClient.get(`/articles/${id}`);
      return {
        id: data.id,
        articleNumber: data.article_number,
        userId: data.user_id,
        userName: data.user?.username || 'Unknown',
        userInitials: data.user?.username?.split(' ').map((n: string) => n[0]).join('') || '??',
        createdAt: data.created_at,
        updatedAt: data.updated_at,
        lastCheck: data.last_checked_at,
        status: data.status || 'active',
        isProblematic: data.status === 'error',
        lastCheckData: data.last_price ? { price: data.last_price, stock: data.stock } : null,
      };
    } catch (error) {
      return null;
    }
  },

  async deleteArticle(id: string): Promise<void> {
    await apiClient.delete(`/articles/${id}`);
  },

  async updateArticle(id: string, updates: Partial<Article>): Promise<Article> {
    const { data } = await apiClient.put(`/articles/${id}`, updates);
    return data;
  },

  async updateArticleStatus(id: string, status: Article['status']): Promise<Article> {
    const { data } = await apiClient.patch(`/articles/${id}`, { status });
    return data;
  },

  async deleteMultipleArticles(ids: string[]): Promise<void> {
    await Promise.all(ids.map((id) => apiClient.delete(`/articles/${id}`)));
  },

  async exportArticles(filters: {
    search?: string;
    status?: string;
    userId?: string;
  }): Promise<string> {
    const { data } = await apiClient.get('/articles/export', {
      params: filters,
      responseType: 'text',
    });
    return data;
  },
};

// ==================== Users CRUD API ====================

export const usersApi = {
  async getUsers(params: {
    page: number;
    pageSize: number;
    search?: string;
  }): Promise<PaginationData<User>> {
    const { data } = await apiClient.get('/users', {
      params: {
        skip: (params.page - 1) * params.pageSize,
        limit: params.pageSize,
        search: params.search,
      },
    });

    return {
      data: data.items.map((item: any) => ({
        id: item.id,
        telegramId: item.telegram_id,
        username: item.telegram_username || item.username,
        initials: item.telegram_username?.split(' ').map((n: string) => n[0]).join('') || '??',
        createdAt: item.created_at,
        isBlocked: item.is_blocked || false,
        lastActiveAt: item.last_active_at,
        articlesCount: item.articles_count || 0,
        requestsCount: item.requests_count || 0,
      })),
      total: data.total,
      page: params.page,
      pageSize: params.pageSize,
      totalPages: Math.ceil(data.total / params.pageSize),
    };
  },

  async getUserById(id: string): Promise<User | null> {
    try {
      const { data } = await apiClient.get(`/users/${id}`);
      return {
        id: data.id,
        telegramId: data.telegram_id,
        username: data.telegram_username || data.username,
        initials: data.telegram_username?.split(' ').map((n: string) => n[0]).join('') || '??',
        createdAt: data.created_at,
        isBlocked: data.is_blocked || false,
        lastActiveAt: data.last_active_at,
        articlesCount: data.articles_count || 0,
        requestsCount: data.requests_count || 0,
      };
    } catch (error) {
      return null;
    }
  },

  async toggleUserBlock(id: string): Promise<User> {
    const { data } = await apiClient.patch(`/users/${id}/block`);
    return data;
  },

  async getUserArticles(userId: string): Promise<Article[]> {
    const { data } = await apiClient.get(`/users/${userId}/articles`);
    return data.items;
  },
};

// ==================== Logs API ====================

export const logsApi = {
  async getLogs(params: {
    page: number;
    pageSize: number;
    level?: string;
    search?: string;
  }): Promise<PaginationData<Log>> {
    const { data } = await apiClient.get('/logs', {
      params: {
        skip: (params.page - 1) * params.pageSize,
        limit: params.pageSize,
        level: params.level !== 'all' ? params.level : undefined,
        search: params.search,
      },
    });

    return {
      data: data.items.map((item: any) => ({
        id: item.id,
        timestamp: item.created_at,
        level: item.level as Log['level'],
        eventType: item.event_type,
        message: item.message,
        userId: item.user_id,
        userName: item.user_name,
        userInitials: item.user_name?.split(' ').map((n: string) => n[0]).join(''),
        articleId: item.article_id,
        metadata: item.metadata,
      })),
      total: data.total,
      page: params.page,
      pageSize: params.pageSize,
      totalPages: Math.ceil(data.total / params.pageSize),
    };
  },

  async getLogById(id: string): Promise<Log | null> {
    try {
      const { data } = await apiClient.get(`/logs/${id}`);
      return {
        id: data.id,
        timestamp: data.created_at,
        level: data.level,
        eventType: data.event_type,
        message: data.message,
        userId: data.user_id,
        userName: data.user_name,
        userInitials: data.user_name?.split(' ').map((n: string) => n[0]).join(''),
        articleId: data.article_id,
        metadata: data.metadata,
      };
    } catch (error) {
      return null;
    }
  },
};

export default {
  dashboard: dashboardApi,
  articles: articlesApi,
  users: usersApi,
  logs: logsApi,
};
