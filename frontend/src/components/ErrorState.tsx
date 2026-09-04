"use client";

import React from "react";

export default function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="card p-10 text-center flex flex-col items-center">
      <div className="text-red-400 mb-3">
        <svg className="w-14 h-14 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <div className="text-slate-600 mb-1 font-medium">Unable to load data</div>
      {message && <div className="text-sm text-slate-400 mb-3">{message}</div>}
      {onRetry && (
        <button className="btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
