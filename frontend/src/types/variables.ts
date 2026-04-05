export type VariableProfileInfo = {
  name: string;
  format: 'txt' | 'json' | 'yaml';
  updatedAt?: string;
  sizeBytes?: number;
};

export type VariableProfilesResponse = {
  success: boolean;
  data: VariableProfileInfo[];
  message?: string;
};

export type VariablePreviewResponse = {
  success: boolean;
  data: Record<string, string>;
  message?: string;
};

export type VariableUploadRequest = {
  name: string;
  format: 'txt' | 'json' | 'yaml';
};
