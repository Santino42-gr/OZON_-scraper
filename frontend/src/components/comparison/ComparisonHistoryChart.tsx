/**
 * ComparisonHistoryChart Component
 * Displays comparison history as a simple list (no charts in MVP)
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, Calendar, ArrowUp, ArrowDown } from 'lucide-react';
import { ComparisonHistoryResponse } from '@/services/comparisonService';

interface ComparisonHistoryChartProps {
  history: ComparisonHistoryResponse;
  loading?: boolean;
}

export const ComparisonHistoryChart: React.FC<ComparisonHistoryChartProps> = ({
  history,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            История изменений
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!history.snapshots || history.snapshots.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            История изменений
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-[300px] text-center">
            <Calendar className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Нет данных за выбранный период
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              История начнет накапливаться после первого сравнения
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate stats
  const indices = history.snapshots.map(s => s.competitiveness_index * 100);
  const currentIndex = history.snapshots[0]?.competitiveness_index;
  const previousIndex = history.snapshots[1]?.competitiveness_index;
  const trend = currentIndex && previousIndex ? currentIndex - previousIndex : null;

  const minIndex = Math.min(...indices);
  const maxIndex = Math.max(...indices);
  const avgIndex = indices.reduce((sum, val) => sum + val, 0) / indices.length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            История изменений
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {history.total_count} снэпшот{history.total_count !== 1 ? 'ов' : ''}
            </Badge>
            {trend !== null && (
              <Badge variant={trend >= 0 ? 'default' : 'destructive'}>
                {trend >= 0 ? '+' : ''}{(trend * 100).toFixed(1)}%
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 border rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Минимум</p>
            <p className="text-2xl font-semibold">
              {minIndex.toFixed(0)}%
            </p>
          </div>
          <div className="text-center p-4 border rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Средний</p>
            <p className="text-2xl font-semibold">
              {avgIndex.toFixed(0)}%
            </p>
          </div>
          <div className="text-center p-4 border rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Максимум</p>
            <p className="text-2xl font-semibold">
              {maxIndex.toFixed(0)}%
            </p>
          </div>
        </div>

        {/* Snapshots List */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">Последние снэпшоты:</h4>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {history.snapshots.slice(0, 10).map((snapshot, index) => {
              const nextSnapshot = history.snapshots[index + 1];
              const change = nextSnapshot
                ? (snapshot.competitiveness_index - nextSnapshot.competitiveness_index) * 100
                : null;

              return (
                <div
                  key={snapshot.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-sm">
                      <p className="font-medium">
                        {new Date(snapshot.snapshot_date).toLocaleDateString('ru-RU', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(snapshot.snapshot_date).toLocaleTimeString('ru-RU', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {change !== null && (
                      <div className={`flex items-center gap-1 text-sm ${
                        change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {change > 0 ? (
                          <ArrowUp className="h-3 w-3" />
                        ) : change < 0 ? (
                          <ArrowDown className="h-3 w-3" />
                        ) : null}
                        {change !== 0 && (
                          <span className="font-mono text-xs">
                            {change > 0 ? '+' : ''}{change.toFixed(1)}%
                          </span>
                        )}
                      </div>
                    )}

                    <Badge variant="outline" className="font-mono">
                      {(snapshot.competitiveness_index * 100).toFixed(0)}%
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>

          {history.snapshots.length > 10 && (
            <p className="text-xs text-muted-foreground text-center pt-2">
              Показаны первые 10 из {history.snapshots.length} снэпшотов
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
