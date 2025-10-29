import { Article, User, Log, PaginationData } from '@/types/crud.ts';

// Mock данные для CRUD операций
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Генераторы mock данных
const generateArticles = (count: number): Article[] => {
  const articles: Article[] = [];
  const statuses: Article['status'][] = ['active', 'inactive', 'error'];
  const users = ['Иван Иванов', 'Петр Петров', 'Мария Сидорова', 'Анна Козлова'];

  for (let i = 0; i < count; i++) {
    const userName = users[i % users.length];
    articles.push({
      id: `article-${i + 1}`,
      articleNumber: `ART-${100000 + i}`,
      userId: `user-${(i % 4) + 1}`,
      userName,
      userInitials: userName.split(' ').map(n => n[0]).join(''),
      createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date().toISOString(),
      lastCheck: Math.random() > 0.3 ? new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000).toISOString() : null,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      isProblematic: Math.random() > 0.8,
      lastCheckData: Math.random() > 0.5 ? { price: Math.floor(Math.random() * 10000), stock: Math.floor(Math.random() * 100) } : null,
    });
  }
  return articles;
};

const generateUsers = (count: number): User[] => {
  const users: User[] = [];
  const names = ['Иван Иванов', 'Петр Петров', 'Мария Сидорова', 'Анна Козлова', 'Сергей Сергеев'];

  for (let i = 0; i < count; i++) {
    const username = names[i % names.length];
    users.push({
      id: `user-${i + 1}`,
      telegramId: `${100000000 + i}`,
      username,
      initials: username.split(' ').map(n => n[0]).join(''),
      createdAt: new Date(Date.now() - Math.random() * 60 * 24 * 60 * 60 * 1000).toISOString(),
      isBlocked: Math.random() > 0.9,
      lastActiveAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      articlesCount: Math.floor(Math.random() * 50),
      requestsCount: Math.floor(Math.random() * 200),
    });
  }
  return users;
};

const generateLogs = (count: number): Log[] => {
  const logs: Log[] = [];
  const levels: Log['level'][] = ['info', 'warning', 'error', 'critical'];
  const events = ['user_login', 'article_added', 'scraping_error', 'api_call', 'user_blocked'];
  const messages = [
    'Пользователь успешно вошел в систему',
    'Добавлен новый артикул',
    'Ошибка при парсинге данных OZON',
    'Выполнен API запрос',
    'Пользователь заблокирован',
  ];
  const users = ['Иван Иванов', 'Петр Петров', 'Мария Сидорова'];

  for (let i = 0; i < count; i++) {
    const userName = Math.random() > 0.3 ? users[i % users.length] : undefined;
    logs.push({
      id: `log-${i + 1}`,
      timestamp: new Date(Date.now() - i * 15 * 60 * 1000).toISOString(),
      level: levels[Math.floor(Math.random() * levels.length)],
      eventType: events[Math.floor(Math.random() * events.length)],
      message: messages[Math.floor(Math.random() * messages.length)],
      userId: userName ? `user-${(i % 3) + 1}` : undefined,
      userName,
      userInitials: userName?.split(' ').map(n => n[0]).join(''),
      articleId: Math.random() > 0.5 ? `article-${Math.floor(Math.random() * 50) + 1}` : undefined,
      metadata: Math.random() > 0.5 ? { ip: '192.168.1.1', duration: Math.floor(Math.random() * 1000) } : undefined,
    });
  }
  return logs;
};

// Mock хранилище
let articlesData = generateArticles(50);
let usersData = generateUsers(20);
let logsData = generateLogs(100);

