/**
 * ComparisonMetrics Component
 * Displays comparison metrics, index, and recommendations
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  Star,
  Tag,
  MessageSquare,
  AlertCircle,
  Trophy,
  Target,
} from 'lucide-react';
import {
  ComparisonMetrics as Metrics,
  getGradeColor,
  getGradeDescription,
  formatPercentage,
} from '@/services/comparisonService';

interface ComparisonMetricsProps {
  metrics: Metrics;
}

export const ComparisonMetrics: React.FC<ComparisonMetricsProps> = ({ metrics }) => {
  const renderDifference = (
    icon: React.ReactNode,
    title: string,
    absolute: number,
    percentage: number,
    who: string,
    recommendation: string,
    isInverse: boolean = false // true для цены (ниже = лучше)
  ) => {
    let trendIcon;
    let trendColor;

    if (who === 'equal') {
      trendIcon = <Minus className="h-4 w-4" />;
      trendColor = 'text-gray-500';
    } else if ((who === 'own' && !isInverse) || (who === 'competitor' && isInverse)) {
      trendIcon = <TrendingUp className="h-4 w-4" />;
      trendColor = 'text-green-600';
    } else {
      trendIcon = <TrendingDown className="h-4 w-4" />;
      trendColor = 'text-red-600';
    }

    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium">{title}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`flex items-center gap-1 ${trendColor}`}>
              {trendIcon}
              <span className="font-mono text-sm">
                {formatPercentage(percentage)}
              </span>
            </span>
          </div>
          <Badge variant="outline" className="text-xs">
            {who === 'own' ? 'Вы лучше' : who === 'competitor' ? 'Конкурент лучше' : 'Равно'}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">{recommendation}</p>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Competitiveness Index & Grade */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              Индекс конкурентоспособности
            </CardTitle>
            <Badge className={`${getGradeColor(metrics.grade)} text-white text-lg px-3 py-1`}>
              {metrics.grade}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">
                {(metrics.competitiveness_index * 100).toFixed(0)}%
              </span>
              <span className="text-sm text-muted-foreground">
                {getGradeDescription(metrics.grade)}
              </span>
            </div>
            <Progress
              value={metrics.competitiveness_index * 100}
              className="h-3"
            />
          </div>

          <Alert>
            <Target className="h-4 w-4" />
            <AlertTitle>Рекомендация</AlertTitle>
            <AlertDescription>{metrics.overall_recommendation}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Детальное сравнение</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Price */}
          {renderDifference(
            <DollarSign className="h-4 w-4 text-green-600" />,
            'Цена',
            metrics.price.absolute,
            metrics.price.percentage,
            metrics.price.who_cheaper,
            metrics.price.recommendation,
            true // inverse - ниже цена = лучше
          )}

          <div className="border-t pt-4" />

          {/* Rating */}
          {renderDifference(
            <Star className="h-4 w-4 text-yellow-500" />,
            'Рейтинг',
            metrics.rating.absolute,
            metrics.rating.percentage,
            metrics.rating.who_better,
            metrics.rating.recommendation
          )}

          <div className="border-t pt-4" />

          {/* SPP */}
          {renderDifference(
            <Tag className="h-4 w-4 text-purple-600" />,
            'СПП (скидки)',
            metrics.spp.absolute,
            metrics.spp.percentage,
            metrics.spp.who_better,
            metrics.spp.recommendation
          )}

          <div className="border-t pt-4" />

          {/* Reviews */}
          {renderDifference(
            <MessageSquare className="h-4 w-4 text-blue-600" />,
            'Отзывы',
            metrics.reviews.absolute,
            metrics.reviews.percentage,
            metrics.reviews.who_more,
            metrics.reviews.recommendation
          )}
        </CardContent>
      </Card>

      {/* Grade Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Шкала оценок</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-2 text-xs">
            {[
              { grade: 'A', range: '85-100%', desc: 'Отлично' },
              { grade: 'B', range: '70-84%', desc: 'Хорошо' },
              { grade: 'C', range: '50-69%', desc: 'Средне' },
              { grade: 'D', range: '30-49%', desc: 'Ниже ср.' },
              { grade: 'F', range: '0-29%', desc: 'Плохо' },
            ].map((item) => (
              <div key={item.grade} className="text-center space-y-1">
                <Badge className={`${getGradeColor(item.grade)} text-white w-full`}>
                  {item.grade}
                </Badge>
                <div className="text-muted-foreground">{item.range}</div>
                <div className="text-muted-foreground">{item.desc}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
