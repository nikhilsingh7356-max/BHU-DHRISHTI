/**
 * DataSourceBadge — Live vs Demo Data Indicator
 *
 * The API layer falls back to bundled mock data whenever the backend is
 * unavailable. That fallback is deliberate (the app stays usable offline),
 * but it also means a broken backend is indistinguishable from a working one.
 * This badge makes the current mode explicit so a misconfigured
 * VITE_API_BASE_URL is caught immediately instead of being mistaken for
 * real data.
 *
 * Renders nothing while `live` — the normal case needs no decoration.
 *
 * @module components/common/DataSourceBadge
 */

import { useSyncExternalStore } from 'react';
import { CloudOff, Loader2, FlaskConical } from 'lucide-react';
import { subscribeDataSource, getDataSource, getServerDataSource } from '../../lib/api';

// ── Status config ──
const STATUS_CONFIG = {
  unconfigured: {
    label: 'Demo data',
    detail:
      'No API configured. Set VITE_API_BASE_URL and redeploy to use live data.',
    icon: FlaskConical,
    tone: 'amber',
  },
  connecting: {
    label: 'Connecting',
    detail: 'Waiting for the first response from the configured API.',
    icon: Loader2,
    tone: 'slate',
  },
  degraded: {
    label: 'API unreachable',
    detail:
      'The configured backend did not respond, so bundled demo data is shown. Check VITE_API_BASE_URL and the backend deployment.',
    icon: CloudOff,
    tone: 'red',
  },
};

const TONE_CLASSES = {
  amber:
    'bg-amber-50 border-amber-200 text-amber-800 [&_svg]:text-amber-600',
  slate:
    'bg-slate-50 border-slate-200 text-slate-600 [&_svg]:text-slate-400',
  red: 'bg-red-50 border-red-200 text-red-800 [&_svg]:text-red-600',
};

export function DataSourceBadge() {
  const status = useSyncExternalStore(
    subscribeDataSource,
    getDataSource,
    getServerDataSource
  );

  if (status === 'live') return null;

  const config = STATUS_CONFIG[status];
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div
      className={`flex items-center gap-2.5 rounded-md border px-3 py-2 text-xs ${TONE_CLASSES[config.tone]}`}
      role="status"
      title={config.detail}
    >
      <Icon
        className={`w-4 h-4 shrink-0 ${status === 'connecting' ? 'animate-spin' : ''}`}
        aria-hidden="true"
      />
      <span className="font-semibold shrink-0">{config.label}</span>
      <span className="hidden sm:inline opacity-80 truncate">{config.detail}</span>
    </div>
  );
}
