import { pageOrder } from '../constants/app'
import type { PageId } from '../types/app'

export function getInitialPage(): PageId {
  if (typeof window === 'undefined') return 'providers'
  const hashValue = window.location.hash.replace('#', '')
  return pageOrder.includes(hashValue as PageId) ? (hashValue as PageId) : 'providers'
}
