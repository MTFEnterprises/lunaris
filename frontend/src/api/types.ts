export type DataClass =
  | 'OBSERVED'
  | 'PUBLISHED'
  | 'CALCULATED'
  | 'ESTIMATED'
  | 'ILLUSTRATIVE'
  | 'UNAVAILABLE';

export interface ProvenanceInput {
  name: string;
  version: string | null;
  retrieved_utc: string | null;
  url: string | null;
}

export interface Provenance {
  class: DataClass;
  inputs: ProvenanceInput[];
  assumptions: string[];
  generated_utc: string | null;
  reason: string | null;
}

export interface Envelope<T> {
  data: T;
  provenance: Provenance;
  warnings: string[];
  cached: boolean;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export interface Site {
  id: string;
  name: string;
  region: string | null;
  lat: number | null;
  lon: number | null;
  source_url: string | null;
  class: DataClass;
  notes: string | null;
  kind: string | null;
  height_m: number | null;
}

export interface SitesData {
  sites: Site[];
}

export interface Angle {
  el: number;
  az: number;
}

export interface EphemerisData {
  site: Site;
  frame: string;
  time_utc: string;
  sun: Angle | null;
  earth: Angle | null;
  sun_dir_bf: number[] | null;
  earth_dir_bf: number[] | null;
  sun_lit_geom: boolean | null;
  earth_vis_geom: boolean | null;
  hours_to_sunset: number | null;
  hours_to_earthset: number | null;
}

export interface Timeseries {
  start_utc: string;
  step_min: number;
  sun_el: number[];
  sun_az: number[];
  earth_el: number[];
  earth_az: number[];
  sun_lit_geom: boolean[] | null;
  sun_lit_terrain: Array<boolean | null> | null;
  earth_vis_geom: boolean[] | null;
  earth_vis_terrain: Array<boolean | null> | null;
}

export interface Metrics {
  sunlit_geom_pct: number | null;
  sunlit_terrain_pct: number | null;
  earth_geom_pct: number | null;
  earth_terrain_pct: number | null;
  longest_dark_h: number | null;
  longest_comms_gap_h: number | null;
  max_sun_el_deg: number | null;
}

export interface Horizon {
  deg: Array<number | null> | null;
  dem: Record<string, unknown> | null;
  approx: boolean;
}

export interface ScenarioData {
  site: Site;
  frame: string;
  horizon: Horizon;
  timeseries: Timeseries;
  metrics: Metrics;
}

export interface LayersCatalog {
  schema_version: string;
  description: string;
  site_alignment_status: string;
  site_alignment_note: string;
  crs: Record<string, unknown>;
  coordinate_conversion: Record<string, unknown>;
  tiles: Record<string, {
    width_px: number;
    height_px: number;
    resolution_m: number;
    projected_bounds_m: Record<string, number>;
    layers: Record<string, { file: string; units: string; [key: string]: unknown }>;
    projection_parameters: { R_m: number; k0: number; lon0_deg: number };
    grid_origin: { x_left_m: number; y_top_m: number };
  }>;
}

export interface RequirementResult {
  id: string;
  status: 'pass' | 'fail' | 'unknown';
  measured: number | null;
  threshold: number | null;
  reason: string | null;
  confidence: string | null;
  missing_info: string[];
}

export interface AssessmentData {
  results: RequirementResult[];
  score: number | null;
  overall: 'pass' | 'fail' | 'unknown';
  [key: string]: unknown;
}

export interface ReportData {
  [key: string]: unknown;
}

export interface PlaceRequest {
  site_id?: string;
  lat?: number;
  lon?: number;
}

export interface TimelineRequest extends PlaceRequest {
  start_utc: string;
  hours: number;
  step_min?: number;
}

export interface PowerRequest extends TimelineRequest {
  panel: Record<string, unknown>;
}

export interface ScenarioRequest extends TimelineRequest {
  mode?: string;
}

export interface RequirementRequest {
  id: 'min_sunlit' | 'min_earth' | 'max_dark_hours';
  threshold: number;
  basis: 'terrain' | 'geometric';
}
