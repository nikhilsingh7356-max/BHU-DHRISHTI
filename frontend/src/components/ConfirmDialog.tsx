"use client";

import React from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger,
  onConfirm,
  onCancel,
  loading,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-2">{title}</h3>
          <p className="text-sm text-slate-600 mb-6">{message}</p>
          <div className="flex justify-end gap-3">
            <button className="btn-secondary" onClick={onCancel} disabled={loading}>
              {cancelLabel}
            </button>
            <button
              className={danger ? "btn-danger" : "btn-primary"}
              onClick={onConfirm}
              disabled={loading}
            >
              {loading ? "Processing..." : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
