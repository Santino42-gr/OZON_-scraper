import { useQuery } from '@tanstack/react-query';
import { Users, Package, Activity, TrendingUp } from 'lucide-react';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { ActivityChart } from '@/components/dashboard/ActivityChart';
import { RequestsChart } from '@/components/dashboard/RequestsChart';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { Skeleton } from '@/components/ui/skeleton';
import { dashboardApi } from '@/services/apiService';

const DashboardSkeleton = () => (
  <div className="flex flex-col gap-6 p-4 md:p-8">
    {/* Stats Cards Skeleton */}
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="rounded-lg border bg-card p-6">
          <Skeleton className="h-4 w-24 mb-4" />
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-4 w-40" />
        </div>
      ))}
    </div>

    {/* Charts Skeleton */}
    <div className="grid gap-4 md:grid-cols-2">
      <Skeleton className="h-[400px] rounded-lg" />
      <Skeleton className="h-[400px] rounded-lg" />
    </div>

    {/* Recent Activity Skeleton */}
    <Skeleton className="h-[500px] rounded-lg" />
  </div>
);

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
    refetchInterval: 30000, // автообновление каждые 30 сек
  });

  const { data: activityData, isLoading: activityLoading } = useQuery({
    queryKey: ['dashboard', 'activity'],
    queryFn: dashboardApi.getActivityData,
  });

  const { data: requestsData, isLoading: requestsLoading } = useQuery({
    queryKey: ['dashboard', 'requests'],
    queryFn: dashboardApi.getRequestsData,
  });

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ['dashboard', 'logs'],
    queryFn: dashboardApi.getRecentLogs,
    refetchInterval: 10000, // автообновление каждые 10 сек
  });

  const isLoading = statsLoading || activityLoading || requestsLoading || logsLoading;

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Панель управления</h1>
        <p className="text-muted-foreground">
          Обзор ключевых метрик и активности системы
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Пользователи"
          value={stats?.users.total.toLocaleString('ru-RU') || '0'}
          change={stats?.users.weeklyChange}
          subtitle={`Активных за сегодня: ${stats?.users.activeToday || 0}`}
          icon={Users}
        />
        <StatsCard
          title="Артикулы"
          value={stats?.articles.total.toLocaleString('ru-RU') || '0'}
          change={stats?.articles.weeklyChange}
          subtitle={`Добавлено за неделю: ${stats?.articles.addedThisWeek || 0}`}
          icon={Package}
        />
        <StatsCard
          title="Запросы"
          value={stats?.requests.total.toLocaleString('ru-RU') || '0'}
          subtitle={`Успешность: ${stats?.requests.successRate || 0}%`}
          icon={Activity}
        />
        <StatsCard
          title="Парсинг"
          value={`${stats?.parsing.successRate || 0}%`}
          change={stats?.parsing.trend}
          subtitle={`За 24ч: ${stats?.parsing.last24h.toLocaleString('ru-RU') || 0}`}
          icon={TrendingUp}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <ActivityChart data={activityData || []} />
        <RequestsChart data={requestsData || []} />
      </div>

      {/* Recent Activity */}
      <RecentActivity logs={logs || []} />
    </div>
  );
}

