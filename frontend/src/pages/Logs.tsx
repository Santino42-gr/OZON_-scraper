import { useState, useCallback } from 'react';
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
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { logsApi } from '@/services/apiService';
import { Log } from '@/types/crud';
import { Search, ChevronLeft, ChevronRight, XCircle, AlertTriangle, Info, Eye } from 'lucide-react';

export default function Logs() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [selectedLog, setSelectedLog] = useState<Log | null>(null);

  // Debounced search
  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    const timer = setTimeout(() => setDebouncedSearch(value), 300);
    return () => clearTimeout(timer);
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ['logs', { page, pageSize, search: debouncedSearch, levelFilter }],
    queryFn: () => logsApi.getLogs({
      page,
      pageSize,
      level: levelFilter,
      search: debouncedSearch,
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
            onChange={(e) => handleSearchChange(e.target.value)}
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
              <TableHead className="w-[80px]">Детали</TableHead>
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
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSelectedLog(log)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
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

      {/* Log Details Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Badge variant={selectedLog ? getLevelBadge(selectedLog.level) : 'default'}>
                {selectedLog && getLevelLabel(selectedLog.level)}
              </Badge>
              {selectedLog?.eventType}
            </DialogTitle>
            <DialogDescription>
              {selectedLog && new Date(selectedLog.timestamp).toLocaleString('ru-RU')}
            </DialogDescription>
          </DialogHeader>

          {selectedLog && (
            <div className="space-y-4">
              <div>
                <Label>Сообщение</Label>
                <p className="mt-1 text-sm">{selectedLog.message}</p>
              </div>

              {selectedLog.userName && (
                <div>
                  <Label>Пользователь</Label>
                  <div className="mt-1 flex items-center gap-2">
                    <Avatar>
                      <AvatarFallback>{selectedLog.userInitials}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{selectedLog.userName}</p>
                      {selectedLog.userId && (
                        <p className="text-sm text-muted-foreground">ID: {selectedLog.userId}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {selectedLog.articleId && (
                <div>
                  <Label>Артикул</Label>
                  <p className="mt-1 font-mono">{selectedLog.articleId}</p>
                </div>
              )}

              {selectedLog.metadata && (
                <div>
                  <Label>Метаданные</Label>
                  <pre className="mt-1 bg-muted p-4 rounded-md text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
