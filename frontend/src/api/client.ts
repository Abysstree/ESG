import type {
  CompanyProfile,
  HealthResponse,
  LLMExtractPreview,
  LLMRoleProfileResult,
  JobCard,
  JobCardUpdate,
  LLMProviderConfig,
  LLMProviderConfigCreate,
  LLMProviderConfigUpdate,
  LLMStatus,
  RawImport,
  RawImportCreate,
  SearchProviderConfig,
  SearchProviderConfigCreate,
  SearchProviderConfigUpdate,
  SearchStatus,
  StoredRoleProfile,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
    ...init,
  })

  if (!response.ok) {
    let message = `API request failed: ${response.status}`
    try {
      const errorPayload = (await response.clone().json()) as { detail?: unknown }
      if (errorPayload.detail) {
        message = `${message} · ${String(errorPayload.detail)}`
      }
    } catch {
      // Keep the status-only message when the backend does not return JSON.
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

export function listImports(): Promise<RawImport[]> {
  return request<RawImport[]>('/api/imports')
}

export async function deleteImport(rawImportId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/imports/${rawImportId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
}

export function listJobs(): Promise<JobCard[]> {
  return request<JobCard[]>('/api/jobs')
}

export function listCompanyProfiles(): Promise<CompanyProfile[]> {
  return request<CompanyProfile[]>('/api/companies')
}

export function enrichCompanyProfile(companyName: string): Promise<CompanyProfile> {
  return request<CompanyProfile>('/api/companies/enrich', {
    method: 'POST',
    body: JSON.stringify({ company_name: companyName }),
  })
}

export function rebuildMockJobs(): Promise<JobCard[]> {
  return request<JobCard[]>('/api/jobs/rebuild-mock', {
    method: 'POST',
  })
}

export function rebuildLLMJobs(): Promise<JobCard[]> {
  return request<JobCard[]>('/api/jobs/rebuild-llm', {
    method: 'POST',
  })
}

export function reextractJob(jobId: number): Promise<JobCard> {
  return request<JobCard>(`/api/jobs/${jobId}/reextract`, {
    method: 'POST',
  })
}

export function generateRoleProfile(roleCategory: string): Promise<LLMRoleProfileResult> {
  return request<LLMRoleProfileResult>('/api/roles/profile', {
    method: 'POST',
    body: JSON.stringify({ role_category: roleCategory }),
  })
}

export function listRoleProfiles(): Promise<StoredRoleProfile[]> {
  return request<StoredRoleProfile[]>('/api/roles/profiles')
}

export function reorderJobs(jobIds: number[]): Promise<JobCard[]> {
  return request<JobCard[]>('/api/jobs/reorder', {
    method: 'POST',
    body: JSON.stringify({ job_ids: jobIds }),
  })
}

export function updateJob(jobId: number, payload: JobCardUpdate): Promise<JobCard> {
  return request<JobCard>(`/api/jobs/${jobId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function deleteJob(jobId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
}

export function getLLMStatus(): Promise<LLMStatus> {
  return request<LLMStatus>('/api/llm/status')
}

export function extractLLMPreview(rawText: string): Promise<LLMExtractPreview> {
  return request<LLMExtractPreview>('/api/llm/extract-preview', {
    method: 'POST',
    body: JSON.stringify({ raw_text: rawText }),
  })
}

export function listLLMProviders(): Promise<LLMProviderConfig[]> {
  return request<LLMProviderConfig[]>('/api/llm/providers')
}

export function getSearchStatus(): Promise<SearchStatus> {
  return request<SearchStatus>('/api/search/status')
}

export function listSearchProviders(): Promise<SearchProviderConfig[]> {
  return request<SearchProviderConfig[]>('/api/search/providers')
}

export function createSearchProvider(
  payload: SearchProviderConfigCreate,
): Promise<SearchProviderConfig> {
  return request<SearchProviderConfig>('/api/search/providers', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateSearchProvider(
  providerId: number,
  payload: SearchProviderConfigUpdate,
): Promise<SearchProviderConfig> {
  return request<SearchProviderConfig>(`/api/search/providers/${providerId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function activateSearchProvider(
  providerId: number,
): Promise<SearchProviderConfig> {
  return request<SearchProviderConfig>(`/api/search/providers/${providerId}/activate`, {
    method: 'POST',
  })
}

export async function deleteSearchProvider(providerId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/search/providers/${providerId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
}

export function createLLMProvider(
  payload: LLMProviderConfigCreate,
): Promise<LLMProviderConfig> {
  return request<LLMProviderConfig>('/api/llm/providers', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateLLMProvider(
  providerId: number,
  payload: LLMProviderConfigUpdate,
): Promise<LLMProviderConfig> {
  return request<LLMProviderConfig>(`/api/llm/providers/${providerId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function activateLLMProvider(providerId: number): Promise<LLMProviderConfig> {
  return request<LLMProviderConfig>(`/api/llm/providers/${providerId}/activate`, {
    method: 'POST',
  })
}

export async function deleteLLMProvider(providerId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/llm/providers/${providerId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
}

export function createImport(payload: RawImportCreate): Promise<RawImport> {
  return request<RawImport>('/api/imports', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function createScreenshotImport(
  file: File,
  rawText: string | null,
): Promise<RawImport> {
  const formData = new FormData()
  formData.append('file', file)
  if (rawText) {
    formData.append('raw_text', rawText)
  }

  const response = await fetch(`${API_BASE_URL}/api/imports/screenshot`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json() as Promise<RawImport>
}
