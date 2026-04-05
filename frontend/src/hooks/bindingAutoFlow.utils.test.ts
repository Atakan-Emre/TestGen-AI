import { describe, expect, it } from 'vitest';
import {
  buildAutoBindingProfileName,
  describeAutoBindingSummary,
  mapReviewReasonsToLabels,
  summarizeBindingRules,
} from './bindingAutoFlow.utils';

describe('bindingAutoFlow utils', () => {
  it('creates deterministic Turkish-safe profile names', () => {
    const profileName = buildAutoBindingProfileName(
      {
        scenario_name: '4nisantest',
        scenario_id: 1,
        json_file_id: 3,
        json_file_name: 'header-orj.json',
        variable_profiles: ['variablesHeader'],
      },
      ['variablesHeader'],
      ['bsc', 'ngi', 'ngv', 'opt']
    );

    expect(profileName).toContain('binding_auto_4nisantest');
    expect(profileName).toContain('variablesheader');
  });

  it('recommends review when generated or suggested bindings exist', () => {
    const summary = summarizeBindingRules([
      {
        json_path: 'a',
        schema_type: 'id',
        suggested_variable_key: 'a',
        variable_key: 'a',
        confidence: 1,
        status: 'matched',
        action: 'use_variable',
        approved: true,
        locked: false,
        generator_scope: ['bsc'],
      },
      {
        json_path: 'b',
        schema_type: 'string',
        suggested_variable_key: null,
        variable_key: null,
        confidence: 0.4,
        status: 'generated',
        action: 'generate_dynamic',
        approved: false,
        locked: false,
        generator_scope: ['bsc'],
      } as any,
    ]);

    expect(summary.reviewRecommended).toBe(true);
    expect(summary.generated).toBe(1);
  });

  it('renders Turkish review copy for backend auto summary', () => {
    expect(
      describeAutoBindingSummary({
        total_fields: 23,
        matched_fields: 7,
        suggested_fields: 2,
        generated_fields: 3,
        template_fields: 8,
        bound_fields: 7,
        approved_fields: 15,
        match_ratio: 0.3,
        average_confidence: 0.81,
        min_confidence: 0.2,
        review_recommended: true,
        review_reasons: ['generated_fields_present'],
      })
    ).toContain('Review önerilir');
  });

  it('maps backend review reason codes to Turkish labels', () => {
    expect(
      mapReviewReasonsToLabels([
        'generated_fields_present',
        'manual_review_for_mid_confidence_fields',
      ])
    ).toEqual([
      'Bazı alanlar dinamik üretim olarak bırakıldı',
      'Bazı alanlar öneri seviyesinde kaldı',
    ]);
  });
});
