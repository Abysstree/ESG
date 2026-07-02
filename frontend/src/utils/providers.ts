import { providerDefaults, searchProviderDefaults } from '../constants/app'
import type {
  LLMProviderConfig,
  LLMProviderType,
  SearchProviderConfig,
  SearchProviderType,
} from '../types/api'
import type { LLMProviderDraft, SearchProviderDraft } from '../types/app'

export function createProviderDraft(providerType: LLMProviderType): LLMProviderDraft {
  const defaults = providerDefaults[providerType]
  return {
    name: defaults.name,
    provider_type: providerType,
    api_key: '',
    base_url: defaults.base_url,
    model: defaults.model,
    enabled: true,
  }
}

export function providerConfigToDraft(provider: LLMProviderConfig): LLMProviderDraft {
  return {
    name: provider.name,
    provider_type: provider.provider_type,
    api_key: '',
    base_url: provider.base_url ?? '',
    model: provider.model ?? '',
    enabled: provider.enabled,
  }
}

export function createSearchProviderDraft(
  providerType: SearchProviderType,
): SearchProviderDraft {
  const defaults = searchProviderDefaults[providerType]
  return {
    name: defaults.name,
    provider_type: providerType,
    api_key: '',
    base_url: defaults.base_url,
    enabled: true,
  }
}

export function searchProviderConfigToDraft(
  provider: SearchProviderConfig,
): SearchProviderDraft {
  return {
    name: provider.name,
    provider_type: provider.provider_type,
    api_key: '',
    base_url: provider.base_url ?? '',
    enabled: provider.enabled,
  }
}
