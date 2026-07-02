import type {
  ChangeEvent,
  ClipboardEvent,
  Dispatch,
  DragEvent,
  FormEvent,
  RefObject,
  SetStateAction,
} from 'react'
import type { LLMStatus, RawImport, SourceType } from '../types/api'
import type { TextInputConfig } from '../types/app'

const importStatusLabels: Record<string, string> = {
  created: '已保存',
  mock_extracted: '规则抽取',
  llm_extracted: 'LLM 抽取',
  llm_failed_mock_extracted: 'LLM 失败后规则抽取',
  ocr_extracted: 'OCR 已识别',
  ocr_unavailable: 'OCR 不可用',
  ocr_empty: 'OCR 无正文',
  ocr_failed: 'OCR 失败',
  url_fetched: 'URL 已读取',
  url_fetch_empty: 'URL 无正文',
  url_fetch_failed: 'URL 读取失败',
  url_fetch_protected: '平台限制',
  url_fetch_unsupported: '暂不支持',
}

type ImportPageProps = {
  sourceType: SourceType
  sourceValue: string
  rawText: string
  sourceInput: TextInputConfig | null
  rawTextInput: TextInputConfig
  screenshotFile: File | null
  screenshotPreviewUrl: string | null
  screenshotInputRef: RefObject<HTMLInputElement | null>
  isDraggingScreenshot: boolean
  isSubmitting: boolean
  isRebuilding: boolean
  deletingImportId: number | null
  errorMessage: string | null
  llmStatus: LLMStatus | null
  imports: RawImport[]
  visibleImports: RawImport[]
  showAllImports: boolean
  onSourceTypeChange: (sourceType: SourceType) => void
  onSourceValueChange: (value: string) => void
  onRawTextChange: (value: string) => void
  onDraggingScreenshotChange: Dispatch<SetStateAction<boolean>>
  onScreenshotSelect: (event: ChangeEvent<HTMLInputElement>) => void
  onScreenshotDrop: (event: DragEvent<HTMLDivElement>) => void
  onScreenshotPaste: (event: ClipboardEvent<HTMLDivElement>) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onRebuildMockJobs: () => void
  onDeleteImport: (rawImport: RawImport) => void
  onShowAllImportsChange: Dispatch<SetStateAction<boolean>>
}

