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
import "./SpaceColorField.css";

interface SpaceColorFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> {
  control: Control<TFieldValues>;
  name: TName;
  label: string;
  placeholder?: string;
  className?: string;
}

export function SpaceColorField<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  control,
  name,
  label,
  placeholder = "",
  className = "",
}: SpaceColorFieldProps<TFieldValues, TName>) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem className={`space-color-field ${className}`}>
          <FormLabel className="space-form-label">{label}</FormLabel>
          <FormControl>
            <div className="space-color-input-wrapper">
              <input
                type="color"
                className="space-color-picker"
                value={field.value || "#3b82f6"}
                onChange={e => {
                  field.onChange(e.target.value);
                }}
                onBlur={field.onBlur}
              />
              <Input
                placeholder={placeholder}
                className="space-form-input"
                value={field.value || ""}
                onChange={e => {
                  field.onChange(e.target.value);
                }}
                onBlur={field.onBlur}
              />
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}
