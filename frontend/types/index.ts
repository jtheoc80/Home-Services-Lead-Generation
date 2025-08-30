/**
 * Main TypeScript types export for frontend
 * Generated after swapping from permits to leads table
 */

// Lead types
export * from './leads';

// API types
export * from './api';

// Utility types
export * from './utils';

// Re-export commonly used types
export type {
  Lead,
  LeadForPermitsView,
  EnhancedLead,
  LeadInsert,
  LeadUpdate,
  CreateLeadFormData,
  CreateLeadResult,
  UseLeadsReturn,
  UseEnhancedLeadsReturn
} from './leads';

export type {
  ApiResponse,
  ApiError,
  PaginatedResponse,
  LeadFilters
} from './api';
