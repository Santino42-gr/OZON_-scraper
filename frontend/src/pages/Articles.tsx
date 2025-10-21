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
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Label } from '@/components/ui/label';
import { mockCrudService } from '@/services/mockCrudService';
import { Article } from '@/types/crud';
import { Search, MoreHorizontal, Eye, Edit, Trash2, ChevronLeft, ChevronRight, Download } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { toast } from 'sonner';

export default function Articles() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  // Модальные окна
  const [viewArticle, setViewArticle] = useState<Article | null>(null);
  const [editArticle, setEditArticle] = useState<Article | null>(null);
  const [editStatus, setEditStatus] = useState<Article['status']>('active');

  const queryClient = useQueryClient();

  // Debounced search
  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    const timer = setTimeout(() => setDebouncedSearch(value), 300);
    return () => clearTimeout(timer);
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ['articles', { page, pageSize, search: debouncedSearch, statusFilter }],
    queryFn: () => mockCrudService.getArticles({
      page,
      pageSize,
      search: debouncedSearch,
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

  const deleteMultipleMutation = useMutation({
    mutationFn: mockCrudService.deleteMultipleArticles,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      setSelectedIds([]);
      toast.success(`Удалено артикулов: ${selectedIds.length}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Article> }) =>
      mockCrudService.updateArticle(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      setEditArticle(null);
      toast.success('Артикул обновлен');
    },
  });

  const exportMutation = useMutation({
    mutationFn: () => mockCrudService.exportArticles({
      search: debouncedSearch,
      status: statusFilter,
    }),
    onSuccess: (csv) => {
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `articles_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      toast.success('Экспорт завершен');
    },
  });

  const toggleSelectAll = () => {
    if (selectedIds.length === data?.data.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(data?.data.map(a => a.id) || []);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

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

  const handleEdit = (article: Article) => {
    setEditArticle(article);
    setEditStatus(article.status);
  };

  const handleSaveEdit = () => {
    if (editArticle) {
      updateMutation.mutate({
        id: editArticle.id,
        data: { status: editStatus },
      });
    }
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

      {/* Filters and Actions */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Поиск по артикулу..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
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

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending}
          >
            <Download className="mr-2 h-4 w-4" />
            Экспорт
          </Button>
          {selectedIds.length > 0 && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => deleteMultipleMutation.mutate(selectedIds)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Удалить ({selectedIds.length})
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]">
                <Checkbox
                  checked={selectedIds.length === data?.data.length && data?.data.length > 0}
                  onCheckedChange={toggleSelectAll}
                />
              </TableHead>
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
                <TableCell>
                  <Checkbox
                    checked={selectedIds.includes(article.id)}
                    onCheckedChange={() => toggleSelect(article.id)}
                  />
                </TableCell>
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
                      <DropdownMenuItem onClick={() => setViewArticle(article)}>
                        <Eye className="mr-2 h-4 w-4" />
                        Просмотр
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleEdit(article)}>
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

      {/* View Dialog */}
      <Dialog open={!!viewArticle} onOpenChange={() => setViewArticle(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Детали артикула {viewArticle?.articleNumber}</DialogTitle>
            <DialogDescription>
              Добавлен {viewArticle && new Date(viewArticle.createdAt).toLocaleDateString('ru-RU')}
            </DialogDescription>
          </DialogHeader>
          {viewArticle && (
            <div className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Артикул</Label>
                  <p className="font-medium mt-1">{viewArticle.articleNumber}</p>
                </div>
                <div>
                  <Label>Статус</Label>
                  <div className="mt-1">
                    <Badge variant={getStatusBadge(viewArticle.status)}>
                      {getStatusLabel(viewArticle.status)}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label>Пользователь</Label>
                  <p className="mt-1">{viewArticle.userName}</p>
                </div>
                <div>
                  <Label>Проблемный</Label>
                  <p className="mt-1">{viewArticle.isProblematic ? 'Да' : 'Нет'}</p>
                </div>
              </div>
              
              {viewArticle.lastCheckData && (
                <div>
                  <Label>Последние данные OZON</Label>
                  <pre className="mt-2 text-xs bg-muted p-4 rounded-md overflow-x-auto">
                    {JSON.stringify(viewArticle.lastCheckData, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editArticle} onOpenChange={() => setEditArticle(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Редактировать артикул</DialogTitle>
            <DialogDescription>
              Изменение статуса артикула {editArticle?.articleNumber}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="status">Статус</Label>
              <Select value={editStatus} onValueChange={(v) => setEditStatus(v as Article['status'])}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Активный</SelectItem>
                  <SelectItem value="inactive">Неактивный</SelectItem>
                  <SelectItem value="error">Ошибка</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditArticle(null)}>
              Отмена
            </Button>
            <Button onClick={handleSaveEdit} disabled={updateMutation.isPending}>
              Сохранить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
