import { useState, useCallback } from 'react';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { mockCrudService } from '@/services/mockCrudService';
import { User, Article } from '@/types/crud';
import { Search, ChevronLeft, ChevronRight, MoreHorizontal, Package, Ban, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function Users() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const queryClient = useQueryClient();

  // Debounced search
  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    const timer = setTimeout(() => setDebouncedSearch(value), 300);
    return () => clearTimeout(timer);
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ['users', { page, pageSize, search: debouncedSearch }],
    queryFn: () => mockCrudService.getUsers({ page, pageSize, search: debouncedSearch }),
  });

  const toggleBlockMutation = useMutation({
    mutationFn: mockCrudService.toggleUserBlock,
    onSuccess: (updatedUser) => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success(
        updatedUser.isBlocked ? 'Пользователь заблокирован' : 'Пользователь разблокирован'
      );
    },
  });

  const { data: articlesData, isLoading: articlesLoading } = useQuery<Article[]>({
    queryKey: ['user-articles', selectedUser?.id],
    queryFn: () => mockCrudService.getUserArticles(selectedUser!.id),
    enabled: !!selectedUser,
  });

  const handleViewArticles = (user: User) => {
    setSelectedUser(user);
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
          onChange={(e) => handleSearchChange(e.target.value)}
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
              <TableHead className="w-[70px]">Действия</TableHead>
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
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleViewArticles(user)}>
                        <Package className="mr-2 h-4 w-4" />
                        Артикулы пользователя
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className={user.isBlocked ? 'text-green-600' : 'text-destructive'}
                        onClick={() => toggleBlockMutation.mutate(user.id)}
                      >
                        {user.isBlocked ? (
                          <>
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Разблокировать
                          </>
                        ) : (
                          <>
                            <Ban className="mr-2 h-4 w-4" />
                            Заблокировать
                          </>
                        )}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
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

      {/* User Articles Dialog */}
      <Dialog open={!!selectedUser} onOpenChange={() => setSelectedUser(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Артикулы пользователя {selectedUser?.username}</DialogTitle>
            <DialogDescription>
              Всего артикулов: {articlesData?.length || 0}
            </DialogDescription>
          </DialogHeader>

          {articlesLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : articlesData && articlesData.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Артикул</TableHead>
                    <TableHead>Дата добавления</TableHead>
                    <TableHead>Последняя проверка</TableHead>
                    <TableHead>Статус</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {articlesData.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell className="font-medium">
                        {article.articleNumber}
                      </TableCell>
                      <TableCell>
                        {new Date(article.createdAt).toLocaleDateString('ru-RU')}
                      </TableCell>
                      <TableCell>
                        {article.lastCheck
                          ? new Date(article.lastCheck).toLocaleDateString('ru-RU')
                          : 'Никогда'}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            article.status === 'active'
                              ? 'default'
                              : article.status === 'error'
                              ? 'destructive'
                              : 'secondary'
                          }
                        >
                          {article.status === 'active'
                            ? 'Активный'
                            : article.status === 'error'
                            ? 'Ошибка'
                            : 'Неактивный'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="text-center py-10 text-muted-foreground">
              У пользователя нет артикулов
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
