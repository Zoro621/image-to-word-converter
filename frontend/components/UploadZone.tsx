"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, ImageIcon, X, FileImage } from "lucide-react";
import Image from "next/image";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  selectedFile?: File | null;
}

export default function UploadZone({ onFileSelect, disabled, selectedFile }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file) return;
      const ok = ["image/jpeg", "image/png", "image/webp"].includes(file.type);
      if (!ok) {
        alert("Please upload a JPG, PNG, or WebP image.");
        return;
      }
      const url = URL.createObjectURL(file);
      setPreview(url);
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
    onFileSelect(null as unknown as File);
  };

  return (
    <div
      className={`upload-zone ${isDragging ? "drag-over" : ""}`}
      style={{
        minHeight: 220,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "32px",
        opacity: disabled ? 0.5 : 1,
        pointerEvents: disabled ? "none" : "auto",
        transition: "all 0.2s",
      }}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      aria-label="Image upload zone"
    >
      <input
        type="file"
        accept=".jpg,.jpeg,.png,.webp"
        onChange={handleChange}
        id="image-upload"
        disabled={disabled}
      />

      <AnimatePresence mode="wait">
        {preview ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3 }}
            style={{ position: "relative", textAlign: "center" }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="Uploaded preview"
              style={{
                maxHeight: 160,
                maxWidth: "100%",
                borderRadius: "var(--radius-md)",
                objectFit: "contain",
                boxShadow: "var(--glow-sm)",
              }}
            />
            <button
              onClick={clearFile}
              style={{
                position: "absolute",
                top: -10,
                right: -10,
                background: "var(--accent-rose)",
                border: "none",
                borderRadius: "50%",
                width: 24,
                height: 24,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
              aria-label="Remove uploaded image"
            >
              <X size={13} color="#fff" />
            </button>
            <p style={{ marginTop: 10, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              <FileImage size={14} style={{ display: "inline", marginRight: 4 }} />
              {selectedFile?.name}
              {selectedFile ? ` · ${(selectedFile.size / 1024).toFixed(1)} KB` : ""}
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{ textAlign: "center" }}
          >
            {/* Animated icon */}
            <motion.div
              animate={{ y: [0, -6, 0] }}
              transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
              style={{
                width: 64,
                height: 64,
                borderRadius: "50%",
                background: "var(--accent-glow)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 16px",
              }}
            >
              <ImageIcon size={28} color="var(--accent-primary)" />
            </motion.div>

            <p style={{ fontWeight: 600, marginBottom: 6 }}>
              Drop your image here
            </p>
            <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: 12 }}>
              JPG, PNG, or WebP — handwritten notes, diagrams, forms
            </p>

            <motion.div
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                padding: "8px 20px",
                borderRadius: "var(--radius-md)",
                background: "var(--accent-glow)",
                border: "1px solid var(--accent-primary)",
                fontSize: "0.84rem",
                fontWeight: 600,
                color: "var(--accent-secondary)",
                cursor: "pointer",
              }}
            >
              <Upload size={14} />
              Browse files
            </motion.div>

            {isDragging && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                style={{
                  marginTop: 14,
                  fontSize: "0.88rem",
                  color: "var(--accent-primary)",
                  fontWeight: 600,
                }}
              >
                ✦ Release to upload
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
