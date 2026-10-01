-- ============================================================================
-- 3. PARCEL GEOJSON READ MODEL (ADDITIVE, NON-DESTRUCTIVE)
-- ============================================================================
-- Serves GET /api/v1/parcels/geojson as a GeoJSON FeatureCollection.
--
-- Why a function instead of a plain table read: PostgREST cannot call PostGIS
-- constructors such as ST_AsGeoJSON(), so the geometry has to be serialised
-- server-side. A `SECURITY INVOKER` SQL function is the smallest possible piece
-- of server-side logic and keeps authorisation where it belongs -- in the API
-- layer, which checks the JWT and the caller's role before calling this.
--
-- AUTHORISATION NOTE (important): the API authenticates with Supabase's
-- `service_role` key, and service_role BYPASSES Row Level Security. Relying on
-- RLS alone would therefore expose every parcel to every signed-in officer. The
-- caller identity is passed in explicitly and the same predicate as the
-- `parcels_select` policy in 01scheme.sql is re-applied here, so the intended
-- restriction (CENTRAL sees all; everyone else sees only their own rows)
-- remains in force.
--
-- SAFETY: this script only ADDS a function. It does not drop, truncate or
-- update any table or any existing data, so it is safe to run against a
-- database that already holds live records. Re-running it is a no-op.
--
-- Only real columns are returned. The demo fixture in the frontend carries
-- richer fields (village, taluka, risk_score, compensation_progress_pct,
-- possession_status, rr_status, main_bottleneck) that do NOT exist as columns
-- in this schema, so they are omitted rather than invented. The map renders
-- those metrics only when present.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.parcels_geojson(
    p_project_code TEXT DEFAULT NULL,
    p_status       public.parcel_status DEFAULT NULL,
    p_user_id      UUID DEFAULT NULL,
    p_role         public.user_role DEFAULT NULL
)
RETURNS jsonb
LANGUAGE sql
STABLE
AS $$
    SELECT jsonb_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(
            jsonb_agg(
                jsonb_build_object(
                    'type', 'Feature',
                    'properties', jsonb_build_object(
                        'id',             lp.id,
                        'ulpin',          lp.ulpin,
                        'khasra_no',      lp.khasra_survey_no,
                        'status',         lp.status,
                        'pending_with_role', lp.pending_with_role,
                        'project_code',   pr.project_code,
                        'stage',          pr.current_stage,
                        -- Derived from the stored polygon, not invented:
                        -- ST_Area over geography returns true square metres.
                        'area_sq_meters', ROUND(ST_Area(lp.geom::geography)::numeric, 2)
                    ),
                    'geometry', ST_AsGeoJSON(lp.geom)::jsonb
                )
            ),
            '[]'::jsonb
        )
    )
    FROM public.land_parcels lp
    JOIN public.projects pr ON pr.id = lp.project_id
    WHERE (p_project_code IS NULL OR pr.project_code = p_project_code)
      AND (p_status       IS NULL OR lp.status = p_status)
      -- Mirrors the `parcels_select` RLS policy. Fails closed: a non-CENTRAL
      -- caller with no resolvable user id matches nothing.
      AND (
            p_role = 'CENTRAL'::public.user_role
            OR lp.created_by = p_user_id
          );
$$;

COMMENT ON FUNCTION public.parcels_geojson(TEXT, public.parcel_status, UUID, public.user_role) IS
    'GeoJSON FeatureCollection of land parcels for the BHU-DRISHTI map. Caller scope is enforced explicitly because the API uses a service_role key that bypasses RLS.';

-- PostgREST can only invoke functions the calling role may EXECUTE.
GRANT EXECUTE ON FUNCTION public.parcels_geojson(TEXT, public.parcel_status, UUID, public.user_role) TO authenticated;
GRANT EXECUTE ON FUNCTION public.parcels_geojson(TEXT, public.parcel_status, UUID, public.user_role) TO service_role;
