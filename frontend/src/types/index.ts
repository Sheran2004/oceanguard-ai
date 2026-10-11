// Shared TypeScript types matching the FastAPI Pydantic schemas.

export interface Location {
  latitude: number | null;
  longitude: number | null;
  depth_m: number | null;
  region_label: string | null;
  is_demo: boolean;
}

export interface Detection {
  id: number;
  scan_id: number;
  detection_uid: string;
  class_id: number;
  class_name: string;
  confidence: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
  area_ratio: number;
  is_anomaly: boolean;
  anomaly_score: number;
  priority: 'low' | 'medium' | 'high' | 'review';
  review_status: 'pending' | 'approved' | 'rejected' | 'review';
  reviewer_comment?: string | null;
  explanation?: string | null;
  created_at: string | null;
}

export interface Scan {
  id: number;
  scan_uid: string;
  mission_id: number;
  filename: string;
  original_name: string;
  file_size: number;
  width: number;
  height: number;
  status: 'pending' | 'processing' | 'complete' | 'failed';
  is_demo: boolean;
  notes?: string | null;
  timestamp: string | null;
  created_at: string | null;
  location: Location | null;
  detection_count: number;
  anomaly_count: number;
  high_priority_count: number;
  detections?: Detection[];
}

export interface Mission {
  id: number;
  mission_id: string;
  name: string;
  survey_area?: string | null;
  operator?: string | null;
  description?: string | null;
  status: string;
  date: string | null;
  created_at: string | null;
  scan_count: number;
  detection_count: number;
  high_priority_count: number;
}

export interface Hotspot {
  region_label: string;
  latitude: number | null;
  longitude: number | null;
  detection_count: number;
  anomaly_count: number;
  avg_confidence: number;
  risk_level: 'low' | 'medium' | 'high';
}

export interface AnalyticsSummary {
  total_scans: number;
  total_detections: number;
  total_missions: number;
  debris_count: number;
  anomaly_count: number;
  high_priority_count: number;
  avg_confidence: number;
  class_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  anomaly_trend: { date: string; detections: number; anomalies: number }[];
  confidence_buckets: { range: string; count: number }[];
  real_vs_demo: {
    real: { scans: number; detections: number; anomalies: number; high: number; avg_confidence: number };
    demo: { scans: number; detections: number; anomalies: number; high: number; avg_confidence: number };
  };
  data_source: 'real-only' | 'real+demo';
}

export interface TimelinePoint {
  scan_id: number;
  scan_uid: string;
  timestamp: string | null;
  detections: number;
  anomalies: number;
}

export interface ClassInfo {
  id: string;
  name: string;
  description: string;
  base_priority: string;
  is_anomaly: boolean;
}

export interface SystemInfo {
  app_name: string;
  app_env: string;
  model_name: string;
  model_version: string;
  model_type: string;
  model_path: string;
  is_real_model: boolean;
  confidence_threshold: number;
  iou_threshold: number;
  anomaly_threshold: number;
  demo_mode: boolean;
  dataset_label: string;
  classes: Record<number, ClassInfo>;
  priority_rules: Record<string, number>;
  disclaimer: string;
}

export interface ModelVersion {
  id: number;
  name: string;
  version: string;
  model_type: string;
  path: string;
  dataset: string | null;
  training_date: string | null;
  metrics_json: string | null;
  status: string;
  description: string | null;
  created_at: string | null;
}

export interface ReportRecord {
  id: number;
  mission_id: number;
  filename: string;
  file_path: string;
  generated_by: string;
  created_at: string | null;
}

export interface AnomalyRecord {
  anomaly_id: number;
  detection_uid: string;
  scan_uid: string;
  scan_id: number;
  detection_id: number;
  score: number;
  method: string;
  description: string;
  region_label: string | null;
  review_status: string;
  priority: string;
  class_name: string;
  created_at: string | null;
}

export interface ScanSummary {
  headline: string;
  findings: string[];
  metrics: {
    total_detections: number;
    anomaly_count: number;
    high_priority_count: number;
    avg_confidence: number;
    top_classes: { class_name: string; count: number }[];
  };
  disclaimer: string;
}

export interface CompareResult {
  scan_a_id: number;
  scan_b_id: number;
  persistent: number;
  new_detections: number;
  removed: number;
  changed_regions: number;
  notes: string[];
}