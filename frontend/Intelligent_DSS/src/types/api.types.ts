export interface ApiError {
  error: string;
  message: string;
  status_code: number;
  detail?: string;
  timestamp: string;
  path: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
