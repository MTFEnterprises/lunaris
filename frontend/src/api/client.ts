import type {
  AssessmentData,
  Envelope,
  EphemerisData,
  LayersCatalog,
  PlaceRequest,
  PowerRequest,
  ReportData,
  RequirementRequest,
  ScenarioData,
  ScenarioRequest,
  SitesData,
  TimelineRequest,
} from './types';
import type { ApiErrorBody } from './types';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor(status: number, body: ApiErrorBody | null) {
    super(body?.error.message ?? `API request failed with HTTP ${status}.`);
    this.name = 'ApiError';
    this.status = status;
    this.code = body?.error.code ?? 'HTTP_ERROR';
    this.details = body?.error.details ?? {};
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(503, {
      error: {
        code: 'SERVICE_UNAVAILABLE',
        message: 'The LUNARIS API could not be reached.',
        details: {},
      },
    });
  }

  if (!response.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      body = null;
    }
    throw new ApiError(response.status, body);
  }

  return (await response.json()) as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
}

export function getHealth(): Promise<Envelope<Record<string, unknown>>> {
  return request('/api/health');
}

export function getSites(): Promise<Envelope<SitesData>> {
  return request('/api/sites');
}

export function getSite(siteId: string): Promise<Envelope<SitesData['sites'][number]>> {
  return request(`/api/sites/${encodeURIComponent(siteId)}`);
}

export function getEphemeris(
  body: PlaceRequest & { time_utc: string },
): Promise<Envelope<EphemerisData>> {
  return post('/api/ephemeris', body);
}

export function getIllumination(body: TimelineRequest): Promise<Envelope<ScenarioData>> {
  return post('/api/illumination', body);
}

export function getCommunication(body: TimelineRequest): Promise<Envelope<ScenarioData>> {
  return post('/api/communication', body);
}

export function getTimeline(body: TimelineRequest): Promise<Envelope<ScenarioData>> {
  return post('/api/timeline', body);
}

export function getPowerEstimate(body: PowerRequest): Promise<Envelope<Record<string, unknown>>> {
  return post('/api/power/estimate', body);
}

export function getTerrainHorizon(
  body: PlaceRequest,
): Promise<Envelope<Record<string, unknown>>> {
  return post('/api/terrain/horizon', body);
}

export function getTerrainSlope(body: PlaceRequest): Promise<Envelope<Record<string, unknown>>> {
  return post('/api/terrain/slope', body);
}

export function compare(body: Record<string, unknown>): Promise<Envelope<Record<string, unknown>>> {
  return post('/api/compare', body);
}

export function assess(
  scenario: Record<string, unknown>,
  requirements: RequirementRequest[],
): Promise<Envelope<AssessmentData>> {
  return post('/api/assessment', { scenario, requirements });
}

export function report(
  scenario: Record<string, unknown>,
  requirements: RequirementRequest[],
): Promise<Envelope<ReportData>> {
  return post('/api/report', { scenario, requirements });
}

export function getLayers(): Promise<Envelope<LayersCatalog>> {
  return request('/api/layers');
}

export function getLayerImageUrl(file: string): string {
  const normalized = file.replace(/^layers\//, '');
  return `/api/layers/${normalized.split('/').map(encodeURIComponent).join('/')}`;
}
