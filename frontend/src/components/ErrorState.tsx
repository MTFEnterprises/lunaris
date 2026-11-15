import { ApiError } from '../api/client';

export default function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof ApiError ? error.message : 'The backend response was unavailable.';
  const backendUnavailable = !(error instanceof ApiError) || error.status >= 500;
  return (
    <div className="rounded-xl border border-rose-400/30 bg-rose-950/30 p-4 text-sm text-rose-200">
      <p className="font-semibold">{backendUnavailable ? 'Backend unavailable' : 'Data unavailable'}</p>
      <p className="mt-1 text-rose-200/80">{message}</p>
      {onRetry && (
        <button className="mt-3 rounded-lg border border-rose-300/30 px-3 py-1.5 text-xs hover:bg-rose-400/10" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
