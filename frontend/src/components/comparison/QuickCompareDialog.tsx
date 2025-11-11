/**
 * QuickCompareDialog Component
 * Dialog for quick 1v1 article comparison
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Scale, AlertCircle } from 'lucide-react';
import { comparisonApi, QuickComparisonCreate, ComparisonResponse } from '@/services/comparisonService';

interface QuickCompareDialogProps {
  userId: string;
  onSuccess?: (comparison: ComparisonResponse) => void;
  trigger?: React.ReactNode;
}

export const QuickCompareDialog: React.FC<QuickCompareDialogProps> = ({
  userId,
  onSuccess,
  trigger,
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<QuickComparisonCreate>({
    own_article_number: '',
    competitor_article_number: '',
    group_name: '',
    scrape_now: true,
    report_frequency: 'once',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const comparison = await comparisonApi.quickCompare(userId, formData);

      // Success
      setOpen(false);
      setFormData({
        own_article_number: '',
        competitor_article_number: '',
        group_name: '',
        scrape_now: true,
        report_frequency: 'once',
      });

      if (onSuccess) {
        onSuccess(comparison);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка при создании сравнения');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof QuickComparisonCreate, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSelectChange = (value: string) => {
    handleChange('report_frequency', value);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button size="lg" className="gap-2">
            <Scale className="h-5 w-5" />
            Быстрое сравнение
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Scale className="h-5 w-5" />
            Сравнить с конкурентом
          </DialogTitle>
          <DialogDescription>
            Введите артикулы для быстрого сравнения 1v1.
            Система автоматически получит данные с OZON и рассчитает все метрики.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {/* Own Article */}
          <div className="space-y-2">
            <Label htmlFor="own">
              Ваш артикул <span className="text-red-500">*</span>
            </Label>
            <Input
              id="own"
              placeholder="Например: 123456789"
              value={formData.own_article_number}
              onChange={(e) => handleChange('own_article_number', e.target.value)}
              required
              disabled={loading}
            />
          </div>

          {/* Competitor Article */}
          <div className="space-y-2">
            <Label htmlFor="competitor">
              Артикул конкурента <span className="text-red-500">*</span>
            </Label>
            <Input
              id="competitor"
              placeholder="Например: 987654321"
              value={formData.competitor_article_number}
              onChange={(e) => handleChange('competitor_article_number', e.target.value)}
              required
              disabled={loading}
            />
          </div>

          {/* Group Name (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="name">
              Название группы <span className="text-muted-foreground text-xs">(опционально)</span>
            </Label>
            <Input
              id="name"
              placeholder="Например: Мой товар vs Конкурент A"
              value={formData.group_name}
              onChange={(e) => handleChange('group_name', e.target.value)}
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground">
              По умолчанию: "{formData.own_article_number} vs {formData.competitor_article_number}"
            </p>
          </div>

          {/* Report Frequency */}
          <div className="space-y-2">
            <Label htmlFor="frequency">
              Частота отчетов <span className="text-muted-foreground text-xs">(для создаваемых артикулов)</span>
            </Label>
            <Select
              value={formData.report_frequency || 'once'}
              onValueChange={handleSelectChange}
              disabled={loading}
            >
              <SelectTrigger id="frequency">
                <SelectValue placeholder="Выберите частоту отчетов" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="once">1 раз в день (09:00)</SelectItem>
                <SelectItem value="twice">2 раза в день (09:00 и 15:00)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Как часто получать обновления цен для этих артикулов
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Info Alert */}
          <Alert>
            <AlertDescription className="text-xs">
              ⏱️ Процесс займёт 10-30 секунд в зависимости от скорости OZON.
              Данные будут актуальными на момент запроса.
            </AlertDescription>
          </Alert>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={loading}
              className="flex-1"
            >
              Отмена
            </Button>
            <Button
              type="submit"
              disabled={loading || !formData.own_article_number || !formData.competitor_article_number}
              className="flex-1 gap-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? 'Сравниваю...' : 'Сравнить'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
