"use client";

import React from "react";

export default function Skeleton({ lines = 4 }: { lines?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="shimmer" style={{ width: `${100 - i * 10}%`, height: i === 0 ? 32 : 20 }} />
      ))}
    </div>
  );
}
