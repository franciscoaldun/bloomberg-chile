export interface Indicator {
  id: string;
  name: string;
  unit: string;
  frequency: string;
  value: number | null;
  date: string | null;
  change: number | null;
  change_pct: number | null;
  prev_date: string | null;
  source: string;
  derived_fields: string[];
}

export interface DashboardResponse {
  indicators: Indicator[];
}

export interface SeriesPoint {
  date: string;
  value: number | null;
}

export interface SeriesResponse {
  id: string;
  bcch_id: string;
  name: string;
  unit: string;
  frequency: string;
  count: number;
  data: SeriesPoint[];
  source: string;
  note: string;
}

export interface RefreshInfo {
  last: string | null;
  last_ok: boolean | null;
  last_series: number;
  last_obs: number;
  next: string | null;
  refreshing: boolean;
  interval_sec: number;
}

export interface HealthResponse {
  status: string;
  series_count: number;
  last_updates: Record<string, string>;
  refresh: RefreshInfo;
}
