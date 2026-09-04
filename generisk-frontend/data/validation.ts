export interface ValidationMetrics {
  auroc: number;
  precision: number;
  recall: number;
  specificity: number;
  f1: number;
  balancedAccuracy: number;
  threshold: number;
  totalVariants: number;
  pathogenicVariants: number;
  benignVariants: number;
  successfullyScored: number;
}

export const validationMetrics: ValidationMetrics = {
  auroc: 0.971,
  precision: 1.0,
  recall: 0.921,
  specificity: 1.0,
  f1: 0.959,
  balancedAccuracy: 0.961,
  threshold: -0.000497677146574893,
  totalVariants: 47,
  pathogenicVariants: 38,
  benignVariants: 9,
  successfullyScored: 47,
};