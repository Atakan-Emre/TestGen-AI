import { useEffect, useMemo, useState } from 'react';
import { bindingApi } from '../api/binding';
import type {
  BindingAutoResolveSummary,
  BindingFieldRule,
  BindingGeneratorKey,
  BindingProfileSource,
} from '../types/binding';
import { extractVariableProfileNames } from './bindingStudio.utils';
import { buildAutoBindingProfileName } from './bindingAutoFlow.utils';

export interface UseBindingAutoFlowParams {
  enabled?: boolean;
  jsonContent?: unknown;
  selectedVariables: string[];
  selectedGenerators: BindingGeneratorKey[];
  source: BindingProfileSource;
}

export const useBindingAutoFlow = ({
  enabled = true,
  selectedVariables,
  selectedGenerators,
  source,
}: UseBindingAutoFlowParams) => {
  const [rules, setRules] = useState<BindingFieldRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<BindingAutoResolveSummary | null>(null);
  const [autoProfileName, setAutoProfileName] = useState<string>('');
  const [refreshToken, setRefreshToken] = useState(0);

  const selectedVariableProfiles = useMemo(
    () => extractVariableProfileNames(selectedVariables),
    [selectedVariables]
  );
  const activeVariableProfile = selectedVariableProfiles[0];
  const autoProfileDraft = useMemo(
    () => buildAutoBindingProfileName(source, selectedVariableProfiles, selectedGenerators),
    [source, selectedVariableProfiles, selectedGenerators]
  );
  const canResolve =
    enabled &&
    Boolean(source.json_file_id) &&
    Boolean(activeVariableProfile) &&
    selectedGenerators.length > 0;

  useEffect(() => {
    let cancelled = false;

    const loadAutoBinding = async () => {
      if (!canResolve) {
        setRules([]);
        setSummary(null);
        setAutoProfileName('');
        setError(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const result = await bindingApi.autoResolve({
          json_file_id: Number(source.json_file_id),
          variables_profile: activeVariableProfile!,
          generators: selectedGenerators,
          profile_name: autoProfileDraft,
          description: `${source.json_file_name || 'JSON şablonu'} için otomatik eşleştirme`,
        });

        if (cancelled) {
          return;
        }

        setRules(result.suggestion.fields);
        setSummary(result.summary);
        setAutoProfileName(result.profile_name);
      } catch (err) {
        if (cancelled) {
          return;
        }
        const errorMessage = err instanceof Error ? err.message : 'Otomatik binding önerileri üretilemedi';
        setError(errorMessage);
        setRules([]);
        setSummary(null);
        setAutoProfileName('');
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadAutoBinding();

    return () => {
      cancelled = true;
    };
  }, [
    activeVariableProfile,
    autoProfileDraft,
    canResolve,
    refreshToken,
    selectedGenerators,
    source.json_file_id,
    source.json_file_name,
  ]);

  const ensureAutoProfile = async () => {
    if (!canResolve) {
      throw new Error('Otomatik binding için JSON ve variables profili seçilmeli');
    }
    if (autoProfileName) {
      return autoProfileName;
    }
    setRefreshToken((current) => current + 1);
    throw new Error('Otomatik binding profili henüz hazır değil');
  };

  const resetAutoProfile = () => {
    setAutoProfileName('');
    setSummary(null);
    setRules([]);
    setError(null);
  };

  const refreshAutoProfile = () => {
    setRefreshToken((current) => current + 1);
  };

  return {
    rules,
    loading,
    error,
    summary,
    autoProfileName,
    canResolve,
    ensureAutoProfile,
    resetAutoProfile,
    refreshAutoProfile,
  };
};
