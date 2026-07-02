import { useEffect, useMemo, useRef, useState } from 'react'
import type { ChangeEvent, ClipboardEvent, DragEvent, FormEvent } from 'react'
import {
  activateLLMProvider,
  activateSearchProvider,
  createImport,
  createLLMProvider,
  createSearchProvider,
  createScreenshotImport,
  deleteImport,
  deleteLLMProvider,
  deleteSearchProvider,
  deleteJob,
  enrichCompanyProfile,
  extractLLMPreview,
  generateRoleProfile,
  getHealth,
  getLLMStatus,
  getSearchStatus,
  listCompanyProfiles,
  listImports,
  listJobs,
  listLLMProviders,
  listSearchProviders,
  rebuildLLMJobs,
  rebuildMockJobs,
  reextractJob,
  reorderJobs,
  updateJob,
  updateLLMProvider,
  updateSearchProvider,
} from './api/client'
import './App.css'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import {
  MIND_MAP_DEFAULT_ZOOM,
  THEME_STORAGE_KEY,
  providerDefaults,
  searchProviderDefaults,
} from './constants/app'
import ImportPage from './pages/ImportPage'
import JobCardsPage from './pages/JobCardsPage'
import LearningMapPage from './pages/LearningMapPage'
import ProviderPage from './pages/ProviderPage'
import RoleCategoriesPage from './pages/RoleCategoriesPage'
import ExtractionDebugPage from './pages/ExtractionDebugPage'
import type {
  CompanyProfile,
  JobCard,
  LLMExtractPreview,
  LLMProviderConfig,
  LLMProviderType,
  LLMRoleProfileResult,
  LLMStatus,
  RawImport,
  SearchProviderConfig,
  SearchProviderType,
  SearchStatus,
  SourceType,
} from './types/api'
import type {
  ApiStatus,
  EditableJobField,
  JobEditDraft,
  LLMProviderDraft,
  PageId,
  SearchProviderDraft,
  ThemeMode,
  ThemePreference,
} from './types/app'
import { moveJobCard, sortJobCards, splitLines, toEditDraft } from './utils/jobs'
import { getInitialPage } from './utils/navigation'
import {
  createProviderDraft,
  createSearchProviderDraft,
  providerConfigToDraft,
  searchProviderConfigToDraft,
} from './utils/providers'
import {
  buildMindMapBranches,
  buildMindMapBranchesFromLLMProfile,
  deriveRoleSummaries,
} from './utils/roles'
import { getInitialThemePreference, resolveThemeMode } from './utils/theme'

