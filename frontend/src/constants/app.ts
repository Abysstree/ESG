import type { LLMProviderType, SearchProviderType } from '../types/api'
import type { PageId, ThemePreference } from '../types/app'

export const confidenceLabels: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

export const statusLabels: Record<string, string> = {
  mock_extracted: '规则抽取',
  llm_extracted: 'LLM抽取',
  llm_failed_mock_extracted: 'LLM失败，规则兜底',
  user_edited: '用户编辑',
  draft: '草稿',
  created: '已创建',
}

export const salaryPeriodLabels: Record<string, string> = {
  monthly: '月薪',
  daily: '日薪',
  yearly: '年薪',
}

export const providerTypeLabels: Record<LLMProviderType, string> = {
  deepseek: 'DeepSeek',
  openai_compatible: 'OpenAI 兼容',
  anthropic: 'Anthropic',
  google: 'Google Gemini',
}

export const providerDefaults: Record<
  LLMProviderType,
  { base_url: string; model: string; name: string }
> = {
  deepseek: {
    name: 'DeepSeek',
    base_url: 'https://api.deepseek.com',
    model: 'deepseek-v4-flash',
  },
  openai_compatible: {
    name: '自定义 OpenAI 兼容',
    base_url: 'https://api.openai.com/v1',
    model: 'gpt-4.1-mini',
  },
  anthropic: {
    name: 'Anthropic',
    base_url: 'https://api.anthropic.com',
    model: 'claude-sonnet-4-6',
  },
  google: {
    name: 'Google Gemini',
    base_url: 'https://generativelanguage.googleapis.com',
    model: 'gemini-3.5-flash',
  },
}

export const searchProviderTypeLabels: Record<SearchProviderType, string> = {
  exa: 'Exa',
  tavily: 'Tavily',
}

export const searchProviderDefaults: Record<
  SearchProviderType,
  { base_url: string; name: string }
> = {
  exa: {
    name: 'Exa',
    base_url: 'https://api.exa.ai',
  },
  tavily: {
    name: 'Tavily',
    base_url: 'https://api.tavily.com',
  },
}

export const THEME_STORAGE_KEY = 'esg-theme-preference'
export const AUTO_DARK_START_HOUR = 19
export const AUTO_DARK_END_HOUR = 7

export const themePreferenceLabels: Record<ThemePreference, string> = {
  auto: '自动',
  light: '浅色',
  dark: '深色',
}

export const pageLabels: Record<PageId, string> = {
  providers: 'API配置',
  debug: '抽取调试',
  import: '导入岗位',
  jobs: '岗位卡片',
  roles: '岗位大类',
  learning: '学习地图',
}

export const pageOrder: PageId[] = [
  'providers',
  'debug',
  'import',
  'jobs',
  'roles',
  'learning',
]

export const MIND_MAP_DEFAULT_ZOOM = 0.74
