import type { Dispatch, FormEvent, SetStateAction } from 'react'
import { providerTypeLabels, searchProviderTypeLabels } from '../constants/app'
import type {
  LLMProviderConfig,
  LLMProviderType,
  SearchProviderConfig,
  SearchProviderType,
  SearchStatus,
} from '../types/api'
import type { LLMProviderDraft, SearchProviderDraft } from '../types/app'

type ProviderPageProps = {
  llmProviders: LLMProviderConfig[]
  selectedProviderId: number | 'new' | null
  providerDraft: LLMProviderDraft
  isSavingProvider: boolean
  searchProviders: SearchProviderConfig[]
  searchStatus: SearchStatus | null
  selectedSearchProviderId: number | 'new' | null
  searchProviderDraft: SearchProviderDraft
  isSavingSearchProvider: boolean
  setProviderDraft: Dispatch<SetStateAction<LLMProviderDraft>>
  setSearchProviderDraft: Dispatch<SetStateAction<SearchProviderDraft>>
  onSelectProvider: (provider: LLMProviderConfig) => void
  onNewProvider: () => void
  onProviderTypeChange: (providerType: LLMProviderType) => void
  onSaveProvider: () => void
  onActivateProvider: (providerId: number) => void
  onDeleteProvider: (provider: LLMProviderConfig) => void
  onSelectSearchProvider: (provider: SearchProviderConfig) => void
  onNewSearchProvider: () => void
  onSearchProviderTypeChange: (providerType: SearchProviderType) => void
  onSaveSearchProvider: () => void
  onActivateSearchProvider: (providerId: number) => void
  onDeleteSearchProvider: (provider: SearchProviderConfig) => void
}

