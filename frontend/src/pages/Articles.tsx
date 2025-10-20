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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { mockCrudService } from '@/services/mockCrudService';
import { Search, MoreHorizontal, Eye, Edit, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { toast } from 'sonner';

export default function Articles() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['articles', { page, pageSize, search, statusFilter }],
    queryFn: () => mockCrudService.getArticles({
      page,
      pageSize,
      search,
      status: statusFilter,
    }),
  });

  const deleteMutation = useMutation({
    mutationFn: mockCrudService.deleteArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      toast.success('Артикул удален');
    },
    onError: () => {
      toast.error('Ошибка при удалении');
    },
  });

  const getStatusBadge = (status: string) => {
    const variants = {
      active: 'default' as const,
      inactive: 'secondary' as const,
      error: 'destructive' as const,
    };
    return variants[status as keyof typeof variants] || 'default';
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      active: 'Активный',
      inactive: 'Неактивный',
      error: 'Ошибка',
    };
    return labels[status as keyof typeof labels] || status;
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
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Артикулы</h1>
        <p className="text-muted-foreground">
          Управление артикулами OZON
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Поиск по артикулу..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Статус" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все статусы</SelectItem>
            <SelectItem value="active">Активные</SelectItem>
            <SelectItem value="inactive">Неактивные</SelectItem>
            <SelectItem value="error">С ошибками</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Артикул</TableHead>
              <TableHead>Пользователь</TableHead>
              <TableHead>Дата добавления</TableHead>
              <TableHead>Последняя проверка</TableHead>
              <TableHead>Статус</TableHead>
              <TableHead className="w-[70px]">Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.data.map((article) => (
              <TableRow key={article.id}>
                <TableCell className="font-medium">
                  {article.articleNumber}
                  {article.isProblematic && (
                    <Badge variant="destructive" className="ml-2">
                      Проблемный
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback>{article.userInitials}</AvatarFallback>
                    </Avatar>
                    <span>{article.userName}</span>
                  </div>
                </TableCell>
                <TableCell>
                  {new Date(article.createdAt).toLocaleDateString('ru-RU')}
                </TableCell>
                <TableCell>
                  {article.lastCheck
                    ? formatDistanceToNow(new Date(article.lastCheck), {
                        locale: ru,
                        addSuffix: true,
                      })
                    : 'Никогда'}
                </TableCell>
                <TableCell>
                  <Badge variant={getStatusBadge(article.status)}>
                    {getStatusLabel(article.status)}
                  </Badge>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Eye className="mr-2 h-4 w-4" />
                        Просмотр
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Edit className="mr-2 h-4 w-4" />
                        Редактировать
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => deleteMutation.mutate(article.id)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Удалить
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
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

