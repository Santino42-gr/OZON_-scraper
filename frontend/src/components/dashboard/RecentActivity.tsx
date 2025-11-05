import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { LogEntry } from '@/types/dashboard';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

interface RecentActivityProps {
  logs: LogEntry[];
}

const getLevelColor = (level: LogEntry['level']) => {
  switch (level) {
    case 'error':
    case 'critical':
      return 'destructive';
    case 'warning':
      return 'secondary';
    default:
      return 'default';
  }
};

const getLevelLabel = (level: LogEntry['level']) => {
  switch (level) {
    case 'error':
      return 'Ошибка';
    case 'critical':
      return 'Критично';
    case 'warning':
      return 'Внимание';
    case 'info':
      return 'Инфо';
    default:
      return level;
  }
};

const getUserInitials = (name?: string) => {
  if (!name) return '?';
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

export const RecentActivity: React.FC<RecentActivityProps> = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Последние события</CardTitle>
          <CardDescription>Последние 10 записей логов</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[400px] text-muted-foreground">
            <p>Нет данных для отображения</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Последние события</CardTitle>
        <CardDescription>Последние 10 записей логов</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-4">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-3 pb-3 border-b last:border-0"
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{getUserInitials(log.userName)}</AvatarFallback>
                </Avatar>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <Badge variant={getLevelColor(log.level)} className="text-xs">
                      {getLevelLabel(log.level)}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(log.timestamp), {
                        locale: ru,
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                  <p className="text-sm">{log.message}</p>
                  {log.userName && (
                    <p className="text-xs text-muted-foreground">
                      Пользователь: {log.userName}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

