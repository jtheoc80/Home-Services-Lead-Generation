/**
 * Utility TypeScript types for frontend
 */

// Common form field types
export interface FormField {
  value: string;
  error?: string;
  touched?: boolean;
}

export interface FormState {
  [key: string]: FormField;
}

// Table/display types
export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

// Chart/metrics types
export interface MetricCard {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
  color?: 'blue' | 'green' | 'purple' | 'yellow' | 'red';
}

export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
}

// Navigation types
export interface NavigationItem {
  name: string;
  href: string;
  icon?: string;
  current?: boolean;
}

// Component prop types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}