function ImportPage({
  sourceType,
  sourceValue,
  rawText,
  sourceInput,
  rawTextInput,
  screenshotFile,
  screenshotPreviewUrl,
  screenshotInputRef,
  isDraggingScreenshot,
  isSubmitting,
  isRebuilding,
  deletingImportId,
  errorMessage,
  llmStatus,
  imports,
  visibleImports,
  showAllImports,
  onSourceTypeChange,
  onSourceValueChange,
  onRawTextChange,
  onDraggingScreenshotChange,
  onScreenshotSelect,
  onScreenshotDrop,
  onScreenshotPaste,
  onSubmit,
  onRebuildMockJobs,
  onDeleteImport,
  onShowAllImportsChange,
}: ImportPageProps) {
  function getImportPreview(item: RawImport) {
    if (item.raw_text) return item.raw_text

    if (item.status === 'url_fetch_protected') {
      return '该平台返回环境校验；ESG 不做登录或反爬绕过，可以改用页面正文粘贴或截图导入。'
    }

    if (item.status === 'url_fetch_empty') {
      return '链接打开成功，但 HTML 中没有足够正文，可能由前端 JS 二次加载。'
    }

    if (item.status === 'url_fetch_failed') {
      return '链接读取失败，请检查页面是否公开可访问，或粘贴页面正文作为备份。'
    }

    if (item.status === 'url_fetch_unsupported') {
      return '这个链接类型暂不支持自动读取。'
    }

    if (item.status.startsWith('ocr_')) {
      return 'OCR 没有得到可用于抽取的正文，可以手动粘贴识别结果。'
    }

    return '等待后续链接读取或 OCR 解析。'
  }

  function getImportStatusLabel(status: string) {
    return importStatusLabels[status] ?? status
  }

  function getImportStatusTone(status: string) {
    if (status.includes('failed') || status.includes('protected')) return 'warning'
    if (status.includes('empty') || status.includes('unsupported')) return 'muted'
    if (status.includes('extracted') || status === 'url_fetched') return 'success'
    return ''
  }

  return (
    <>
      <section className="content-grid">
        <form className="import-panel" id="import" onSubmit={onSubmit}>
          <div className="section-heading">
            <p className="eyebrow">Import</p>
            <h3>新增岗位来源</h3>
          </div>

          <div className="mode-tabs" aria-label="导入方式">
            <button
              type="button"
              className={sourceType === 'url' ? 'selected' : ''}
              onClick={() => onSourceTypeChange('url')}
            >
              链接
            </button>
            <button
              type="button"
              className={sourceType === 'text' ? 'selected' : ''}
              onClick={() => onSourceTypeChange('text')}
            >
              文本
            </button>
            <button
              type="button"
              className={sourceType === 'screenshot' ? 'selected' : ''}
              onClick={() => onSourceTypeChange('screenshot')}
            >
              截图
            </button>
          </div>

          {sourceInput ? (
            <label className="field">
              <span>{sourceInput.label}</span>
              <input
                value={sourceValue}
                onChange={(event) => onSourceValueChange(event.target.value)}
                placeholder={sourceInput.placeholder}
              />
            </label>
          ) : null}

          {sourceType === 'screenshot' ? (
            <div className="field">
              <span>截图</span>
              <input
                ref={screenshotInputRef}
                className="visually-hidden"
                type="file"
                accept="image/*"
                onChange={onScreenshotSelect}
              />
              <div
                className={`screenshot-dropzone ${
                  isDraggingScreenshot ? 'dragging' : ''
                }`}
                role="button"
                tabIndex={0}
                onClick={() => screenshotInputRef.current?.click()}
                onDragEnter={(event) => {
                  event.preventDefault()
                  onDraggingScreenshotChange(true)
                }}
                onDragLeave={() => onDraggingScreenshotChange(false)}
                onDragOver={(event) => event.preventDefault()}
                onDrop={onScreenshotDrop}
                onPaste={onScreenshotPaste}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    screenshotInputRef.current?.click()
                  }
                }}
              >
                {screenshotPreviewUrl ? (
                  <div className="screenshot-preview">
                    <img src={screenshotPreviewUrl} alt="已选择的岗位截图预览" />
                    <div>
                      <strong>{screenshotFile?.name}</strong>
                      <span>
                        {screenshotFile ? `${Math.ceil(screenshotFile.size / 1024)} KB` : ''}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="dropzone-copy">
                    <strong>拖拽截图到这里，或直接 Ctrl+V 粘贴</strong>
                    <span>也可以点击选择图片文件。</span>
                  </div>
                )}
              </div>
            </div>
          ) : null}

          <label className="field">
            <span>{rawTextInput.label}</span>
            <textarea
              value={rawText}
              onChange={(event) => onRawTextChange(event.target.value)}
              placeholder={rawTextInput.placeholder}
            />
          </label>

          {errorMessage ? (
            <p className="form-error" role="alert">
              {errorMessage}
            </p>
          ) : null}

          <button className="primary-action" type="submit" disabled={isSubmitting}>
            {isSubmitting ? '保存中' : '保存导入记录'}
          </button>
        </form>

        <section className="status-panel" aria-label="MVP status">
          <div className="section-heading">
            <p className="eyebrow">Pipeline</p>
            <h3>第一阶段骨架</h3>
          </div>

          <ol className="pipeline-list">
            <li className="done">FastAPI 后端</li>
            <li className="done">SQLite 本地库</li>
            <li className="done">React 前端</li>
            <li className="done">公开 URL 读取</li>
            <li className="done">Mock 结构化抽取</li>
            <li className="done">岗位卡片生成</li>
            <li className={llmStatus?.configured ? 'done' : ''}>
              LLM 接口：{llmStatus?.provider ?? '检查中'}
            </li>
            <li>学习地图</li>
          </ol>

          <button
            className="secondary-action"
            type="button"
            onClick={onRebuildMockJobs}
            disabled={isRebuilding}
          >
            {isRebuilding ? '重新抽取中' : '重新规则抽取'}
          </button>
        </section>
      </section>

      <section className="records-section compact-import-history">
        <div className="section-heading inline-heading">
          <div>
            <p className="eyebrow">Raw Imports</p>
            <h3>最近导入</h3>
          </div>
          {imports.length > 2 ? (
            <button
              className="text-action"
              type="button"
              onClick={() => onShowAllImportsChange((currentValue) => !currentValue)}
            >
              {showAllImports ? '收起' : `显示全部 ${imports.length} 条`}
            </button>
          ) : null}
        </div>

        {imports.length === 0 ? (
          <div className="empty-state">
            <p>还没有导入记录。</p>
          </div>
        ) : (
          <div className="import-list">
            {visibleImports.map((item) => (
              <article className="import-card" key={item.id}>
                <div>
                  <span className="source-chip">{item.source_type}</span>
                  <span
                    className={`import-status-chip ${getImportStatusTone(item.status)}`}
                  >
                    {getImportStatusLabel(item.status)}
                  </span>
                  <h4>{item.source_value}</h4>
                  <button
                    className="danger-action import-delete-action"
                    type="button"
                    onClick={() => onDeleteImport(item)}
                    disabled={deletingImportId === item.id}
                  >
                    {deletingImportId === item.id ? '删除中' : '删除'}
                  </button>
                </div>
                <p>{getImportPreview(item)}</p>
                <time dateTime={item.created_at}>
                  {new Date(item.created_at).toLocaleString()}
                </time>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  )
}

export default ImportPage
