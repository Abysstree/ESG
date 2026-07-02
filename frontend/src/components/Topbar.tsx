import { pageLabels, themePreferenceLabels } from '../constants/app'
import type { ApiStatus, PageId, ThemePreference } from '../types/app'

type TopbarProps = {
  activePage: PageId
  apiStatus: ApiStatus
  themePreference: ThemePreference
  onThemePreferenceChange: (preference: ThemePreference) => void
}

function Topbar({
  activePage,
  apiStatus,
  themePreference,
  onThemePreferenceChange,
}: TopbarProps) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Local MVP</p>
        <h2>{pageLabels[activePage]}</h2>
      </div>
      <div className="topbar-actions">
        <div className="theme-switch" aria-label="主题模式">
          {(['auto', 'light', 'dark'] as ThemePreference[]).map((preference) => (
            <button
              key={preference}
              className={themePreference === preference ? 'selected' : ''}
              type="button"
              onClick={() => onThemePreferenceChange(preference)}
            >
              {themePreferenceLabels[preference]}
            </button>
          ))}
        </div>
        <span className={`status-pill ${apiStatus}`}>
          {apiStatus === 'checking'
            ? '连接中'
            : apiStatus === 'online'
              ? '后端在线'
              : '后端离线'}
        </span>
      </div>
    </header>
  )
}

export default Topbar
