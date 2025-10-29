import {
  DashboardStats,
  ActivityDataPoint,
  RequestsDataPoint,
  LogEntry,
} from '@/types/dashboard.ts';

// Генерация mock данных для Dashboard
export const mockDashboardService = {
  async getStats(): Promise<DashboardStats> {
    // Имитация задержки сети
    await new Promise((resolve) => setTimeout(resolve, 500));

    return {
      users: {
        total: 1234,
        activeToday: 234,
        weeklyChange: 15.3,
      },
      articles: {
        total: 5678,
        addedThisWeek: 143,
        weeklyChange: 8.2,
      },
      requests: {
        total: 12567,
        successful: 11892,
        failed: 675,
        successRate: 94.6,
      },
      parsing: {
        successRate: 96.3,
        last24h: 2456,
        trend: 3.8,
      },
    };
  },

  async getActivityData(): Promise<ActivityDataPoint[]> {
    await new Promise((resolve) => setTimeout(resolve, 600));

    const data: ActivityDataPoint[] = [];
    const today = new Date();

    for (let i = 29; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);

      data.push({
        date: date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' }),
        users: Math.floor(Math.random() * 100) + 150,
      });
    }

    return data;
  },

  async getRequestsData(): Promise<RequestsDataPoint[]> {
    await new Promise((resolve) => setTimeout(resolve, 600));

    const data: RequestsDataPoint[] = [];
    const today = new Date();

    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);

      const successful = Math.floor(Math.random() * 500) + 1500;
      const failed = Math.floor(Math.random() * 50) + 20;

      data.push({
        date: date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' }),
        successful,
        failed,
      });
    }

    return data;
  },

  async getRecentLogs(): Promise<LogEntry[]> {
    await new Promise((resolve) => setTimeout(resolve, 400));

    const levels: LogEntry['level'][] = ['info', 'warning', 'error', 'critical'];
    const messages = [
      'Новый пользователь зарегистрирован',
      'Артикул добавлен в систему',
      'Ошибка при парсинге данных OZON',
      'Превышен лимит запросов',
      'Успешная проверка артикула',
      'Обновление данных завершено',
      'Критическая ошибка подключения',
      'Артикул удален из системы',
      'Пользователь заблокирован',
      'Массовая проверка артикулов завершена',
    ];
    const users = [
      'Иван Иванов',
      'Петр Петров',
      'Мария Сидорова',
      'Анна Козлова',
      undefined,
    ];

    const logs: LogEntry[] = [];
    const now = new Date();

    for (let i = 0; i < 10; i++) {
      const timestamp = new Date(now);
      timestamp.setMinutes(timestamp.getMinutes() - i * 15);

      logs.push({
        id: `log-${i}`,
        level: levels[Math.floor(Math.random() * levels.length)],
        message: messages[Math.floor(Math.random() * messages.length)],
        timestamp: timestamp.toISOString(),
        userName: users[Math.floor(Math.random() * users.length)],
        userId: Math.random() > 0.5 ? `user-${i}` : undefined,
      });
    }

    return logs;
  },
};

