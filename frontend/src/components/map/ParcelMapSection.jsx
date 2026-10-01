/**
 * ParcelMapSection — Deferred parcel map region
 *
 * The map is the heaviest thing in the app: react-leaflet, Leaflet itself and
 * the OSM tile pipeline. It also sits below the page header, so on a phone it
 * starts well below the fold.
 *
 * Two separate deferrals happen here, and they are deliberately different:
 *
 *  1. Data — the parcel GeoJSON request is not issued until the section is
 *     close to the viewport. On a phone the user gets the header, banner and
 *     navigation painted first instead of waiting on a fetch they cannot see.
 *
 *  2. Code — ParcelMap is behind React.lazy, so Leaflet + react-leaflet arrive
 *     as their own chunk instead of sitting in the critical path of first
 *     paint.
 *
 * The placeholder reserves exactly the height of the real MapContainer so the
 * swap cannot shift layout (CLS stays at zero).
 *
 * @module components/map/ParcelMapSection
 */

import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { fetchParcelsGeoJSON } from '../../lib/api';

// Split out of the main bundle: everything ParcelMap pulls in (Leaflet,
// react-leaflet, leaflet.css) is only fetched once this chunk is requested.
const ParcelMap = lazy(() => import('./ParcelMap'));

const EMPTY = { type: 'FeatureCollection', features: [] };

// Must match ParcelMap's MapContainer sizing so the swap causes no reflow.
const MAP_HEIGHT = { height: 'min(70vh, 500px)', minHeight: '280px' };

function MapPlaceholder({ label }) {
  return (
    <div
      className="w-full flex flex-col items-center justify-center gap-2 bg-slate-100 text-slate-400"
      style={MAP_HEIGHT}
      role="status"
      aria-label={label}
    >
      <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}

export function ParcelMapSection({
  projectCode,
  district,
  selectedParcel,
  onParcelSelect,
}) {
  const containerRef = useRef(null);
  // Environments without IntersectionObserver (very old browsers, some test
  // runners) must never be stuck behind the placeholder, so the fallback is
  // applied as the initial value rather than via a state update in an effect.
  const [isNearViewport, setIsNearViewport] = useState(
    () => typeof IntersectionObserver === 'undefined'
  );
  const [parcels, setParcels] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Start fetching only once the section is near the viewport. rootMargin gives
  // it a generous head start so the data is usually already there by the time
  // the map scrolls into view.
  useEffect(() => {
    const el = containerRef.current;
    if (!el || isNearViewport) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setIsNearViewport(true);
          observer.disconnect();
        }
      },
      { rootMargin: '400px 0px' }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [isNearViewport]);

  // Fetch only once the section is close to being needed. `cancelled` prevents a
  // slow response from an old project/district overwriting the current one.
  useEffect(() => {
    if (!isNearViewport) return undefined;

    let cancelled = false;

    (async () => {
      setLoading(true);
      setError(null);

      // fetchParcelsGeoJSON resolves with mock data rather than rejecting, so a
      // catch here is only a guard against an unexpected throw.
      try {
        const geojson = await fetchParcelsGeoJSON({ projectCode, district });
        if (cancelled) return;
        setParcels(
          geojson && Array.isArray(geojson.features) ? geojson : EMPTY
        );
      } catch (err) {
        console.warn('[ParcelMapSection] Parcel fetch failed:', err);
        if (cancelled) return;
        setError('Unable to load parcel data. Please try again later.');
        setParcels(EMPTY);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isNearViewport, projectCode, district]);

  const handleParcelSelect = useCallback(
    (parcel) => onParcelSelect(parcel),
    [onParcelSelect]
  );

  return (
    <div ref={containerRef}>
      <Suspense
        fallback={<MapPlaceholder label="Loading GIS map…" />}
      >
        {isNearViewport ? (
          <ParcelMap
            parcels={parcels}
            selectedParcel={selectedParcel}
            onParcelSelect={handleParcelSelect}
            loading={loading}
            error={error}
          />
        ) : (
          <MapPlaceholder label="Map available on scroll" />
        )}
      </Suspense>
    </div>
  );
}

export default ParcelMapSection;
