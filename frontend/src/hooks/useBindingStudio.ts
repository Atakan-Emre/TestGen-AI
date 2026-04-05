import { useEffect, useMemo, useState } from 'react';
import { bindingApi } from '../api/binding';
import { variablesApi } from '../api/variables';
import type {
  BindingFieldRule,
  BindingGeneratorKey,
  BindingProfile,
  BindingProfilePayload,
  BindingProfileSource,
  BindingProfileSummary,
} from '../types/binding';
import {
  buildBindingSuggestions,
  extractVariableProfileNames,
  hydrateBindingProfile,
} from './bindingStudio.utils';

export interface UseBindingStudioParams {
  jsonContent: unknown;
  selectedVariables: string[];
  selectedGenerators: BindingGeneratorKey[];
  source: BindingProfileSource;
}

export const useBindingStudio = ({
  jsonContent,
  selectedVariables,
  selectedGenerators,
  source,
}: UseBindingStudioParams) => {
  const [rules, setRules] = useState<BindingFieldRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedProfiles, setSavedProfiles] = useState<BindingProfileSummary[]>([]);
  const [selectedProfileName, setSelectedProfileName] = useState<string>('');
  const [profileNameDraft, setProfileNameDraft] = useState<string>('');
  const [refreshToken, setRefreshToken] = useState(0);

  const selectedVariableProfiles = useMemo(
    () => extractVariableProfileNames(selectedVariables),
    [selectedVariables]
  );

  const refreshSavedProfiles = async () => {
    const profiles = await bindingApi.listProfiles();
    setSavedProfiles(profiles);
  };

  useEffect(() => {
    refreshSavedProfiles().catch(() => setSavedProfiles([]));
  }, []);

  useEffect(() => {
    const loadSuggestions = async () => {
      if (!jsonContent) {
        setRules([]);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const parsedJson = typeof jsonContent === 'string' ? JSON.parse(jsonContent) : jsonContent;
        const activeProfileName = selectedVariableProfiles[0];

        if (activeProfileName && source.json_file_id) {
          try {
            const suggestions = await bindingApi.suggestBindings({
              json_file_id: source.json_file_id,
              variables_profile: activeProfileName,
              generators: selectedGenerators,
            });
            setRules(suggestions);
            setSelectedProfileName('');
            return;
          } catch (suggestError) {
            console.warn('Backend binding suggestion başarısız, local fallback kullanılıyor', suggestError);
          }
        }

        const variableEntries = await Promise.all(
          selectedVariableProfiles.map(async (profileName) => {
            try {
              const profile = await variablesApi.fetchProfile(profileName);
              return Object.entries(profile);
            } catch {
              return [];
            }
          })
        );

        const variablesMap = Object.fromEntries(variableEntries.flat());
        const suggestions = buildBindingSuggestions({
          jsonContent: parsedJson,
          variablesMap,
          selectedGenerators,
          source,
        });

        setRules(suggestions);
        setSelectedProfileName('');
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Binding önerileri üretilemedi';
        setError(errorMessage);
        setRules([]);
      } finally {
        setLoading(false);
      }
    };

    loadSuggestions();
  }, [jsonContent, selectedGenerators, selectedVariableProfiles, source, refreshToken]);

  const updateRule = (
    jsonPath: string,
    patch: Partial<Pick<BindingFieldRule, 'action' | 'variable_key' | 'approved' | 'locked' | 'generator_scope'>>
  ) => {
    setRules((current) =>
      current.map((rule) =>
        rule.json_path === jsonPath
          ? {
              ...rule,
              ...patch,
              approved: patch.approved ?? rule.approved,
              locked: patch.locked ?? rule.locked,
            }
          : rule
      )
    );
    setSelectedProfileName('');
  };

  const applyProfile = (profile: BindingProfile) => {
    setRules((current) =>
      current.map((rule) => {
        const override = profile.rules.find((profileRule) => profileRule.json_path === rule.json_path);
        return override ? { ...rule, ...override } : rule;
      })
    );
    setSelectedProfileName(profile.name);
    setProfileNameDraft(profile.name);
  };

  const saveCurrentProfile = async (name?: string) => {
    const profileName = (name || profileNameDraft || '').trim();
    if (!profileName) {
      throw new Error('Binding profil adı girilmeli');
    }

    const payload: BindingProfilePayload = hydrateBindingProfile(profileName, rules, source);
    const saved = await bindingApi.saveProfile(payload);
    await refreshSavedProfiles();
    setSelectedProfileName(saved.name);
    setProfileNameDraft(saved.name);
    return saved;
  };

  const loadSelectedProfile = async (name: string) => {
    const profile = await bindingApi.getProfile(name);
    if (!profile) {
      throw new Error(`Binding profili bulunamadı: ${name}`);
    }
    applyProfile(profile);
    return profile;
  };

  const deleteProfile = async (name: string) => {
    await bindingApi.deleteProfile(name);
    await refreshSavedProfiles();
    if (selectedProfileName === name) {
      setSelectedProfileName('');
    }
  };

  const resetSuggestions = () => {
    setSelectedProfileName('');
    setRefreshToken((current) => current + 1);
  };

  return {
    rules,
    setRules,
    loading,
    error,
    savedProfiles,
    selectedProfileName,
    profileNameDraft,
    setProfileNameDraft,
    setSelectedProfileName,
    updateRule,
    saveCurrentProfile,
    loadSelectedProfile,
    deleteProfile,
    applyProfile,
    resetSuggestions,
    refreshSavedProfiles,
  };
};
