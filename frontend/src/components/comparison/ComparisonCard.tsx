/**
 * ComparisonCard Component
 * Displays article data for comparison
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  TrendingDown,
  Star,
  MessageSquare,
  Tag,
  ExternalLink
} from 'lucide-react';
import { ArticleComparisonData } from '@/services/comparisonService';
import { formatPrice, formatRating, formatPercentage } from '@/services/comparisonService';

interface ComparisonCardProps {
  article: ArticleComparisonData;
  isOwn?: boolean;
}

export const ComparisonCard: React.FC<ComparisonCardProps> = ({ article, isOwn = false }) => {
  const roleColors = {
    own: 'bg-blue-100 text-blue-800 border-blue-300',
    competitor: 'bg-red-100 text-red-800 border-red-300',
    item: 'bg-gray-100 text-gray-800 border-gray-300',
  };

  const roleLabels = {
    own: 'Ваш товар',
    competitor: 'Конкурент',
    item: 'Товар',
  };

  return (
    <Card className={`h-full ${isOwn ? 'border-2 border-primary' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge className={roleColors[article.role]}>
                {roleLabels[article.role]}
              </Badge>
              {!article.available && (
                <Badge variant="destructive">Нет в наличии</Badge>
              )}
            </div>
            <CardTitle className="text-base line-clamp-2">
              {article.name || 'Без названия'}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Арт. {article.article_number}
            </p>
          </div>
          {article.image_url && (
            <img
              src={article.image_url}
              alt={article.name}
              className="w-16 h-16 object-cover rounded"
            />
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Цены */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Цена с картой:</span>
            <span className="font-semibold text-lg">
              {formatPrice(article.ozon_card_price || article.normal_price)}
            </span>
          </div>

          {article.normal_price && article.ozon_card_price && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Без карты:</span>
              <span className="line-through text-muted-foreground">
                {formatPrice(article.normal_price)}
              </span>
            </div>
          )}

          {article.old_price && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Старая цена:</span>
              <span className="line-through text-muted-foreground">
                {formatPrice(article.old_price)}
              </span>
            </div>
          )}

          {article.average_price_7days && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Средняя за 7 дней:</span>
              <span>{formatPrice(article.average_price_7days)}</span>
            </div>
          )}
        </div>

        {/* Рейтинг и отзывы */}
        <div className="flex items-center gap-4 pt-2 border-t">
          {article.rating && (
            <div className="flex items-center gap-1">
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <span className="font-medium">{formatRating(article.rating)}</span>
            </div>
          )}
          {article.reviews_count !== undefined && (
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <MessageSquare className="h-4 w-4" />
              <span>{article.reviews_count}</span>
            </div>
          )}
        </div>

        {/* СПП метрики */}
        {(article.spp_total || article.spp1 || article.spp2) && (
          <div className="space-y-1 pt-2 border-t">
            <div className="flex items-center gap-2 text-sm">
              <Tag className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">СПП:</span>
            </div>

            {article.spp_total && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Общий:</span>
                <Badge variant="outline" className="font-mono">
                  {formatPercentage(article.spp_total)}
                </Badge>
              </div>
            )}

            {article.spp1 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">СПП1:</span>
                <span className="font-mono text-xs">{formatPercentage(article.spp1)}</span>
              </div>
            )}

            {article.spp2 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">СПП2:</span>
                <span className="font-mono text-xs">{formatPercentage(article.spp2)}</span>
              </div>
            )}
          </div>
        )}

        {/* Ссылка на товар */}
        {article.product_url && (
          <a
            href={article.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-primary hover:underline pt-2 border-t"
          >
            <ExternalLink className="h-3 w-3" />
            Открыть на OZON
          </a>
        )}
      </CardContent>
    </Card>
  );
};