function App() {
  const [activePage, setActivePage] = useState<PageId>(getInitialPage)
  const [themePreference, setThemePreference] = useState<ThemePreference>(
    getInitialThemePreference,
  )
  const [themeMode, setThemeMode] = useState<ThemeMode>(() =>
    resolveThemeMode(getInitialThemePreference()),
  )
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')
  const [sourceType, setSourceType] = useState<SourceType>('url')
  const [sourceValue, setSourceValue] = useState('')
  const [rawText, setRawText] = useState('')
  const [screenshotFile, setScreenshotFile] = useState<File | null>(null)
  const [screenshotPreviewUrl, setScreenshotPreviewUrl] = useState<string | null>(null)
  const [isDraggingScreenshot, setIsDraggingScreenshot] = useState(false)
  const [imports, setImports] = useState<RawImport[]>([])
  const [showAllImports, setShowAllImports] = useState(false)
  const [jobCards, setJobCards] = useState<JobCard[]>([])
  const [companyProfiles, setCompanyProfiles] = useState<Record<string, CompanyProfile>>(
    {},
  )
  const [selectedRoleName, setSelectedRoleName] = useState<string | null>(null)
  const [roleProfileResults, setRoleProfileResults] = useState<
    Record<string, LLMRoleProfileResult>
  >({})
  const [generatingRoleProfileName, setGeneratingRoleProfileName] = useState<string | null>(
    null,
  )
  const [mindMapZoom, setMindMapZoom] = useState(MIND_MAP_DEFAULT_ZOOM)
  const [collapsedMindMapBranchIds, setCollapsedMindMapBranchIds] = useState<string[]>(
    [],
  )
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null)
  const [llmProviders, setLlmProviders] = useState<LLMProviderConfig[]>([])
  const [searchStatus, setSearchStatus] = useState<SearchStatus | null>(null)
  const [searchProviders, setSearchProviders] = useState<SearchProviderConfig[]>([])
  const [debugRawText, setDebugRawText] = useState('')
  const [debugResult, setDebugResult] = useState<LLMExtractPreview | null>(null)
  const [debugErrorMessage, setDebugErrorMessage] = useState<string | null>(null)
  const [isRunningDebugExtraction, setIsRunningDebugExtraction] = useState(false)
  const [selectedProviderId, setSelectedProviderId] = useState<number | 'new' | null>(
    null,
  )
  const [providerDraft, setProviderDraft] = useState<LLMProviderDraft>(() =>
    createProviderDraft('deepseek'),
  )
  const [selectedSearchProviderId, setSelectedSearchProviderId] = useState<
    number | 'new' | null
  >(null)
  const [searchProviderDraft, setSearchProviderDraft] =
    useState<SearchProviderDraft>(() => createSearchProviderDraft('exa'))
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRebuilding, setIsRebuilding] = useState(false)
  const [isRebuildingWithLLM, setIsRebuildingWithLLM] = useState(false)
  const [isSavingProvider, setIsSavingProvider] = useState(false)
  const [isSavingSearchProvider, setIsSavingSearchProvider] = useState(false)
  const [editingJobId, setEditingJobId] = useState<number | null>(null)
  const [expandedJobId, setExpandedJobId] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState<JobEditDraft | null>(null)
  const [savingJobId, setSavingJobId] = useState<number | null>(null)
  const [deletingJobId, setDeletingJobId] = useState<number | null>(null)
  const [reextractingJobId, setReextractingJobId] = useState<number | null>(null)
  const [enrichingCompanyName, setEnrichingCompanyName] = useState<string | null>(null)
  const [deletingImportId, setDeletingImportId] = useState<number | null>(null)
  const [draggedJobId, setDraggedJobId] = useState<number | null>(null)
  const [dragOverJobId, setDragOverJobId] = useState<number | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const screenshotInputRef = useRef<HTMLInputElement | null>(null)

  const sourceInput = useMemo(() => {
    if (sourceType === 'url') {
      return {
        label: '岗位链接',
        placeholder: 'https://example.com/jobs/123',
      }
    }

    return null
  }, [sourceType])

  const rawTextInput = useMemo(() => {
    if (sourceType === 'url') {
      return {
        label: '可选：页面正文备份',
        placeholder: '如果链接暂时无法读取，可以先把岗位正文粘贴在这里。',
      }
    }

    if (sourceType === 'screenshot') {
      return {
        label: 'OCR 识别结果',
        placeholder: '截图识别功能接入后，这里会显示识别出的岗位正文；现在也可以手动粘贴。',
      }
    }

    return {
      label: '岗位文本',
      placeholder: '粘贴岗位职责、任职要求、加分项等原文。',
    }
  }, [sourceType])

  const roleSummaries = useMemo(() => deriveRoleSummaries(jobCards), [jobCards])
  const selectedRole = useMemo(
    () =>
      roleSummaries.find((role) => role.name === selectedRoleName) ??
      roleSummaries[0] ??
      null,
    [roleSummaries, selectedRoleName],
  )
  const mindMapBranches = useMemo(
    () => {
      const llmProfile = selectedRole?.name
        ? roleProfileResults[selectedRole.name]?.role_profile
        : null
      const llmBranches = buildMindMapBranchesFromLLMProfile(llmProfile)
      return llmBranches.length ? llmBranches : selectedRole ? buildMindMapBranches(selectedRole) : []
    },
    [roleProfileResults, selectedRole],
  )
  const visibleImports = showAllImports ? imports : imports.slice(0, 2)

  useEffect(() => {
    function handleHashChange() {
      setActivePage(getInitialPage())
    }

    window.addEventListener('hashchange', handleHashChange)
    window.addEventListener('popstate', handleHashChange)
    return () => {
      window.removeEventListener('hashchange', handleHashChange)
      window.removeEventListener('popstate', handleHashChange)
    }
  }, [])

  useEffect(() => {
    document.documentElement.dataset.theme = themeMode
    document.documentElement.style.colorScheme = themeMode
  }, [themeMode])

  useEffect(() => {
    const spotlightSelector = [
      '.import-panel',
      '.status-panel',
      '.records-section',
      '.import-card',
      '.job-card',
      '.provider-list button',
      '.role-list button',
      '.learning-role-tabs button',
      '.detail-section',
      '.job-preview-grid section',
      '.job-sections section',
      '.debug-card-grid section',
      '.debug-source-panel',
      '.debug-json-grid details',
    ].join(',')

    function handlePointerMove(event: PointerEvent) {
      const target = (event.target as Element | null)?.closest<HTMLElement>(
        spotlightSelector,
      )
      if (!target) return

      const rect = target.getBoundingClientRect()
      target.style.setProperty('--spot-x', `${event.clientX - rect.left}px`)
      target.style.setProperty('--spot-y', `${event.clientY - rect.top}px`)
    }

    document.addEventListener('pointermove', handlePointerMove)
    return () => document.removeEventListener('pointermove', handlePointerMove)
  }, [])

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, themePreference)

    function updateThemeMode() {
      setThemeMode(resolveThemeMode(themePreference))
    }

    updateThemeMode()

    if (themePreference !== 'auto') return undefined
    const timerId = window.setInterval(updateThemeMode, 60 * 1000)
    return () => window.clearInterval(timerId)
  }, [themePreference])

  useEffect(() => {
    if (roleSummaries.length === 0) {
      setSelectedRoleName(null)
      return
    }

    if (!selectedRoleName || !roleSummaries.some((role) => role.name === selectedRoleName)) {
      setSelectedRoleName(roleSummaries[0].name)
    }
  }, [roleSummaries, selectedRoleName])

  useEffect(() => {
    async function bootstrap() {
      try {
        await getHealth()
        setApiStatus('online')
        const [rawImports, jobs, llm, search, profiles] = await Promise.all([
          listImports(),
          listJobs(),
          getLLMStatus(),
          getSearchStatus(),
          listCompanyProfiles(),
        ])
        const [providers, searchProviderList] = await Promise.all([
          listLLMProviders(),
          listSearchProviders(),
        ])
        setImports(rawImports)
        setJobCards(jobs)
        setCompanyProfiles(indexCompanyProfiles(profiles))
        setLlmStatus(llm)
        setLlmProviders(providers)
        setSearchStatus(search)
        setSearchProviders(searchProviderList)

        const activeProvider = providers.find((provider) => provider.is_active)
        const selectedProvider = activeProvider ?? providers[0]
        if (selectedProvider) {
          setSelectedProviderId(selectedProvider.id)
          setProviderDraft(providerConfigToDraft(selectedProvider))
        }
        const activeSearchProvider = searchProviderList.find((provider) => provider.is_active)
        const selectedSearchProvider = activeSearchProvider ?? searchProviderList[0]
        if (selectedSearchProvider) {
          setSelectedSearchProviderId(selectedSearchProvider.id)
          setSearchProviderDraft(searchProviderConfigToDraft(selectedSearchProvider))
        }
      } catch {
        setApiStatus('offline')
      }
    }

    void bootstrap()
  }, [])

  useEffect(() => {
    if (!screenshotFile) {
      setScreenshotPreviewUrl(null)
      return
    }

    const previewUrl = URL.createObjectURL(screenshotFile)
    setScreenshotPreviewUrl(previewUrl)

    return () => URL.revokeObjectURL(previewUrl)
  }, [screenshotFile])

  useEffect(() => {
    function handleWindowPaste(event: globalThis.ClipboardEvent) {
      if (sourceType !== 'screenshot') return

      const imageFile = findImageFile(event.clipboardData?.files)
      if (!imageFile) return

      event.preventDefault()
      setScreenshotFile(imageFile)
      setErrorMessage(null)
    }

    window.addEventListener('paste', handleWindowPaste)
    return () => window.removeEventListener('paste', handleWindowPaste)
  }, [sourceType])

  useEffect(() => {
    setMindMapZoom(MIND_MAP_DEFAULT_ZOOM)
    setCollapsedMindMapBranchIds(mindMapBranches.map((branch) => branch.id))
  }, [mindMapBranches, selectedRole?.name])

  function findImageFile(files: FileList | null | undefined): File | null {
    if (!files) return null
    return Array.from(files).find((file) => file.type.startsWith('image/')) ?? null
  }

  function setScreenshotFromFiles(files: FileList | null | undefined) {
    const imageFile = findImageFile(files)
    if (!imageFile) {
      setErrorMessage('请放入图片格式的截图。')
      return
    }

    setScreenshotFile(imageFile)
    setErrorMessage(null)
  }

  function handleScreenshotSelect(event: ChangeEvent<HTMLInputElement>) {
    setScreenshotFromFiles(event.target.files)
    event.target.value = ''
  }

  function handleScreenshotDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDraggingScreenshot(false)
    setScreenshotFromFiles(event.dataTransfer.files)
  }

  function handleScreenshotPaste(event: ClipboardEvent<HTMLDivElement>) {
    const imageFile = findImageFile(event.clipboardData.files)
    if (!imageFile) return

    event.preventDefault()
    setScreenshotFile(imageFile)
    setErrorMessage(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage(null)

    const trimmedSourceValue = sourceValue.trim()
    const trimmedRawText = rawText.trim()

    if (sourceType === 'url' && !trimmedSourceValue) {
      setErrorMessage('请先输入岗位链接。')
      return
    }

    if (sourceType === 'text' && !trimmedRawText) {
      setErrorMessage('请先粘贴岗位文本。')
      return
    }

    if (sourceType === 'screenshot' && !screenshotFile && !trimmedRawText) {
      setErrorMessage('请先拖入、粘贴或选择一张截图；也可以先粘贴 OCR 识别后的岗位文本。')
      return
    }

    setIsSubmitting(true)
    try {
      const savedImport =
        sourceType === 'screenshot' && screenshotFile
          ? await createScreenshotImport(screenshotFile, trimmedRawText || null)
          : await createImport({
              source_type: sourceType,
              source_value:
                sourceType === 'text'
                  ? '手动粘贴文本'
                  : sourceType === 'screenshot'
                    ? '手动粘贴 OCR 文本'
                    : trimmedSourceValue,
              raw_text: trimmedRawText || null,
            })

      setImports((currentImports) => [savedImport, ...currentImports])
      setJobCards(await listJobs())
      setSourceValue('')
      setRawText('')
      setScreenshotFile(null)
    } catch {
      setErrorMessage('保存失败，请确认后端服务正在运行。')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleRebuildMockJobs() {
    setErrorMessage(null)
    setIsRebuilding(true)
    try {
      const rebuiltJobs = await rebuildMockJobs()
      const rawImports = await listImports()
      setJobCards(rebuiltJobs)
      setImports(rawImports)
    } catch {
      setErrorMessage('重新抽取失败，请确认后端服务正在运行。')
    } finally {
      setIsRebuilding(false)
    }
  }

  async function handleRebuildLLMJobs() {
    setErrorMessage(null)
    setIsRebuildingWithLLM(true)
    try {
      const rebuiltJobs = await rebuildLLMJobs()
      const rawImports = await listImports()
      setJobCards(rebuiltJobs)
      setImports(rawImports)
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? `LLM重新抽取失败：${error.message}`
          : 'LLM重新抽取失败，请检查模型配置。',
      )
    } finally {
      setIsRebuildingWithLLM(false)
    }
  }

  async function handleReextractJob(job: JobCard) {
    setErrorMessage(null)
    setReextractingJobId(job.id)
    try {
      const updatedJob = await reextractJob(job.id)
      setJobCards((currentJobs) =>
        sortJobCards(
          currentJobs.map((item) => (item.id === updatedJob.id ? updatedJob : item)),
        ),
      )
      setImports(await listImports())
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? `LLM重新抽取“${job.title}”失败：${error.message}`
          : 'LLM重新抽取失败，请检查模型配置。',
      )
    } finally {
      setReextractingJobId(null)
    }
  }

  async function handleEnrichCompany(companyName: string) {
    const trimmedCompanyName = companyName.trim()
    if (!trimmedCompanyName) {
      setErrorMessage('公司名称为空，无法补全公司信息。')
      return
    }

    setErrorMessage(null)
    setEnrichingCompanyName(trimmedCompanyName)
    try {
      const profile = await enrichCompanyProfile(trimmedCompanyName)
      setCompanyProfiles((currentProfiles) => ({
        ...currentProfiles,
        [profile.company_name]: profile,
      }))
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? `补全“${trimmedCompanyName}”失败：${error.message}`
          : '补全公司信息失败，请检查模型配置。',
      )
    } finally {
      setEnrichingCompanyName(null)
    }
  }

  function handleStartEditing(job: JobCard) {
    setEditingJobId(job.id)
    setExpandedJobId(job.id)
    setEditDraft(toEditDraft(job))
    setErrorMessage(null)
  }

  function handleDraftChange(field: EditableJobField, value: string) {
    setEditDraft((currentDraft) =>
      currentDraft ? { ...currentDraft, [field]: value } : currentDraft,
    )
  }

  async function handleSaveJob(jobId: number) {
    if (!editDraft) return

    setErrorMessage(null)
    setSavingJobId(jobId)
    try {
      const updatedJob = await updateJob(jobId, {
        title: editDraft.title.trim(),
        company_name: editDraft.company_name.trim() || null,
        role_category: editDraft.role_category.trim() || null,
        salary_range: editDraft.salary_range.trim() || null,
        salary_period: editDraft.salary_period.trim() || null,
        base_location: editDraft.base_location.trim() || null,
        education_requirement: editDraft.education_requirement.trim() || null,
        experience_requirement: editDraft.experience_requirement.trim() || null,
        skills: splitLines(editDraft.skillsText),
        responsibilities: splitLines(editDraft.responsibilitiesText),
        requirements: splitLines(editDraft.requirementsText),
        bonus_points: splitLines(editDraft.bonusPointsText),
      })

      setJobCards((currentJobs) =>
        currentJobs.map((job) => (job.id === updatedJob.id ? updatedJob : job)),
      )
      setEditingJobId(null)
      setEditDraft(null)
    } catch {
      setErrorMessage('保存岗位卡失败，请确认后端服务正在运行。')
    } finally {
      setSavingJobId(null)
    }
  }

  async function handleDeleteJob(job: JobCard) {
    const confirmed = window.confirm(`删除岗位卡“${job.title}”？`)
    if (!confirmed) return

    setErrorMessage(null)
    setDeletingJobId(job.id)
    try {
      await deleteJob(job.id)
      setJobCards((currentJobs) => currentJobs.filter((item) => item.id !== job.id))
      if (editingJobId === job.id) {
        setEditingJobId(null)
        setEditDraft(null)
      }
      if (expandedJobId === job.id) {
        setExpandedJobId(null)
      }
    } catch {
      setErrorMessage('删除岗位卡失败，请确认后端服务正在运行。')
    } finally {
      setDeletingJobId(null)
    }
  }

  async function handleDeleteImport(rawImport: RawImport) {
    const confirmed = window.confirm('删除这条导入记录及其生成的岗位卡？')
    if (!confirmed) return

    setErrorMessage(null)
    setDeletingImportId(rawImport.id)
    try {
      await deleteImport(rawImport.id)
      setImports((currentImports) =>
        currentImports.filter((item) => item.id !== rawImport.id),
      )
      setJobCards((currentJobs) =>
        currentJobs.filter((job) => job.raw_import_id !== rawImport.id),
      )
    } catch {
      setErrorMessage('删除导入记录失败，请确认后端服务正在运行。')
    } finally {
      setDeletingImportId(null)
    }
  }

  async function handleTogglePinned(job: JobCard) {
    setErrorMessage(null)
    try {
      const updatedJob = await updateJob(job.id, {
        is_pinned: !job.is_pinned,
      })
      setJobCards((currentJobs) =>
        sortJobCards(
          currentJobs.map((item) => (item.id === updatedJob.id ? updatedJob : item)),
        ),
      )
    } catch {
      setErrorMessage('更新置顶状态失败，请确认后端服务正在运行。')
    }
  }

  function handleJobDragStart(jobId: number, event: DragEvent<HTMLElement>) {
    setDraggedJobId(jobId)
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(jobId))
  }

  function handleJobDragOver(jobId: number, event: DragEvent<HTMLElement>) {
    event.preventDefault()
    if (!draggedJobId || draggedJobId === jobId) return

    setDragOverJobId(jobId)
    setJobCards((currentJobs) => moveJobCard(currentJobs, draggedJobId, jobId))
  }

  async function handleJobDrop(event: DragEvent<HTMLElement>) {
    event.preventDefault()
    setDragOverJobId(null)
    setDraggedJobId(null)

    try {
      const savedJobs = await reorderJobs(jobCards.map((job) => job.id))
      setJobCards(savedJobs)
    } catch {
      setErrorMessage('保存排序失败，请确认后端服务正在运行。')
      setJobCards(await listJobs())
    }
  }

  function handleJobDragEnd() {
    setDragOverJobId(null)
    setDraggedJobId(null)
  }

  function handleSelectProvider(provider: LLMProviderConfig) {
    setSelectedProviderId(provider.id)
    setProviderDraft(providerConfigToDraft(provider))
    setErrorMessage(null)
  }

  function handleNewProvider(providerType: LLMProviderType = 'deepseek') {
    setSelectedProviderId('new')
    setProviderDraft(createProviderDraft(providerType))
    setErrorMessage(null)
  }

  function handleProviderTypeChange(providerType: LLMProviderType) {
    const defaults = providerDefaults[providerType]
    setProviderDraft((currentDraft) => ({
      ...currentDraft,
      provider_type: providerType,
      name: selectedProviderId === 'new' ? defaults.name : currentDraft.name,
      base_url: defaults.base_url,
      model: defaults.model,
    }))
  }

  async function refreshLLMProviders() {
    const [providers, status] = await Promise.all([listLLMProviders(), getLLMStatus()])
    setLlmProviders(providers)
    setLlmStatus(status)
    return providers
  }

  function handleSelectSearchProvider(provider: SearchProviderConfig) {
    setSelectedSearchProviderId(provider.id)
    setSearchProviderDraft(searchProviderConfigToDraft(provider))
    setErrorMessage(null)
  }

  function handleNewSearchProvider(providerType: SearchProviderType = 'exa') {
    setSelectedSearchProviderId('new')
    setSearchProviderDraft(createSearchProviderDraft(providerType))
    setErrorMessage(null)
  }

  function handleSearchProviderTypeChange(providerType: SearchProviderType) {
    const defaults = searchProviderDefaults[providerType]
    setSearchProviderDraft((currentDraft) => ({
      ...currentDraft,
      provider_type: providerType,
      name: selectedSearchProviderId === 'new' ? defaults.name : currentDraft.name,
      base_url: defaults.base_url,
    }))
  }

  async function refreshSearchProviders() {
    const [providers, status] = await Promise.all([
      listSearchProviders(),
      getSearchStatus(),
    ])
    setSearchProviders(providers)
    setSearchStatus(status)
    return providers
  }

  async function handleRunDebugExtraction() {
    const trimmedRawText = debugRawText.trim()
    if (!trimmedRawText) {
      setDebugErrorMessage('请先粘贴一段岗位正文。')
      return
    }

    setDebugErrorMessage(null)
    setIsRunningDebugExtraction(true)
    try {
      setLlmStatus(await getLLMStatus())
      const result = await extractLLMPreview(trimmedRawText)
      setDebugResult(result)
    } catch (error) {
      setDebugResult(null)
      setDebugErrorMessage(
        error instanceof Error
          ? `抽取失败：${error.message}`
          : '抽取失败，请检查模型配置。',
      )
    } finally {
      setIsRunningDebugExtraction(false)
    }
  }

  async function handleGenerateRoleProfile(roleName: string) {
    setErrorMessage(null)
    setGeneratingRoleProfileName(roleName)
    try {
      const result = await generateRoleProfile(roleName)
      setRoleProfileResults((currentResults) => ({
        ...currentResults,
        [roleName]: result,
      }))
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? `LLM生成“${roleName}”失败：${error.message}`
          : 'LLM生成岗位大类画像失败，请检查模型配置。',
      )
    } finally {
      setGeneratingRoleProfileName(null)
    }
  }

  async function handleSaveProvider() {
    setErrorMessage(null)
    setIsSavingProvider(true)
    try {
      const payload = {
        name: providerDraft.name.trim(),
        provider_type: providerDraft.provider_type,
        base_url: providerDraft.base_url.trim() || null,
        model: providerDraft.model.trim() || null,
        enabled: providerDraft.enabled,
      }
      const apiKey = providerDraft.api_key.trim()

      const savedProvider =
        selectedProviderId === 'new' || selectedProviderId === null
          ? await createLLMProvider({
              ...payload,
              api_key: apiKey || null,
              is_active: false,
            })
          : await updateLLMProvider(
              selectedProviderId,
              apiKey ? { ...payload, api_key: apiKey } : payload,
            )

      let providers = await refreshLLMProviders()
      const latestProvider =
        providers.find((provider) => provider.id === savedProvider.id) ?? savedProvider
      const shouldActivateAfterSave =
        latestProvider.enabled && (latestProvider.api_key_set || Boolean(apiKey))
      if (shouldActivateAfterSave) {
        const activatedProvider = await activateLLMProvider(latestProvider.id)
        providers = await refreshLLMProviders()
        const refreshedProvider =
          providers.find((provider) => provider.id === activatedProvider.id) ??
          activatedProvider
        setSelectedProviderId(refreshedProvider.id)
        setProviderDraft(providerConfigToDraft(refreshedProvider))
        return
      }

      setSelectedProviderId(latestProvider.id)
      setProviderDraft(providerConfigToDraft(latestProvider))
    } catch {
      setErrorMessage('保存模型提供商失败，请检查配置。')
    } finally {
      setIsSavingProvider(false)
    }
  }

  async function handleSaveSearchProvider() {
    setErrorMessage(null)
    setIsSavingSearchProvider(true)
    try {
      const payload = {
        name: searchProviderDraft.name.trim(),
        provider_type: searchProviderDraft.provider_type,
        base_url: searchProviderDraft.base_url.trim() || null,
        enabled: searchProviderDraft.enabled,
      }
      const apiKey = searchProviderDraft.api_key.trim()

      const savedProvider =
        selectedSearchProviderId === 'new' || selectedSearchProviderId === null
          ? await createSearchProvider({
              ...payload,
              api_key: apiKey || null,
              is_active: false,
            })
          : await updateSearchProvider(
              selectedSearchProviderId,
              apiKey ? { ...payload, api_key: apiKey } : payload,
            )

      let providers = await refreshSearchProviders()
      const latestProvider =
        providers.find((provider) => provider.id === savedProvider.id) ?? savedProvider
      const shouldActivateAfterSave =
        latestProvider.enabled && (latestProvider.api_key_set || Boolean(apiKey))
      if (shouldActivateAfterSave) {
        const activatedProvider = await activateSearchProvider(latestProvider.id)
        providers = await refreshSearchProviders()
        const refreshedProvider =
          providers.find((provider) => provider.id === activatedProvider.id) ??
          activatedProvider
        setSelectedSearchProviderId(refreshedProvider.id)
        setSearchProviderDraft(searchProviderConfigToDraft(refreshedProvider))
        return
      }

      setSelectedSearchProviderId(latestProvider.id)
      setSearchProviderDraft(searchProviderConfigToDraft(latestProvider))
    } catch {
      setErrorMessage('保存联网检索提供商失败，请检查配置。')
    } finally {
      setIsSavingSearchProvider(false)
    }
  }

  async function handleActivateProvider(providerId: number) {
    setErrorMessage(null)
    try {
      const activatedProvider = await activateLLMProvider(providerId)
      const providers = await refreshLLMProviders()
      setSelectedProviderId(activatedProvider.id)
      setProviderDraft(
        providerConfigToDraft(
          providers.find((provider) => provider.id === activatedProvider.id) ??
            activatedProvider,
        ),
      )
    } catch {
      setErrorMessage('启用模型提供商失败，请确认 API Key 和配置已保存。')
    }
  }

  async function handleActivateSearchProvider(providerId: number) {
    setErrorMessage(null)
    try {
      const activatedProvider = await activateSearchProvider(providerId)
      const providers = await refreshSearchProviders()
      setSelectedSearchProviderId(activatedProvider.id)
      setSearchProviderDraft(
        searchProviderConfigToDraft(
          providers.find((provider) => provider.id === activatedProvider.id) ??
            activatedProvider,
        ),
      )
    } catch {
      setErrorMessage('启用联网检索提供商失败，请确认 API Key 和配置已保存。')
    }
  }

  async function handleDeleteProvider(provider: LLMProviderConfig) {
    const confirmed = window.confirm(`删除模型提供商“${provider.name}”？`)
    if (!confirmed) return

    setErrorMessage(null)
    try {
      await deleteLLMProvider(provider.id)
      const providers = await refreshLLMProviders()
      const nextProvider = providers[0]
      setSelectedProviderId(nextProvider?.id ?? 'new')
      setProviderDraft(
        nextProvider ? providerConfigToDraft(nextProvider) : createProviderDraft('deepseek'),
      )
    } catch {
      setErrorMessage('删除模型提供商失败。')
    }
  }

  async function handleDeleteSearchProvider(provider: SearchProviderConfig) {
    const confirmed = window.confirm(`删除联网检索提供商“${provider.name}”？`)
    if (!confirmed) return

    setErrorMessage(null)
    try {
      await deleteSearchProvider(provider.id)
      const providers = await refreshSearchProviders()
      const nextProvider = providers[0]
      setSelectedSearchProviderId(nextProvider?.id ?? 'new')
      setSearchProviderDraft(
        nextProvider ? searchProviderConfigToDraft(nextProvider) : createSearchProviderDraft('exa'),
      )
    } catch {
      setErrorMessage('删除联网检索提供商失败。')
    }
  }

  function handlePageChange(page: PageId) {
    setActivePage(page)
    if (window.location.hash !== `#${page}`) {
      window.history.pushState(null, '', `#${page}`)
    }
  }

  function handleMindMapZoom(delta: number) {
    setMindMapZoom((currentZoom) =>
      Math.min(1.3, Math.max(0.58, Number((currentZoom + delta).toFixed(2)))),
    )
  }

  function toggleMindMapBranch(branchId: string) {
    setCollapsedMindMapBranchIds((currentIds) =>
      currentIds.includes(branchId)
        ? currentIds.filter((id) => id !== branchId)
        : [...currentIds, branchId],
    )
  }

  function expandAllMindMapBranches() {
    setCollapsedMindMapBranchIds([])
  }

  function resetMindMapView() {
    setMindMapZoom(MIND_MAP_DEFAULT_ZOOM)
    setCollapsedMindMapBranchIds(mindMapBranches.map((branch) => branch.id))
  }

  function cancelJobEditing() {
    setEditingJobId(null)
    setEditDraft(null)
  }

  function toggleJobDetails(jobId: number) {
    setExpandedJobId((currentJobId) => (currentJobId === jobId ? null : jobId))
  }

  return (
    <main className="app-shell">
      <Sidebar activePage={activePage} onPageChange={handlePageChange} />

      <section className="workspace">
        <Topbar
          activePage={activePage}
          apiStatus={apiStatus}
          themePreference={themePreference}
          onThemePreferenceChange={setThemePreference}
        />

        {activePage === 'providers' ? (
          <ProviderPage
            llmProviders={llmProviders}
            selectedProviderId={selectedProviderId}
            providerDraft={providerDraft}
            isSavingProvider={isSavingProvider}
            searchProviders={searchProviders}
            searchStatus={searchStatus}
            selectedSearchProviderId={selectedSearchProviderId}
            searchProviderDraft={searchProviderDraft}
            isSavingSearchProvider={isSavingSearchProvider}
            setProviderDraft={setProviderDraft}
            setSearchProviderDraft={setSearchProviderDraft}
            onSelectProvider={handleSelectProvider}
            onNewProvider={handleNewProvider}
            onProviderTypeChange={handleProviderTypeChange}
            onSaveProvider={handleSaveProvider}
            onActivateProvider={handleActivateProvider}
            onDeleteProvider={handleDeleteProvider}
            onSelectSearchProvider={handleSelectSearchProvider}
            onNewSearchProvider={handleNewSearchProvider}
            onSearchProviderTypeChange={handleSearchProviderTypeChange}
            onSaveSearchProvider={handleSaveSearchProvider}
            onActivateSearchProvider={handleActivateSearchProvider}
            onDeleteSearchProvider={handleDeleteSearchProvider}
          />
        ) : null}

        {activePage === 'debug' ? (
          <ExtractionDebugPage
            rawText={debugRawText}
            result={debugResult}
            llmStatus={llmStatus}
            isRunning={isRunningDebugExtraction}
            errorMessage={debugErrorMessage}
            onRawTextChange={setDebugRawText}
            onRun={handleRunDebugExtraction}
          />
        ) : null}

        {activePage === 'import' ? (
          <ImportPage
            sourceType={sourceType}
            sourceValue={sourceValue}
            rawText={rawText}
            sourceInput={sourceInput}
            rawTextInput={rawTextInput}
            screenshotFile={screenshotFile}
            screenshotPreviewUrl={screenshotPreviewUrl}
            screenshotInputRef={screenshotInputRef}
            isDraggingScreenshot={isDraggingScreenshot}
            isSubmitting={isSubmitting}
            isRebuilding={isRebuilding}
            deletingImportId={deletingImportId}
            errorMessage={errorMessage}
            llmStatus={llmStatus}
            imports={imports}
            visibleImports={visibleImports}
            showAllImports={showAllImports}
            onSourceTypeChange={setSourceType}
            onSourceValueChange={setSourceValue}
            onRawTextChange={setRawText}
            onDraggingScreenshotChange={setIsDraggingScreenshot}
            onScreenshotSelect={handleScreenshotSelect}
            onScreenshotDrop={handleScreenshotDrop}
            onScreenshotPaste={handleScreenshotPaste}
            onSubmit={handleSubmit}
            onRebuildMockJobs={handleRebuildMockJobs}
            onDeleteImport={handleDeleteImport}
            onShowAllImportsChange={setShowAllImports}
          />
        ) : null}

        {activePage === 'jobs' ? (
          <JobCardsPage
            jobCards={jobCards}
            companyProfiles={companyProfiles}
            editingJobId={editingJobId}
            editDraft={editDraft}
            savingJobId={savingJobId}
            deletingJobId={deletingJobId}
            reextractingJobId={reextractingJobId}
            enrichingCompanyName={enrichingCompanyName}
            isRebuildingWithLLM={isRebuildingWithLLM}
            draggedJobId={draggedJobId}
            dragOverJobId={dragOverJobId}
            expandedJobId={expandedJobId}
            errorMessage={errorMessage}
            onDraftChange={handleDraftChange}
            onSaveJob={handleSaveJob}
            onCancelEditing={cancelJobEditing}
            onStartEditing={handleStartEditing}
            onDeleteJob={handleDeleteJob}
            onReextractJob={handleReextractJob}
            onEnrichCompany={handleEnrichCompany}
            onRebuildLLMJobs={handleRebuildLLMJobs}
            onTogglePinned={handleTogglePinned}
            onToggleDetails={toggleJobDetails}
            onJobDragStart={handleJobDragStart}
            onJobDragOver={handleJobDragOver}
            onJobDrop={handleJobDrop}
            onJobDragEnd={handleJobDragEnd}
          />
        ) : null}

        {activePage === 'roles' ? (
          <RoleCategoriesPage
            roleSummaries={roleSummaries}
            selectedRole={selectedRole}
            roleProfileResult={selectedRole ? roleProfileResults[selectedRole.name] : null}
            generatingRoleProfileName={generatingRoleProfileName}
            errorMessage={errorMessage}
            onSelectedRoleChange={setSelectedRoleName}
            onGenerateRoleProfile={handleGenerateRoleProfile}
          />
        ) : null}

        {activePage === 'learning' ? (
          <LearningMapPage
            roleSummaries={roleSummaries}
            selectedRole={selectedRole}
            mindMapBranches={mindMapBranches}
            mindMapZoom={mindMapZoom}
            collapsedBranchIds={collapsedMindMapBranchIds}
            roleProfileResult={selectedRole ? roleProfileResults[selectedRole.name] : null}
            generatingRoleProfileName={generatingRoleProfileName}
            onSelectedRoleChange={setSelectedRoleName}
            onGenerateRoleProfile={handleGenerateRoleProfile}
            onZoom={handleMindMapZoom}
            onResetView={resetMindMapView}
            onExpandAll={expandAllMindMapBranches}
            onToggleBranch={toggleMindMapBranch}
          />
        ) : null}
      </section>
    </main>
  )
}

function indexCompanyProfiles(profiles: CompanyProfile[]) {
  return profiles.reduce<Record<string, CompanyProfile>>((indexedProfiles, profile) => {
    indexedProfiles[profile.company_name] = profile
    return indexedProfiles
  }, {})
}

export default App
