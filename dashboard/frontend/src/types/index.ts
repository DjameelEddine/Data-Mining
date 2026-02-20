/* ------------------------------------------------------------------ */
/*  TypeScript interfaces shared across the frontend                  */
/* ------------------------------------------------------------------ */

export interface OverviewStats {
  total_shipments: number;
  unique_packages: number;
  date_range_start: string;
  date_range_end: string;
}

export interface RcpOverviewStats {
  total_records: number;
  unique_receptacles: number;
  date_range_start: string;
  date_range_end: string;
}

export interface JourneyHistoryRow {
  date: string;
  etablissement_postal: string;
  next_etablissement_postal: string;
  EVENT_TYPE_CD: string;
}

export interface PredictionResult {
  mailitm_fid: string;
  prediction_hours: number;
  time_since_first_scan_hours: number;
  receptacle_time_since_first_scan_hours: number;
  total_estimated_hours: number;
  total_estimated_days: number;
  is_delayed: boolean;
  delay_threshold_days: number;
  route_speed: "fast" | "normal" | "slow";
  current_location: string;
  next_location?: string;
  event_type: string | number;
  last_scan_date: string;
  total_scans: number;
  recptcl_fid: string;
  was_saved: boolean;
  features: Record<string, string>;
  journey_history: JourneyHistoryRow[];
}

export interface RcpPredictionResult {
  recptcl_fid: string;
  prediction_hours: number;
  time_since_first_scan_hours: number;
  total_estimated_hours: number;
  total_estimated_days: number;
  route_speed: "fast" | "normal" | "slow";
  origin_country: string;
  destination_country: string;
  current_location: string;
  next_location?: string;
  event_type: string | number;
  last_scan_date: string;
  total_scans: number;
  was_saved: boolean;
  features: Record<string, string>;
  journey_history: JourneyHistoryRow[];
}

export type PredictionMode = "package" | "receptacle";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
