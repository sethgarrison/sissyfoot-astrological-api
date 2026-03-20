/**
 * TypeScript types for Natal Chart API data tables.
 * Matches GET response shapes and PATCH request bodies from /data/* endpoints.
 */

// --- Reference tables ---

export interface Planet {
  id: number;
  name: string;
  symbol: string | null;
  description: string | null;
  keywords: string | null;
}

export interface PlanetUpdate {
  symbol?: string | null;
  description?: string | null;
  keywords?: string | null;
}

export interface Sign {
  id: number;
  name: string;
  element: string | null;
  modality: string | null;
  archetypes_balanced: string | null;
  archetypes_unbalanced: string | null;
  journey: string | null;
  gifts: string | null;
  challenges: string | null;
  interpretation: string | null;
}

export interface SignUpdate {
  element?: string | null;
  modality?: string | null;
  archetypes_balanced?: string | null;
  archetypes_unbalanced?: string | null;
  journey?: string | null;
  gifts?: string | null;
  challenges?: string | null;
  interpretation?: string | null;
}

export interface House {
  id: number;
  number: number;
  type: string | null; // angular, succedent, cadent
  description: string | null;
  subtitle: string | null;
  keywords: string | null;
}

export interface HouseUpdate {
  type?: string | null;
  description?: string | null;
  subtitle?: string | null;
  keywords?: string | null;
}

export interface Aspect {
  id: number;
  name: string;
  angle_degrees: number | null;
  symbol: string | null;
  type: string | null; // conjunction, stressful, easy-flowing
}

export interface AspectUpdate {
  angle_degrees?: number | null;
  symbol?: string | null;
  type?: string | null;
}

// --- Big Three: Sun merged into signs; Moon/Ascendant in dedicated tables ---

export interface MoonSignInterpretation {
  id: number;
  sign: string;
  sign_id: number;
  nature: string | null;
  sources_of_contentment: string | null;
  keywords: string | null;
  interpretation: string | null;
}

export interface MoonSignInterpretationUpdate {
  nature?: string | null;
  sources_of_contentment?: string | null;
  keywords?: string | null;
  interpretation?: string | null;
}

export interface AscendantSignInterpretation {
  id: number;
  sign: string;
  sign_id: number;
  impression: string | null;
  appearance: string | null;
  childhood: string | null;
  balance: string | null;
  interpretation: string | null;
}

export interface AscendantSignInterpretationUpdate {
  impression?: string | null;
  appearance?: string | null;
  childhood?: string | null;
  balance?: string | null;
  interpretation?: string | null;
}

// --- Interpretation tables ---

export interface PlanetSignInterpretation {
  id: number;
  planet: string;
  sign: string;
  interpretation_text: string;
  interpretation_long: string | null;
  interpretation_short: string | null;
  keywords: string | null;
  retrograde_interpretation: string | null;
}

export interface PlanetSignInterpretationUpdate {
  interpretation_text?: string | null;
  interpretation_long?: string | null;
  interpretation_short?: string | null;
  keywords?: string | null;
  retrograde_interpretation?: string | null;
}

export interface PlanetHouseInterpretation {
  id: number;
  planet: string;
  house: number;
  interpretation_text: string;
  short_interpretation: string | null;
  retrograde_interpretation: string | null;
}

export interface PlanetHouseInterpretationUpdate {
  interpretation_text?: string | null;
  short_interpretation?: string | null;
  retrograde_interpretation?: string | null;
}

export interface AspectTypeInterpretation {
  id: number;
  type_key: string; // conjunction, stressful, easy-flowing
  interpretation_text: string;
}

export interface AspectTypeInterpretationUpdate {
  interpretation_text?: string | null;
}

export interface AspectInterpretation {
  id: number;
  aspect: string;
  interpretation_text: string;
}

export interface AspectInterpretationUpdate {
  interpretation_text?: string | null;
}

export interface PlanetAspectInterpretation {
  id: number;
  planet_1: string;
  planet_2: string;
  aspect: string;
  interpretation_text: string;
}

export interface PlanetAspectInterpretationUpdate {
  interpretation_text?: string | null;
}

export interface SignHouseInterpretation {
  id: number;
  house: number;
  sign: string;
  interpretation_text: string;
}

export interface SignHouseInterpretationUpdate {
  interpretation_text?: string | null;
}

export interface ChartShapeInterpretation {
  id: number;
  shape_key: string;
  interpretation_text: string;
}

export interface ChartShapeInterpretationUpdate {
  interpretation_text?: string | null;
}

export interface ChartDistributionInterpretation {
  id: number;
  distribution_key: string;
  interpretation_text: string;
}

export interface ChartDistributionInterpretationUpdate {
  interpretation_text?: string | null;
}

export interface ModalityElementDistributionInterpretation {
  id: number;
  distribution_key: string;
  interpretation_text: string;
}

export interface ModalityElementDistributionInterpretationUpdate {
  interpretation_text?: string | null;
}

// --- API path helpers ---

export const DATA_ENDPOINTS = {
  planets: "/data/planets",
  signs: "/data/signs",  // Sun-in-sign (Big Three) fields: archetypes_balanced, journey, etc.
  houses: "/data/houses",
  aspects: "/data/aspects",
  moon: "/data/moon",
  ascendant: "/data/ascendant",
  planetSign: "/data/planet-sign",
  planetHouse: "/data/planet-house",
  aspectType: "/data/aspect-type",
  aspectGeneric: "/data/aspect-generic",
  planetAspect: "/data/planet-aspect",
  signHouse: "/data/sign-house",
  chartShape: "/data/chart-shape",
  chartDistribution: "/data/chart-distribution",
  modalityElement: "/data/modality-element",
} as const;
