const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'
const MIN_IMPORT_TEXT_LENGTH = 40

const titleElement = document.querySelector('#page-title')
const urlElement = document.querySelector('#page-url')
const countElement = document.querySelector('#page-count')
const cleaningModeElement = document.querySelector('#cleaning-mode')
const statusElement = document.querySelector('#status-message')
const importButton = document.querySelector('#import-button')
const refreshButton = document.querySelector('#refresh-button')
const apiBaseUrlInput = document.querySelector('#api-base-url')
const previewTextArea = document.querySelector('#preview-text')

let collectedPage = null

document.addEventListener('DOMContentLoaded', async () => {
  apiBaseUrlInput.value =
    window.localStorage.getItem('esg_api_base_url') || DEFAULT_API_BASE_URL
  await refreshCurrentPage()
})

refreshButton.addEventListener('click', async () => {
  await refreshCurrentPage()
})

importButton.addEventListener('click', async () => {
  if (!collectedPage) {
    await refreshCurrentPage()
  }

  if (!collectedPage) {
    setStatus('无法读取当前页面，请刷新招聘页后重试。', 'error')
    return
  }

  const rawText = normalizeText(previewTextArea.value)
  if (rawText.length < MIN_IMPORT_TEXT_LENGTH) {
    setStatus('当前预览正文太短，可能不是岗位详情页。', 'error')
    return
  }

  const apiBaseUrl = normalizeApiBaseUrl(apiBaseUrlInput.value)
  window.localStorage.setItem('esg_api_base_url', apiBaseUrl)
  apiBaseUrlInput.value = apiBaseUrl

  setBusy(true)
  setStatus('正在导入到本地 ESG...', '')

  try {
    const response = await fetch(`${apiBaseUrl}/api/imports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        source_type: 'url',
        source_value: collectedPage.url,
        raw_text: rawText,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const result = await response.json()
    setStatus(`已导入 ESG，记录状态：${result.status}`, 'success')
  } catch (error) {
    setStatus(
      `导入失败，请确认后端已启动：${error instanceof Error ? error.message : error}`,
      'error',
    )
  } finally {
    setBusy(false)
  }
})

async function refreshCurrentPage() {
  setBusy(true)
  setStatus('正在读取当前页面...', '')

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (!tab?.id) {
      throw new Error('没有找到当前标签页')
    }

    await ensureContentScript(tab.id)
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'ESG_COLLECT_PAGE',
    })

    if (!response?.ok || !response.page) {
      throw new Error('页面脚本没有返回正文')
    }

    collectedPage = response.page
    renderPageSummary(collectedPage)
    setStatus('', '')
  } catch (error) {
    collectedPage = null
    renderPageSummary(null)
    setStatus(
      `读取失败：${error instanceof Error ? error.message : error}`,
      'error',
    )
  } finally {
    setBusy(false)
  }
}

async function ensureContentScript(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, { type: 'ESG_COLLECT_PAGE' })
  } catch {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ['content.js'],
    })
  }
}

function renderPageSummary(page) {
  if (!page) {
    titleElement.textContent = '未读取到当前页面'
    urlElement.textContent = ''
    cleaningModeElement.textContent = ''
    countElement.textContent = ''
    previewTextArea.value = ''
    return
  }

  const text = buildImportText(page)
  titleElement.textContent = page.title || '未命名页面'
  urlElement.textContent = page.url
  cleaningModeElement.textContent = formatTextSource(page.textSource)
  countElement.textContent = buildCountText(page, text)
  previewTextArea.value = text
}

function buildImportText(page) {
  const text = page.cleanedText || page.text || page.bodyText || ''
  const parts = [
    page.title ? `页面标题：${page.title}` : '',
    page.metaDescription ? `页面描述：${page.metaDescription}` : '',
    text,
  ]
  return normalizeText(parts.filter(Boolean).join('\n\n'))
}

function buildCountText(page, text) {
  const warnings = Array.isArray(page.warnings) ? page.warnings : []
  const warningText = warnings.length ? ` ${warnings.join(' ')}` : ''
  return `预览正文约 ${text.length} 字，可在导入前手动修改。${warningText}`
}

function formatTextSource(textSource) {
  const labels = {
    selection: '读取方式：选中文本',
    boss_cleaned: '读取方式：BOSS DOM 清洗',
    visible_text: '读取方式：页面可见文本',
  }
  return labels[textSource] || '读取方式：页面可见文本'
}

function normalizeApiBaseUrl(value) {
  const trimmed = String(value || DEFAULT_API_BASE_URL).trim()
  return trimmed.replace(/\/+$/, '') || DEFAULT_API_BASE_URL
}

function normalizeText(value) {
  return String(value || '')
    .replace(/\u00a0/g, ' ')
    .replace(/[ \t\r\f\v]+/g, ' ')
    .replace(/ *\n+ */g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function setBusy(isBusy) {
  importButton.disabled = isBusy
  refreshButton.disabled = isBusy
}

function setStatus(message, tone) {
  statusElement.textContent = message
  statusElement.className = tone ? `status-message ${tone}` : 'status-message'
}
