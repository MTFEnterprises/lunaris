import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-[70vh] text-center space-y-4">
      <h1 className="text-6xl font-extrabold text-cyan-400">404</h1>
      <h2 className="text-xl font-semibold text-slate-200">Signal Lost in Deep Space</h2>
      <p className="text-slate-400 text-sm max-w-md">
        The telemetry route you requested does not exist or has been decommissioned.
      </p>
      <Link to="/" className="px-5 py-2.5 bg-cyan-500 hover:bg-cyan-600 text-white font-medium rounded-lg text-sm transition-colors shadow-lg shadow-cyan-500/20">
        Return to Dashboard
      </Link>
    </div>
  );
}