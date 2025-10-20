export interface DashboardStats {
  users: {
    total: number;
    activeToday: number;
    weeklyChange: number;
  };
  articles: {
    total: number;
    addedThisWeek: number;
    weeklyChange: number;
  };
  requests: {
    total: number;
    successful: number;
    failed: number;
    successRate: number;
  };
  parsing: {
    successRate: number;
    last24h: number;
    trend: number;
  };
}

export interface ActivityDataPoint {
  date: string;
  users: number;
}

export interface RequestsDataPoint {
  date: string;
  successful: number;
  failed: number;
}

export interface LogEntry {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
  userId?: string;
  userName?: string;
  articleId?: string;
  metadata?: Record<string, unknown>;
}

export interface Alert {
  id: string;
  type: 'destructive' | 'warning' | 'default';
  title: string;
  description: string;
  timestamp: string;
}

