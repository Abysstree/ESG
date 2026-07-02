import {
  AUTO_DARK_END_HOUR,
  AUTO_DARK_START_HOUR,
  THEME_STORAGE_KEY,
} from '../constants/app'
import type { ThemeMode, ThemePreference } from '../types/app'

export function getInitialThemePreference(): ThemePreference {
  if (typeof window === 'undefined') return 'auto'
  const storedValue = window.localStorage.getItem(THEME_STORAGE_KEY)
  return storedValue === 'auto' || storedValue === 'light' || storedValue === 'dark'
    ? storedValue
    : 'auto'
}

export function getAutoThemeMode(date = new Date()): ThemeMode {
  const hour = date.getHours()
  return hour >= AUTO_DARK_START_HOUR || hour < AUTO_DARK_END_HOUR ? 'dark' : 'light'
}

export function resolveThemeMode(preference: ThemePreference): ThemeMode {
  return preference === 'auto' ? getAutoThemeMode() : preference
}
