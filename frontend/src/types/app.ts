import type { LLMProviderType, SearchProviderType } from './api'

export type ApiStatus = 'checking' | 'online' | 'offline'

export type EditableJobField =
  | 'title'
  | 'company_name'
  | 'role_category'
  | 'salary_range'
  | 'salary_period'
  | 'base_location'
  | 'education_requirement'
  | 'experience_requirement'
  | 'skillsText'
  | 'responsibilitiesText'
  | 'requirementsText'
  | 'bonusPointsText'

export type JobEditDraft = Record<EditableJobField, string>

export type LLMProviderDraft = {
  name: string
  provider_type: LLMProviderType
  api_key: string
  base_url: string
  model: string
  enabled: boolean
}

export type SearchProviderDraft = {
  name: string
  provider_type: SearchProviderType
  api_key: string
  base_url: string
  enabled: boolean
}

export type ThemePreference = 'auto' | 'light' | 'dark'
export type ThemeMode = 'light' | 'dark'
export type PageId = 'providers' | 'debug' | 'import' | 'jobs' | 'roles' | 'learning'

export type RoleSummary = {
  name: string
  jobCount: number
  titles: string[]
  companies: string[]
  baseLocations: string[]
  salarySamples: string[]
  educationRequirements: string[]
  experienceRequirements: string[]
  topSkills: string[]
  commonResponsibilities: string[]
  commonRequirements: string[]
  commonBonusPoints: string[]
}

export type MindMapNode = {
  id: string
  title: string
  nodeType: string
  level: string
  sourceFields: string[]
  evidence: string[]
  children: MindMapNode[]
}

export type MindMapBranch = {
  id: string
  title: string
  side: 'left' | 'right'
  x: number
  y: number
  color: string
  items: string[]
  nodes: MindMapNode[]
  sourceFields: string[]
  evidence: string[]
  focus: string
}

export type TextInputConfig = {
  label: string
  placeholder: string
}
