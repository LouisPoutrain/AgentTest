/**
 * Registry des champs de formulaire pour le wizard d'automatisation.
 * Définit les types de champs, leurs validations et leurs dépendances.
 */

import type { FieldType, TemplateField } from "./templates";

export interface FieldSchema extends TemplateField {
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    custom?: (value: string) => string | null; // returns error message or null
  };
  dependsOn?: { key: string; value: string }; // only show when this key equals this value
}

/**
 * Map of all available field types with their default behaviors.
 */
export const FIELD_TYPES: Record<FieldType, { label: string; icon: string; multiline: boolean }> = {
  text: { label: "Texte", icon: "A", multiline: false },
  textarea: { label: "Texte long", icon: "¶", multiline: true },
  path: { label: "Chemin", icon: "/", multiline: false },
  select: { label: "Sélection", icon: "▾", multiline: false },
  url: { label: "URL", icon: "@", multiline: false },
  toggle: { label: "Activation", icon: "⊘", multiline: false },
};

/**
 * Validate a field value against its schema.
 * Returns an error message string if invalid, or null if valid.
 */
export function validateField(
  value: string,
  field: FieldSchema
): string | null {
  if (field.required && !value.trim()) {
    return "Ce champ est requis";
  }

  if (!value.trim()) return null;

  const validation = field.validation;
  if (!validation) return null;

  if (validation.minLength && value.length < validation.minLength) {
    return "Minimum " + validation.minLength + " caractères";
  }

  if (validation.maxLength && value.length > validation.maxLength) {
    return "Maximum " + validation.maxLength + " caractères";
  }

  if (validation.pattern) {
    const regex = new RegExp(validation.pattern);
    if (!regex.test(value)) {
      return "Format invalide";
    }
  }

  if (validation.custom) {
    return validation.custom(value);
  }

  return null;
}

/**
 * Check if a field should be visible based on dependsOn.
 */
export function isFieldVisible(
  field: FieldSchema,
  inputs: Record<string, string>
): boolean {
  if (!field.dependsOn) return true;
  return inputs[field.dependsOn.key] === field.dependsOn.value;
}
