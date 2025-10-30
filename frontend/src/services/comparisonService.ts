/**
 * Comparison Service
 * API methods for article comparison functionality
 */

import axios, { AxiosInstance } from 'axios';

// Base URL from environment
const API_BASE_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/comparison`,
  timeout: 30000, // 30s for scraping operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Comparison API Error:', error.response?.data || error.message);
    throw error;
  }
);

// ==================== Types ====================

export interface ArticleGroupCreate {
  name?: string;
  group_type: 'comparison' | 'variants' | 'similar';
}

export interface ArticleGroupResponse {
  id: string;
  user_id: string;
  name?: string;
  group_type: string;
  created_at: string;
  updated_at: string;
  members_count?: number;
}

export interface QuickComparisonCreate {
  own_article_number: string;
  competitor_article_number: string;
  group_name?: string;
  scrape_now: boolean;
}

export interface PriceDifference {
  absolute: number;
  percentage: number;
  who_cheaper: 'own' | 'competitor' | 'equal';
  recommendation: string;
}

export interface RatingDifference {
  absolute: number;
  percentage: number;
  who_better: 'own' | 'competitor' | 'equal';
  recommendation: string;
}

export interface SPPDifference {
  absolute: number;
  percentage: number;
  who_better: 'own' | 'competitor' | 'equal';
  recommendation: string;
}

export interface ReviewsDifference {
  absolute: number;
  percentage: number;
  who_more: 'own' | 'competitor' | 'equal';
  recommendation: string;
}

export interface ComparisonMetrics {
  price: PriceDifference;
  rating: RatingDifference;
  spp: SPPDifference;
  reviews: ReviewsDifference;
  competitiveness_index: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  overall_recommendation: string;
}

export interface ArticleComparisonData {
  article_id: string;
  article_number: string;
  role: 'own' | 'competitor' | 'item';
  name?: string;
  price?: number;
  old_price?: number;
  normal_price?: number;
  ozon_card_price?: number;
  average_price_7days?: number;
  rating?: number;
  reviews_count?: number;
  spp1?: number;
  spp2?: number;
  spp_total?: number;
  available: boolean;
  image_url?: string;
  product_url?: string;
  position: number;
}

export interface ComparisonResponse {
  group_id: string;
  group_name?: string;
  group_type: string;
  own_product?: ArticleComparisonData;
  competitors: ArticleComparisonData[];
  other_items: ArticleComparisonData[];
  metrics?: ComparisonMetrics;
  compared_at: string;
  is_fresh: boolean;
}

export interface ComparisonSnapshotResponse {
  id: string;
  group_id: string;
  snapshot_date: string;
  comparison_data: any;
  metrics: any;
  competitiveness_index: number;
  created_at: string;
}

export interface ComparisonHistoryResponse {
  group_id: string;
  snapshots: ComparisonSnapshotResponse[];
  total_count: number;
  date_from: string;
  date_to: string;
}

export interface UserComparisonStats {
  total_groups: number;
  comparison_groups: number;
  total_articles: number;
  avg_competitiveness_index?: number;
  last_comparison_date?: string;
}

// ==================== API Methods ====================

export const comparisonApi = {
  /**
   * Quick create comparison (1v1)
   * Creates group, adds articles, scrapes data, calculates metrics - all in one request
   */
  async quickCompare(
    userId: string,
    data: QuickComparisonCreate
  ): Promise<ComparisonResponse> {
    const { data: response } = await apiClient.post(
      `/quick-compare?user_id=${userId}`,
      data
    );
    return response;
  },

  /**
   * Create comparison group
   */
  async createGroup(
    userId: string,
    groupData: ArticleGroupCreate
  ): Promise<ArticleGroupResponse> {
    const { data } = await apiClient.post(`/groups?user_id=${userId}`, groupData);
    return data;
  },

  /**
   * Get comparison group
   */
  async getGroup(groupId: string, userId: string): Promise<ArticleGroupResponse> {
    const { data } = await apiClient.get(`/groups/${groupId}?user_id=${userId}`);
    return data;
  },

  /**
   * Delete comparison group
   */
  async deleteGroup(groupId: string, userId: string): Promise<void> {
    await apiClient.delete(`/groups/${groupId}?user_id=${userId}`);
  },

  /**
   * Get comparison with metrics
   */
  async getComparison(
    groupId: string,
    userId: string,
    refresh: boolean = false
  ): Promise<ComparisonResponse> {
    const { data } = await apiClient.get(
      `/groups/${groupId}/compare?user_id=${userId}&refresh=${refresh}`
    );
    return data;
  },

  /**
   * Get comparison history
   */
  async getHistory(
    groupId: string,
    userId: string,
    days: number = 30
  ): Promise<ComparisonHistoryResponse> {
    const { data } = await apiClient.get(
      `/groups/${groupId}/history?user_id=${userId}&days=${days}`
    );
    return data;
  },

  /**
   * Get user comparison statistics
   */
  async getUserStats(userId: string): Promise<UserComparisonStats> {
    const { data } = await apiClient.get(`/users/${userId}/stats`);
    return data;
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<any> {
    const { data } = await apiClient.get('/health');
    return data;
  },
};

// Helper functions

/**
 * Get grade color for badges
 */
export function getGradeColor(grade: string): string {
  switch (grade) {
    case 'A':
      return 'bg-green-500';
    case 'B':
      return 'bg-blue-500';
    case 'C':
      return 'bg-yellow-500';
    case 'D':
      return 'bg-orange-500';
    case 'F':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
}

/**
 * Get grade description
 */
export function getGradeDescription(grade: string): string {
  switch (grade) {
    case 'A':
      return 'Отличная конкурентоспособность';
    case 'B':
      return 'Хорошая конкурентоспособность';
    case 'C':
      return 'Средняя конкурентоспособность';
    case 'D':
      return 'Ниже среднего';
    case 'F':
      return 'Плохая конкурентоспособность';
    default:
      return 'Нет данных';
  }
}

/**
 * Format price
 */
export function formatPrice(price?: number): string {
  if (!price) return '—';
  return `${price.toLocaleString('ru-RU')} ₽`;
}

/**
 * Format percentage
 */
export function formatPercentage(value?: number): string {
  if (!value && value !== 0) return '—';
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
}

/**
 * Format rating
 */
export function formatRating(rating?: number): string {
  if (!rating) return '—';
  return rating.toFixed(1);
}