function ProviderPage({
  llmProviders,
  selectedProviderId,
  providerDraft,
  isSavingProvider,
  searchProviders,
  searchStatus,
  selectedSearchProviderId,
  searchProviderDraft,
  isSavingSearchProvider,
  setProviderDraft,
  setSearchProviderDraft,
  onSelectProvider,
  onNewProvider,
  onProviderTypeChange,
  onSaveProvider,
  onActivateProvider,
  onDeleteProvider,
  onSelectSearchProvider,
  onNewSearchProvider,
  onSearchProviderTypeChange,
  onSaveSearchProvider,
  onActivateSearchProvider,
  onDeleteSearchProvider,
}: ProviderPageProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSaveProvider()
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSaveSearchProvider()
  }

  return (
    <>
      <section className="records-section llm-settings" id="providers">
        <div className="section-heading">
          <p className="eyebrow">Model Providers</p>
          <h3>模型接口配置</h3>
        </div>

        <div className="provider-layout">
          <div className="provider-list">
            {llmProviders.map((provider) => (
              <button
                key={provider.id}
                className={selectedProviderId === provider.id ? 'selected' : ''}
                type="button"
                onClick={() => onSelectProvider(provider)}
              >
                <span>{provider.name}</span>
                <small>
                  {providerTypeLabels[provider.provider_type]} ·{' '}
                  {provider.api_key_set ? '已加密保存' : '未配置密钥'}
                </small>
                {provider.is_active ? <strong>当前</strong> : null}
              </button>
            ))}
            <button
              className={selectedProviderId === 'new' ? 'selected' : ''}
              type="button"
              onClick={onNewProvider}
            >
              <span>新增提供商</span>
              <small>DeepSeek / OpenAI / Anthropic / Gemini</small>
            </button>
          </div>

          <form className="provider-form" onSubmit={handleSubmit}>
            <label>
              <span>提供商名称</span>
              <input
                value={providerDraft.name}
                autoComplete="off"
                placeholder="例如 OpenAI"
                onChange={(event) =>
                  setProviderDraft((draft) => ({
                    ...draft,
                    name: event.target.value,
                  }))
                }
              />
            </label>

            <label>
              <span>提供商类型</span>
              <select
                value={providerDraft.provider_type}
                onChange={(event) =>
                  onProviderTypeChange(event.target.value as LLMProviderType)
                }
              >
                <option value="deepseek">DeepSeek</option>
                <option value="openai_compatible">OpenAI 兼容</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google Gemini</option>
              </select>
            </label>

            <label className="provider-form-wide">
              <span>API Key</span>
              <input
                value={providerDraft.api_key}
                type="password"
                autoComplete="new-password"
                placeholder={
                  selectedProviderId !== 'new' &&
                  llmProviders.find((provider) => provider.id === selectedProviderId)
                    ?.api_key_set
                    ? '已保存密钥；留空则不修改'
                    : '粘贴 API Key'
                }
                onChange={(event) =>
                  setProviderDraft((draft) => ({
                    ...draft,
                    api_key: event.target.value,
                  }))
                }
              />
            </label>

            <label className="provider-form-wide">
              <span>API 地址</span>
              <input
                value={providerDraft.base_url}
                autoComplete="off"
                placeholder="https://api.openai.com/v1"
                onChange={(event) =>
                  setProviderDraft((draft) => ({
                    ...draft,
                    base_url: event.target.value,
                  }))
                }
              />
            </label>

            <label>
              <span>模型</span>
              <input
                value={providerDraft.model}
                autoComplete="off"
                placeholder="gpt-4.1-mini"
                onChange={(event) =>
                  setProviderDraft((draft) => ({
                    ...draft,
                    model: event.target.value,
                  }))
                }
              />
            </label>

            <label className="provider-toggle">
              <input
                checked={providerDraft.enabled}
                type="checkbox"
                onChange={(event) =>
                  setProviderDraft((draft) => ({
                    ...draft,
                    enabled: event.target.checked,
                  }))
                }
              />
              <span>启用</span>
            </label>

            <div className="provider-actions provider-form-wide">
              <button type="submit" disabled={isSavingProvider}>
                {isSavingProvider ? '保存中' : '保存配置'}
              </button>
              {typeof selectedProviderId === 'number' ? (
                <>
                  <button type="button" onClick={() => onActivateProvider(selectedProviderId)}>
                    设为当前
                  </button>
                  <button
                    className="danger-action"
                    type="button"
                    onClick={() => {
                      const provider = llmProviders.find(
                        (item) => item.id === selectedProviderId,
                      )
                      if (provider) onDeleteProvider(provider)
                    }}
                  >
                    删除提供商
                  </button>
                </>
              ) : null}
            </div>

            <p className="provider-save-note provider-form-wide">
              保存带 API Key 且已启用的配置后，会自动设为当前抽取模型。
            </p>
          </form>
        </div>
      </section>

      <section className="records-section search-settings">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Search Providers</p>
            <h3>联网检索配置</h3>
          </div>
          <span className="status-pill online">
            {searchStatus?.configured
              ? `${searchProviderTypeLabels[searchStatus.provider as SearchProviderType] ?? searchStatus.provider} 已配置`
              : '未启用联网检索'}
          </span>
        </div>

        <div className="provider-layout">
          <div className="provider-list">
            {searchProviders.map((provider) => (
              <button
                key={provider.id}
                className={selectedSearchProviderId === provider.id ? 'selected' : ''}
                type="button"
                onClick={() => onSelectSearchProvider(provider)}
              >
                <span>{provider.name}</span>
                <small>
                  {searchProviderTypeLabels[provider.provider_type]} ·{' '}
                  {provider.api_key_set ? '已加密保存' : '未配置密钥'}
                </small>
                {provider.is_active ? <strong>当前</strong> : null}
              </button>
            ))}
            <button
              className={selectedSearchProviderId === 'new' ? 'selected' : ''}
              type="button"
              onClick={onNewSearchProvider}
            >
              <span>新增检索提供商</span>
              <small>Exa / Tavily</small>
            </button>
          </div>

          <form className="provider-form" onSubmit={handleSearchSubmit}>
            <label>
              <span>提供商名称</span>
              <input
                value={searchProviderDraft.name}
                autoComplete="off"
                placeholder="例如 Exa"
                onChange={(event) =>
                  setSearchProviderDraft((draft) => ({
                    ...draft,
                    name: event.target.value,
                  }))
                }
              />
            </label>

            <label>
              <span>提供商类型</span>
              <select
                value={searchProviderDraft.provider_type}
                onChange={(event) =>
                  onSearchProviderTypeChange(event.target.value as SearchProviderType)
                }
              >
                <option value="exa">Exa</option>
                <option value="tavily">Tavily</option>
              </select>
            </label>

            <label className="provider-form-wide">
              <span>API Key</span>
              <input
                value={searchProviderDraft.api_key}
                type="password"
                autoComplete="new-password"
                placeholder={
                  selectedSearchProviderId !== 'new' &&
                  searchProviders.find(
                    (provider) => provider.id === selectedSearchProviderId,
                  )?.api_key_set
                    ? '已保存密钥；留空则不修改'
                    : '粘贴检索 API Key'
                }
                onChange={(event) =>
                  setSearchProviderDraft((draft) => ({
                    ...draft,
                    api_key: event.target.value,
                  }))
                }
              />
            </label>

            <label className="provider-form-wide">
              <span>API 地址</span>
              <input
                value={searchProviderDraft.base_url}
                autoComplete="off"
                placeholder="https://api.exa.ai"
                onChange={(event) =>
                  setSearchProviderDraft((draft) => ({
                    ...draft,
                    base_url: event.target.value,
                  }))
                }
              />
            </label>

            <label className="provider-toggle">
              <input
                checked={searchProviderDraft.enabled}
                type="checkbox"
                onChange={(event) =>
                  setSearchProviderDraft((draft) => ({
                    ...draft,
                    enabled: event.target.checked,
                  }))
                }
              />
              <span>启用</span>
            </label>

            <div className="provider-actions provider-form-wide">
              <button type="submit" disabled={isSavingSearchProvider}>
                {isSavingSearchProvider ? '保存中' : '保存检索配置'}
              </button>
              {typeof selectedSearchProviderId === 'number' ? (
                <>
                  <button
                    type="button"
                    onClick={() => onActivateSearchProvider(selectedSearchProviderId)}
                  >
                    设为当前
                  </button>
                  <button
                    className="danger-action"
                    type="button"
                    onClick={() => {
                      const provider = searchProviders.find(
                        (item) => item.id === selectedSearchProviderId,
                      )
                      if (provider) onDeleteSearchProvider(provider)
                    }}
                  >
                    删除提供商
                  </button>
                </>
              ) : null}
            </div>

            <p className="provider-save-note provider-form-wide">
              公司补全会先调用当前检索服务；有搜索结果时，公司字段来源会标为 external_search。
            </p>
          </form>
        </div>
      </section>
    </>
  )
}

export default ProviderPage
