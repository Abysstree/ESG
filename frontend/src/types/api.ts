export type SourceType = 'url' | 'text' | 'screenshot'

export type HealthResponse = {
  status: string
  service: string
}

export type RawImport = {
  id: number
  source_type: SourceType
  source_value: string
  raw_text: string | null
  status: string
  created_at: string
}

export type RawImportCreate = {
  source_type: SourceType
  source_value: string
  raw_text: string | null
}

export type JobCard = {
  id: number
  raw_import_id: number | null
  title: string
  company_name: string | null
  role_category: string | null
  salary_range: string | null
  salary_period: string | null
  base_location: string | null
  education_requirement: string | null
  experience_requirement: string | null
  responsibilities: string[]
  requirements: string[]
  bonus_points: string[]
  skills: string[]
  field_sources: Record<string, string>
  evidence: Record<string, string | null>
  confidence: string
  status: string
  is_pinned: boolean
  sort_order: number
  created_at: string
}

export type JobCardUpdate = Partial<
  Pick<
    JobCard,
    | 'title'
    | 'company_name'
    | 'role_category'
    | 'salary_range'
    | 'salary_period'
    | 'base_location'
    | 'education_requirement'
    | 'experience_requirement'
    | 'responsibilities'
    | 'requirements'
    | 'bonus_points'
    | 'skills'
    | 'confidence'
    | 'is_pinned'
    | 'sort_order'
  >
>

export type CompanyProfile = {
  id: number
  company_name: string
  summary: string | null
  industry: string | null
  financing_stage: string | null
  scale: string | null
  headquarters: string | null
  official_website: string | null
  official_careers_url: string | null
  source_urls: string[]
  field_sources: Record<string, string>
  evidence: Record<string, string | null>
  inference_notes: string[]
  confidence: string
  status: string
  created_at: string
  updated_at: string
}

export type LLMStatus = {
  provider: string
  configured: boolean
  model: string | null
  base_url: string | null
  active_provider_id: number | null
}

export type LLMProviderType = 'deepseek' | 'openai_compatible' | 'anthropic' | 'google'

export type LLMProviderConfig = {
  id: number
  name: string
  provider_type: LLMProviderType
  api_key_set: boolean
  base_url: string | null
  model: string | null
  enabled: boolean
  is_active: boolean
  created_at: string
}

export type LLMProviderConfigCreate = {
  name: string
  provider_type: LLMProviderType
  api_key?: string | null
  base_url: string | null
  model: string | null
  enabled: boolean
  is_active: boolean
}

export type LLMProviderConfigUpdate = Partial<LLMProviderConfigCreate>

export type SearchStatus = {
  provider: string
  configured: boolean
  base_url: string | null
  active_provider_id: number | null
}

export type SearchProviderType = 'exa' | 'tavily'

export type SearchProviderConfig = {
  id: number
  name: string
  provider_type: SearchProviderType
  api_key_set: boolean
  base_url: string | null
  enabled: boolean
  is_active: boolean
  created_at: string
}

export type SearchProviderConfigCreate = {
  name: string
  provider_type: SearchProviderType
  api_key?: string | null
  base_url: string | null
  enabled: boolean
  is_active: boolean
}

export type SearchProviderConfigUpdate = Partial<SearchProviderConfigCreate>

export type LLMExtractedJobCard = {
  title: string
  company_name: string | null
  role_category: string
  salary_range: string | null
  salary_period: string | null
  base_location: string | null
  education_requirement: string | null
  experience_requirement: string | null
  responsibilities: string[]
  requirements: string[]
  bonus_points: string[]
  skills: string[]
  field_sources: Record<string, string>
  evidence: Record<string, string | null>
  inference_notes: string[]
  confidence: string
}

export type LLMExtractQualityChecks = {
  missing_fields: string[]
  inferred_fields: string[]
  original_posting_fields: string[]
  evidence_fields: string[]
  field_source_coverage: number
  required_field_count: number
  confidence: string
}

export type LLMExtractPreview = {
  provider: string
  mode: string
  model: string | null
  base_url: string | null
  prompt?: string
  extracted_schema?: LLMExtractedJobCard
  normalized_job_card?: LLMExtractedJobCard
  job_card?: LLMExtractedJobCard
  quality_checks?: LLMExtractQualityChecks
  raw_model_response?: unknown
  raw_response?: unknown
  provider_result?: unknown
}

export type LLMLearningMapNode = {
  id: string
  title: string
  node_type: string
  level: string
  source_fields: string[]
  evidence: string[]
  children: LLMLearningMapNode[]
}

export type LLMLearningMapBranch = {
  id: string
  title: string
  focus: string
  source_fields: string[]
  evidence: string[]
  nodes: LLMLearningMapNode[]
}

export type LLMRoleProfile = {
  role_category: string
  summary: string
  job_count: number
  representative_titles: string[]
  core_responsibilities: string[]
  common_requirements: string[]
  high_frequency_skills: string[]
  bonus_signals: string[]
  learning_map: {
    center_title: string
    center_subtitle: string | null
    branches: LLMLearningMapBranch[]
  }
  field_sources: Record<string, string>
  evidence: Record<string, string[]>
  inference_notes: string[]
  confidence: string
}

export type LLMRoleProfileResult = {
  provider: string
  mode: string
  input: Record<string, unknown>
  role_profile: LLMRoleProfile
  raw_model_response: unknown
  status: string
  updated_at: string | null
}

export type StoredRoleProfile = LLMRoleProfileResult & {
  id: number
  role_category: string
  job_count: number
  created_at: string
  updated_at: string
}
