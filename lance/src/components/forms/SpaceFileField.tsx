"use client";

import { FormLabel } from "@/components/ui/form";
import Image from "next/image";
import "./SpaceFileField.css";

interface SpaceFileFieldProps {
  label: string;
  helperText?: string;
  accept?: string;
  id: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  preview?: string | null;
  buttonText?: string;
  className?: string;
}

export function SpaceFileField({
  label,
  helperText,
  accept = "image/*",
  id,
  onChange,
  preview,
  buttonText = "Upload file",
  className = "",
}: SpaceFileFieldProps) {
  return (
    <div className={`space-file-field ${className}`}>
      <FormLabel className="space-form-label">{label}</FormLabel>
      {helperText && <p className="space-form-helper-text">{helperText}</p>}
      <input
        type="file"
        accept={accept}
        className="space-file-input"
        id={id}
        onChange={onChange}
      />
      <label htmlFor={id} className="space-file-label">
        {preview ? "Change File" : buttonText}
      </label>
      {preview && (
        <div className="space-file-preview">
          <Image
            src={preview}
            alt="File preview"
            width={200}
            height={200}
            style={{ objectFit: "contain" }}
          />
        </div>
      )}
    </div>
  );
}
