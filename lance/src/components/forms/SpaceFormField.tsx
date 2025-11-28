"use client";

import { Input } from "@/components/ui/input";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Control, FieldPath, FieldValues } from "react-hook-form";
import "./SpaceFormField.css";

interface SpaceFormFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> {
  control: Control<TFieldValues>;
  name: TName;
  label: string;
  placeholder?: string;
  type?: string;
  helperText?: string;
  className?: string;
}

export function SpaceFormField<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  control,
  name,
  label,
  placeholder = "",
  type = "text",
  helperText,
  className = "",
}: SpaceFormFieldProps<TFieldValues, TName>) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className={`space-form-field ${className}`}>
          <FormLabel className="space-form-label">{label}</FormLabel>
          {helperText && <p className="space-form-helper-text">{helperText}</p>}
          <FormControl>
            <Input
              type={type}
              placeholder={placeholder}
              className="space-form-input"
              {...field}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}
