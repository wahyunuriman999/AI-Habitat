import { useEffect, useState } from 'react';
import { apiGet } from './lib/api';
import './App.css';

/* ── Types ──────────────────────────────────────────────────────────────── */

interface HealthData {
  status: string;
  database: string;
  environment?: string;
}

interface VersionData {
  name: string;
  version: string;
  environment: string;
}

/* ── Status Row ─────────────────────────────────────────────────────────── */

function StatusRow({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-zinc-900 border border-zinc-800 rounded">
      <div
        className={`w-2 h-2 rounded-full shrink-0 ${ok ? 'bg-emerald-500' : 'bg-red-500'}`}
      />
      <span className="text-sm text-zinc-400 w-32">{label}</span>
      <span className="text-sm text-zinc-200">{value}</span>
    </div>
  );
}

/* ── App ────────────────────────────────────────────────────────────────── */

function App() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [version, setVersion] = useState<VersionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiReachable, setApiReachable] = useState(false);

  useEffect(() => {
    async function checkStatus() {
      try {
        const [healthRes, versionRes] = await Promise.all([
          apiGet<HealthData>('/api/v1/health'),
          apiGet<VersionData>('/api/v1/version'),
        ]);
        setApiReachable(true);
        if (healthRes.success && healthRes.data) setHealth(healthRes.data);
        if (versionRes.success && versionRes.data) setVersion(versionRes.data);
      } catch {
        setApiReachable(false);
      } finally {
        setLoading(false);
      }
    }
    checkStatus();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="border-b border-zinc-800 px-6 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold tracking-tight">AI HABITAT</h1>
        {version && (
          <span className="text-xs text-zinc-500 font-mono">
            v{version.version}
          </span>
        )}
      </header>

      {/* ── Layout ──────────────────────────────────────────────── */}
      <div className="flex h-[calc(100vh-49px)]">
        {/* Sidebar */}
        <nav className="w-56 border-r border-zinc-800 p-4 shrink-0">
          <div className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-3">
            Navigation
          </div>
          <div className="space-y-1">
            <div className="px-3 py-2 text-sm text-zinc-300 bg-zinc-800/50 rounded cursor-default">
              Dashboard
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="flex-1 p-8 overflow-auto">
          <div className="max-w-xl">
            <h2 className="text-xl font-semibold mb-1">Foundation Online</h2>
            <p className="text-sm text-zinc-500 mb-6">
              Phase 1 — infrastructure health
            </p>

            {loading ? (
              <div className="text-sm text-zinc-500">Connecting to API…</div>
            ) : (
              <div className="space-y-2">
                <StatusRow
                  label="API"
                  value={apiReachable ? 'Connected' : 'Disconnected'}
                  ok={apiReachable}
                />
                <StatusRow
                  label="Database"
                  value={
                    health?.database === 'connected'
                      ? 'Connected'
                      : 'Disconnected'
                  }
                  ok={health?.database === 'connected'}
                />
                <StatusRow
                  label="Environment"
                  value={
                    version?.environment ?? health?.environment ?? 'Unknown'
                  }
                  ok={true}
                />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
