/**
 * API-related TypeScript types for frontend
 */

// Base API response structure
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  success?: boolean;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
}

// Pagination types
export interface PaginationParams {
  page?: number;
  limit?: number;
  orderBy?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T = any> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// Filter types for leads
export interface LeadFilters {
  city?: string;
  county?: string;
  status?: string;
  service?: string;
  minValue?: number;
  maxValue?: number;
  startDate?: string;
  endDate?: string;
}