export const mockCrudService = {
  // Articles
  async getArticles(params: {
    page: number;
    pageSize: number;
    search?: string;
    status?: string;
    userId?: string;
  }): Promise<PaginationData<Article>> {
    await delay(500);

    let filtered = [...articlesData];

    if (params.search) {
      filtered = filtered.filter(a => 
        a.articleNumber.toLowerCase().includes(params.search!.toLowerCase())
      );
    }

    if (params.status && params.status !== 'all') {
      filtered = filtered.filter(a => a.status === params.status);
    }

    if (params.userId) {
      filtered = filtered.filter(a => a.userId === params.userId);
    }

    const start = (params.page - 1) * params.pageSize;
    const end = start + params.pageSize;
    const paginatedData = filtered.slice(start, end);

    return {
      data: paginatedData,
      total: filtered.length,
      page: params.page,
      pageSize: params.pageSize,
      totalPages: Math.ceil(filtered.length / params.pageSize),
    };
  },

  async deleteArticle(id: string): Promise<void> {
    await delay(300);
    articlesData = articlesData.filter(a => a.id !== id);
  },

  async getArticleById(id: string): Promise<Article | null> {
    await delay(300);
    return articlesData.find(a => a.id === id) || null;
  },

  async updateArticle(id: string, data: Partial<Article>): Promise<Article> {
    await delay(300);
    const article = articlesData.find(a => a.id === id);
    if (article) {
      Object.assign(article, data);
      article.updatedAt = new Date().toISOString();
    }
    return article!;
  },

  async updateArticleStatus(id: string, status: Article['status']): Promise<Article> {
    await delay(300);
    const article = articlesData.find(a => a.id === id);
    if (article) {
      article.status = status;
      article.updatedAt = new Date().toISOString();
    }
    return article!;
  },

  async deleteMultipleArticles(ids: string[]): Promise<void> {
    await delay(500);
    articlesData = articlesData.filter(a => !ids.includes(a.id));
  },

  async exportArticles(filters: {
    search?: string;
    status?: string;
    userId?: string;
  }): Promise<string> {
    await delay(300);
    let filtered = [...articlesData];

    if (filters.search) {
      filtered = filtered.filter(a => 
        a.articleNumber.toLowerCase().includes(filters.search!.toLowerCase())
      );
    }

    if (filters.status && filters.status !== 'all') {
      filtered = filtered.filter(a => a.status === filters.status);
    }

    if (filters.userId) {
      filtered = filtered.filter(a => a.userId === filters.userId);
    }

    // Generate CSV
    const headers = ['Артикул', 'Пользователь', 'Дата создания', 'Последняя проверка', 'Статус'];
    const rows = filtered.map(a => [
      a.articleNumber,
      a.userName,
      new Date(a.createdAt).toLocaleDateString('ru-RU'),
      a.lastCheck ? new Date(a.lastCheck).toLocaleDateString('ru-RU') : 'Никогда',
      a.status,
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    return csv;
  },

  // Users
  async getUsers(params: {
    page: number;
    pageSize: number;
    search?: string;
  }): Promise<PaginationData<User>> {
    await delay(500);

    let filtered = [...usersData];

    if (params.search) {
      filtered = filtered.filter(u => 
        u.username.toLowerCase().includes(params.search!.toLowerCase()) ||
        u.telegramId.includes(params.search!)
      );
    }

    const start = (params.page - 1) * params.pageSize;
    const end = start + params.pageSize;
    const paginatedData = filtered.slice(start, end);

    return {
      data: paginatedData,
      total: filtered.length,
      page: params.page,
      pageSize: params.pageSize,
      totalPages: Math.ceil(filtered.length / params.pageSize),
    };
  },

  async getUserById(id: string): Promise<User | null> {
    await delay(300);
    return usersData.find(u => u.id === id) || null;
  },

  async toggleUserBlock(id: string): Promise<User> {
    await delay(300);
    const user = usersData.find(u => u.id === id);
    if (user) {
      user.isBlocked = !user.isBlocked;
    }
    return user!;
  },

  async getUserArticles(userId: string): Promise<Article[]> {
    await delay(400);
    return articlesData.filter(a => a.userId === userId);
  },

  // Logs
  async getLogs(params: {
    page: number;
    pageSize: number;
    level?: string;
    search?: string;
  }): Promise<PaginationData<Log>> {
    await delay(500);

    let filtered = [...logsData];

    if (params.level && params.level !== 'all') {
      filtered = filtered.filter(l => l.level === params.level);
    }

    if (params.search) {
      filtered = filtered.filter(l => 
        l.message.toLowerCase().includes(params.search!.toLowerCase())
      );
    }

    const start = (params.page - 1) * params.pageSize;
    const end = start + params.pageSize;
    const paginatedData = filtered.slice(start, end);

    return {
      data: paginatedData,
      total: filtered.length,
      page: params.page,
      pageSize: params.pageSize,
      totalPages: Math.ceil(filtered.length / params.pageSize),
    };
  },

  async getLogById(id: string): Promise<Log | null> {
    await delay(300);
    return logsData.find(l => l.id === id) || null;
  },
};

