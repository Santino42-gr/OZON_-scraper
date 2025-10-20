import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { mockCrudService } from '@/services/mockCrudService';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

export default function Users() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['users', { page, pageSize, search }],
    queryFn: () => mockCrudService.getUsers({ page, pageSize, search }),
  });

  const toggleBlockMutation = useMutation({
    mutationFn: mockCrudService.toggleUserBlock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success('Статус пользователя обновлен');
    },
  });

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
        <h1 className="text-3xl font-bold tracking-tight">Пользователи</h1>
        <p className="text-muted-foreground">
          Управление пользователями Telegram бота
        </p>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Поиск по имени или Telegram ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-8"
        />
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Пользователь</TableHead>
              <TableHead>Дата регистрации</TableHead>
              <TableHead>Артикулов</TableHead>
              <TableHead>Запросов</TableHead>
              <TableHead>Статус</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.data.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarFallback>{user.initials}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{user.username}</p>
                      <p className="text-sm text-muted-foreground">
                        ID: {user.telegramId}
                      </p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  {new Date(user.createdAt).toLocaleDateString('ru-RU')}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{user.articlesCount}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{user.requestsCount}</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={!user.isBlocked}
                      onCheckedChange={() => toggleBlockMutation.mutate(user.id)}
                    />
                    <span className="text-sm">
                      {user.isBlocked ? 'Заблокирован' : 'Активен'}
                    </span>
                  </div>
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

