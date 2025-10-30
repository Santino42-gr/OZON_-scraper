/**
 * ComparisonHistoryChart Component
 * Displays comparison history as a line chart
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, Calendar } from 'lucide-react';
import { ComparisonHistoryResponse } from '@/services/comparisonService';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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

  // Prepare chart data
  const chartData = history.snapshots
    .slice()
    .reverse() // Reverse to show chronological order
    .map((snapshot) => ({
      date: new Date(snapshot.snapshot_date).toLocaleDateString('ru-RU', {
        month: 'short',
        day: 'numeric',
      }),
      index: Math.round(snapshot.competitiveness_index * 100),
      timestamp: snapshot.snapshot_date,
    }));

  const currentIndex = history.snapshots[0]?.competitiveness_index;
  const previousIndex = history.snapshots[1]?.competitiveness_index;
  const trend = currentIndex && previousIndex ? currentIndex - previousIndex : null;

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
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickMargin={10}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-background border rounded-lg p-3 shadow-lg">
                      <p className="text-sm font-medium">{payload[0].payload.date}</p>
                      <p className="text-sm text-muted-foreground">
                        Индекс: <span className="font-semibold">{payload[0].value}%</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="index"
              name="Индекс конкурентоспособности"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t">
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">Минимум</p>
            <p className="text-lg font-semibold">
              {Math.min(...chartData.map(d => d.index))}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">Средний</p>
            <p className="text-lg font-semibold">
              {Math.round(chartData.reduce((sum, d) => sum + d.index, 0) / chartData.length)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">Максимум</p>
            <p className="text-lg font-semibold">
              {Math.max(...chartData.map(d => d.index))}%
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
