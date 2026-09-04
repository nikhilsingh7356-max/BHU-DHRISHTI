"use client";

import dynamic from "next/dynamic";
import { Parcel } from "@/lib/types";

const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => (
    <div className="w-full rounded-xl border border-slate-200 bg-slate-100 flex items-center justify-center" style={{ height: 520 }}>
      <span className="text-sm text-slate-400">Loading map...</span>
    </div>
  ),
});

export default function MapViewDynamic(props: { parcels: Parcel[]; height?: number | string; onParcelClick?: (parcel: Parcel) => void }) {
  return <MapView {...props} />;
}
