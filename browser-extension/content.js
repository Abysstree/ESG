(() => {
  if (window.__ESG_IMPORTER_READY__) return
  window.__ESG_IMPORTER_READY__ = true

  const MIN_SELECTED_TEXT_LENGTH = 40
  const MIN_CLEANED_TEXT_LENGTH = 80

  const BOSS_SELECTORS = [
    '[class*="job-detail"]',
    '[class*="job-sec"]',
    '[class*="job-primary"]',
    '[class*="job-banner"]',
    '[class*="job-name"]',
    '[class*="job-info"]',
    '[class*="detail-content"]',
    '[class*="company"]',
  ]

  const COMMON_NOISE_PATTERNS = [
    /^$/,
    /^打开.*app$/i,
    /^下载.*app$/i,
    /^立即沟通$/,
    /^继续沟通$/,
    /^去沟通$/,
    /^投递$/,
    /^分享$/,
    /^收藏$/,
    /^保存$/,
    /^举报$/,
    /^反馈$/,
    /^复制$/,
    /^展开$/,
    /^收起$/,
    /^查看全部$/,
    /^加载更多$/,
    /^推荐职位$/,
    /^其他职位$/,
    /^相似职位$/,
    /^附近职位$/,
    /^微信$/,
    /^小程序$/,
    /^二维码$/,
    /^客服$/,
    /^帮助$/,
    /^隐私$/,
    /^用户协议$/,
    /^知道了$/,
    /^我知道了$/,
    /^登录$/,
    /^注册$/,
  ]

  const BOSS_NOISE_PATTERNS = [
    /^boss直聘$/i,
    /^boss直聘.*$/,
    /^直聘$/,
    /^求职安全提示$/,
    /^职位竞争力分析$/,
    /^职位发布者$/,
    /^看过该职位的人还看了$/,
    /^你可能感兴趣$/,
    /^使用.*boss.*app/i,
    /^打开boss直聘app/i,
  ]

  function normalizeText(value) {
    return String(value || '')
      .replace(/\u00a0/g, ' ')
      .replace(/[ \t\r\f\v]+/g, ' ')
      .replace(/ *\n+ */g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim()
  }

  function collectMetaDescription() {
    const meta = document.querySelector(
      'meta[name="description"], meta[property="og:description"]',
    )
    return normalizeText(meta?.getAttribute('content'))
  }

  function isBossPage() {
    const host = window.location.hostname.toLowerCase()
    const url = window.location.href.toLowerCase()
    const title = document.title.toLowerCase()
    return (
      host.endsWith('zhipin.com') ||
      url.includes('zhipin.com') ||
      url.includes('/weijd/') ||
      title.includes('boss直聘')
    )
  }

  function isVisibleElement(element) {
    const style = window.getComputedStyle(element)
    if (style.display === 'none' || style.visibility === 'hidden') return false
    return element.getClientRects().length > 0
  }

  function collectSelectorText(selectors) {
    const values = []
    document.querySelectorAll(selectors.join(',')).forEach((element) => {
      if (!(element instanceof HTMLElement) || !isVisibleElement(element)) return
      const text = normalizeText(element.innerText)
      if (text.length >= 20) {
        values.push(text)
      }
    })
    return normalizeText(values.join('\n\n'))
  }

  function stripLineNoise(line) {
    return normalizeText(line)
      .replace(/^[-•·*]\s*/, '')
      .replace(/\s*(展开|收起)\s*$/, '')
      .trim()
  }

  function shouldDropLine(line, patterns) {
    const normalized = stripLineNoise(line)
    if (!normalized) return true
    if (normalized.length === 1 && !/[A-Za-z0-9一-龥]/.test(normalized)) {
      return true
    }
    return patterns.some((pattern) => pattern.test(normalized))
  }

  function cleanLines(text, extraPatterns = []) {
    const seen = new Set()
    const patterns = [...COMMON_NOISE_PATTERNS, ...extraPatterns]
    const lines = []

    normalizeText(text)
      .split('\n')
      .map(stripLineNoise)
      .forEach((line) => {
        if (shouldDropLine(line, patterns)) return
        const key = line.toLowerCase()
        if (seen.has(key)) return
        seen.add(key)
        lines.push(line)
      })

    return normalizeText(lines.join('\n'))
  }

  function collectBossText(bodyText) {
    const targetedText = collectSelectorText(BOSS_SELECTORS)
    const sourceText =
      targetedText.length >= MIN_CLEANED_TEXT_LENGTH ? targetedText : bodyText
    return cleanLines(sourceText, BOSS_NOISE_PATTERNS)
  }

  function collectPageText() {
    const selectedText = normalizeText(window.getSelection?.().toString())
    const bodyText = normalizeText(document.body?.innerText)
    const metaDescription = collectMetaDescription()
    const title = normalizeText(document.title)
    const bossPage = isBossPage()
    const bossText = bossPage ? collectBossText(bodyText) : ''
    const visibleText = cleanLines(bodyText)
    let text = visibleText
    let textSource = 'visible_text'
    const warnings = []

    if (selectedText.length >= MIN_SELECTED_TEXT_LENGTH) {
      text = selectedText
      textSource = 'selection'
    } else if (bossText.length >= MIN_CLEANED_TEXT_LENGTH) {
      text = bossText
      textSource = 'boss_cleaned'
    } else if (bossPage) {
      warnings.push('BOSS 页面未找到足够稳定的岗位详情区域，已回退到页面可见文本。')
    }

    return {
      url: window.location.href,
      title,
      selectedText,
      bodyText,
      cleanedText: text,
      metaDescription,
      text,
      textSource,
      isBossPage: bossPage,
      warnings,
    }
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== 'ESG_COLLECT_PAGE') return false

    sendResponse({
      ok: true,
      page: collectPageText(),
    })
    return false
  })
})()
