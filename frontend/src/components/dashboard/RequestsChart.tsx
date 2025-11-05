import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from 'recharts';
import { RequestsDataPoint } from '@/types/dashboard';

interface RequestsChartProps {
  data: RequestsDataPoint[];
}

export const RequestsChart: React.FC<RequestsChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Запросы к OZON</CardTitle>
          <CardDescription>Успешные vs Ошибочные</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            <p>Данные пока недоступны</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Запросы к OZON</CardTitle>
        <CardDescription>Успешные vs Ошибочные</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <XAxis
              dataKey="date"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
              }}
            />
            <Bar
              dataKey="successful"
              fill="hsl(142 76% 36%)"
              radius={[4, 4, 0, 0]}
              name="Успешные"
            />
            <Bar
              dataKey="failed"
              fill="hsl(0 84% 60%)"
              radius={[4, 4, 0, 0]}
              name="Ошибочные"
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

