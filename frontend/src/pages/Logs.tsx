import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { mockCrudService } from '@/services/mockCrudService';
import { Search, ChevronLeft, ChevronRight, XCircle, AlertTriangle, Info } from 'lucide-react';

export default function Logs() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');

  const { data, isLoading } = useQuery({
    queryKey: ['logs', { page, pageSize, search, levelFilter }],
    queryFn: () => mockCrudService.getLogs({
      page,
      pageSize,
      level: levelFilter,
      search,
    }),
  });

  const getLevelBadge = (level: string) => {
    const variants = {
      info: 'default' as const,
      warning: 'secondary' as const,
      error: 'destructive' as const,
      critical: 'destructive' as const,
    };
    return variants[level as keyof typeof variants] || 'default';
  };

  const getLevelLabel = (level: string) => {
    const labels = {
      info: 'Инфо',
      warning: 'Внимание',
      error: 'Ошибка',
      critical: 'Критично',
    };
    return labels[level as keyof typeof labels] || level;
  };

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6 p-4 md:p-8">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-[500px] w-full" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Логи системы</h1>
        <p className="text-muted-foreground">
          Просмотр системных событий и ошибок
        </p>
      </div>

      <div className="flex flex-col gap-4">
        <Tabs value={levelFilter} onValueChange={setLevelFilter}>
          <TabsList>
            <TabsTrigger value="all">Все</TabsTrigger>
            <TabsTrigger value="error">
              <XCircle className="mr-2 h-4 w-4" />
              Ошибки
            </TabsTrigger>
            <TabsTrigger value="warning">
              <AlertTriangle className="mr-2 h-4 w-4" />
              Предупреждения
            </TabsTrigger>
            <TabsTrigger value="info">
              <Info className="mr-2 h-4 w-4" />
              Информация
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="relative max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Поиск в логах..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[180px]">Время</TableHead>
              <TableHead className="w-[100px]">Уровень</TableHead>
              <TableHead>Сообщение</TableHead>
              <TableHead className="w-[150px]">Пользователь</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.data.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="font-mono text-xs">
                  {new Date(log.timestamp).toLocaleString('ru-RU')}
                </TableCell>
                <TableCell>
                  <Badge variant={getLevelBadge(log.level)}>
                    {getLevelLabel(log.level)}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-[500px] truncate">
                  {log.message}
                </TableCell>
                <TableCell>
                  {log.userName ? (
                    <div className="flex items-center gap-2">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback className="text-xs">
                          {log.userInitials}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm">{log.userName}</span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground text-sm">Система</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Показано {Math.min((page - 1) * pageSize + 1, data.total)}-
            {Math.min(page * pageSize, data.total)} из {data.total}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Назад
            </Button>
            <span className="text-sm">
              Страница {page} из {data.totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page === data.totalPages}
            >
              Вперед
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

