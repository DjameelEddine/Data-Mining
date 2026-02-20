/* ------------------------------------------------------------------ */
/*  TypeScript interfaces shared across the frontend                  */
/* ------------------------------------------------------------------ */

export interface OverviewStats {
  total_shipments: number;
  delivered: number;
  in_transit: number;
  delayed: number;
  unique_packages: number;
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
  total_estimated_hours: number;
  total_estimated_days: number;
  route_speed: "fast" | "normal" | "slow";
  current_location: string;
  next_location?: string;
  event_type: string | number;
  last_scan_date: string;
  total_scans: number;
  was_saved: boolean;
  status: string;
  features: Record<string, string>;
  journey_history: JourneyHistoryRow[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
