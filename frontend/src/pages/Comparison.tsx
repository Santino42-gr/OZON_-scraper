/**
 * Comparison Page
 * Main page for article comparison functionality
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Scale,
  RefreshCw,
  AlertCircle,
  TrendingUp,
  BarChart3,
} from 'lucide-react';
import { ComparisonCard } from '@/components/comparison/ComparisonCard';
import { ComparisonMetrics } from '@/components/comparison/ComparisonMetrics';
import { QuickCompareDialog } from '@/components/comparison/QuickCompareDialog';
import { ComparisonHistoryChart } from '@/components/comparison/ComparisonHistoryChart';
import {
  comparisonApi,
  ComparisonResponse,
  ComparisonHistoryResponse,
  UserComparisonStats,
} from '@/services/comparisonService';
import { StatsCard } from '@/components/dashboard/StatsCard';

// Mock user ID - в реальном приложении берем из контекста/auth
const MOCK_USER_ID = '123e4567-e89b-12d3-a456-426614174000';

export const Comparison: React.FC = () => {
  const [activeComparison, setActiveComparison] = useState<ComparisonResponse | null>(null);
  const [history, setHistory] = useState<ComparisonHistoryResponse | null>(null);
  const [stats, setStats] = useState<UserComparisonStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load user stats on mount
  useEffect(() => {
    loadUserStats();
  }, []);

  const loadUserStats = async () => {
    try {
      const data = await comparisonApi.getUserStats(MOCK_USER_ID);
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleQuickCompareSuccess = async (comparison: ComparisonResponse) => {
    setActiveComparison(comparison);
    loadUserStats();

    // Load history if available
    if (comparison.group_id) {
      loadHistory(comparison.group_id);
    }
  };

  const handleRefresh = async () => {
    if (!activeComparison) return;

    setLoading(true);
    setError(null);

    try {
      const refreshed = await comparisonApi.getComparison(
        activeComparison.group_id,
        MOCK_USER_ID,
        true // refresh = true
      );
      setActiveComparison(refreshed);

      // Reload history
      loadHistory(activeComparison.group_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при обновлении данных');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async (groupId: string, days: number = 30) => {
    setHistoryLoading(true);
    try {
      const data = await comparisonApi.getHistory(groupId, MOCK_USER_ID, days);
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Сравнение товаров</h1>
          <p className="text-muted-foreground mt-1">
            Сравнивайте свои товары с конкурентами и отслеживайте конкурентоспособность
          </p>
        </div>
        <QuickCompareDialog
          userId={MOCK_USER_ID}
          onSuccess={handleQuickCompareSuccess}
        />
      </div>

      {/* User Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatsCard
            title="Всего групп"
            value={stats.total_groups}
            icon={Scale}
            subtitle="Групп сравнения"
          />
          <StatsCard
            title="Товаров в сравнении"
            value={stats.total_articles}
            icon={BarChart3}
            subtitle="Активных артикулов"
          />
          <StatsCard
            title="Средний индекс"
            value={stats.avg_competitiveness_index ? `${(stats.avg_competitiveness_index * 100).toFixed(0)}%` : '—'}
            icon={TrendingUp}
            subtitle="Конкурентоспособность"
          />
          <StatsCard
            title="Последнее сравнение"
            value={stats.last_comparison_date
              ? new Date(stats.last_comparison_date).toLocaleDateString('ru-RU')
              : '—'
            }
            icon={Scale}
            subtitle="Дата"
          />
        </div>
      )}

      {/* Main Content */}
      {!activeComparison ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Scale className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Начните сравнение</h3>
            <p className="text-muted-foreground text-center max-w-md mb-6">
              Нажмите кнопку "Быстрое сравнение" чтобы сравнить ваш товар с конкурентом.
              Система автоматически рассчитает все метрики.
            </p>
            <QuickCompareDialog
              userId={MOCK_USER_ID}
              onSuccess={handleQuickCompareSuccess}
            />
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue="comparison" className="space-y-4">
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="comparison">Сравнение</TabsTrigger>
              <TabsTrigger value="history">История</TabsTrigger>
            </TabsList>

            <div className="flex items-center gap-2">
              {!activeComparison.is_fresh && (
                <Alert variant="destructive" className="py-2 px-3">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    Данные устарели (&gt; 1 часа)
                  </AlertDescription>
                </Alert>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loading}
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Обновить
              </Button>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <TabsContent value="comparison" className="space-y-6">
            {/* Group Info */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{activeComparison.group_name || 'Сравнение'}</CardTitle>
                  <div className="text-sm text-muted-foreground">
                    {new Date(activeComparison.compared_at).toLocaleString('ru-RU')}
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Article Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Own Product */}
              {activeComparison.own_product && (
                <ComparisonCard
                  article={activeComparison.own_product}
                  isOwn={true}
                />
              )}

              {/* Competitor */}
              {activeComparison.competitors.map((competitor) => (
                <ComparisonCard
                  key={competitor.article_id}
                  article={competitor}
                  isOwn={false}
                />
              ))}
            </div>

            {/* Metrics */}
            {activeComparison.metrics && (
              <ComparisonMetrics metrics={activeComparison.metrics} />
            )}

            {/* No metrics warning */}
            {!activeComparison.metrics && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Метрики доступны только для сравнения 1v1 (ваш товар vs 1 конкурент)
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            {history ? (
              <ComparisonHistoryChart
                history={history}
                loading={historyLoading}
              />
            ) : (
              <Card>
                <CardContent className="py-16">
                  <div className="text-center">
                    {historyLoading ? (
                      <Skeleton className="h-[300px] w-full" />
                    ) : (
                      <>
                        <TrendingUp className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                        <p className="text-muted-foreground">
                          Загрузка истории...
                        </p>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};
