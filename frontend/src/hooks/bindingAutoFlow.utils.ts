import type {
  BindingAutoResolveSummary,
  BindingFieldRule,
  BindingGeneratorKey,
  BindingProfileSource,
} from '../types/binding';

export interface BindingAutoFlowSummary {
  total: number;
  matched: number;
  suggested: number;
  generated: number;
  template: number;
  approved: number;
  locked: number;
  averageConfidence: number;
  reviewRecommended: boolean;
  reviewReason: string;
}

const REVIEW_REASON_LABELS: Record<string, string> = {
  generated_fields_present: 'Bazı alanlar dinamik üretim olarak bırakıldı',
  manual_review_for_mid_confidence_fields: 'Bazı alanlar öneri seviyesinde kaldı',
  low_match_ratio: 'Eşleşme oranı düşük kaldı',
  low_confidence_bindings: 'Bazı binding kararlarının güven skoru düşük',
};

const slugify = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/gi, '_')
    .replace(/_{2,}/g, '_')
    .replace(/^_+|_+$/g, '');

export const buildAutoBindingProfileName = (
  source: BindingProfileSource,
  selectedVariableProfiles: string[],
  selectedGenerators: BindingGeneratorKey[]
) => {
  const scenarioName = source.scenario_name || source.json_file_name || 'binding-flow';
  const variablePart = selectedVariableProfiles.join('_') || 'variables';
  const generatorPart = selectedGenerators.map((generator) => generator.toUpperCase()).join('_') || 'ALL';
  return slugify(`binding_auto_${scenarioName}_${variablePart}_${generatorPart}`);
};

export const summarizeBindingRules = (rules: BindingFieldRule[]): BindingAutoFlowSummary => {
  const total = rules.length;
  const matched = rules.filter((rule) => rule.status === 'matched').length;
  const suggested = rules.filter((rule) => rule.status === 'suggested').length;
  const generated = rules.filter((rule) => rule.status === 'generated').length;
  const template = rules.filter((rule) => rule.status === 'template').length;
  const approved = rules.filter((rule) => rule.approved).length;
  const locked = rules.filter((rule) => rule.locked).length;
  const averageConfidence = total
    ? Number((rules.reduce((sum, rule) => sum + Number(rule.confidence || 0), 0) / total).toFixed(2))
    : 0;

  const reviewRecommended = suggested > 0 || generated > 0 || averageConfidence < 0.92;
  const reviewReason = reviewRecommended
    ? generated > 0
      ? 'Bazı alanlar otomatikte üretildi. Gözden geçirmeniz önerilir.'
      : suggested > 0
        ? 'Bazı alanlar öneri seviyesinde kaldı. Gözden geçirmeniz önerilir.'
        : 'Ortalama güven seviyesi düşük. Gözden geçirmeniz önerilir.'
    : 'Otomatik eşleştirme yeterli görünüyor.';

  return {
    total,
    matched,
    suggested,
    generated,
    template,
    approved,
    locked,
    averageConfidence,
    reviewRecommended,
    reviewReason,
  };
};

export const describeAutoBindingSummary = (summary: BindingAutoResolveSummary | null) => {
  if (!summary) {
    return 'Otomatik eşleştirme henüz hazır değil.';
  }

  if (!summary.review_recommended) {
    return 'Otomatik eşleştirme yeterli görünüyor. Review zorunlu değil.';
  }

  if (summary.generated_fields > 0) {
    return 'Bazı alanlar dinamik üretime bırakıldı. Review önerilir.';
  }

  if (summary.suggested_fields > 0) {
    return 'Bazı alanlar öneri seviyesinde kaldı. Review önerilir.';
  }

  return 'Otomatik eşleştirme tamamlandı fakat güven skoru nedeniyle review önerilir.';
};

export const mapReviewReasonsToLabels = (reasons: string[]) =>
  reasons.map((reason) => REVIEW_REASON_LABELS[reason] || reason);
