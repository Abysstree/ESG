import { pageLabels, pageOrder } from '../constants/app'
import type { PageId } from '../types/app'

type SidebarProps = {
  activePage: PageId
  onPageChange: (page: PageId) => void
}

function Sidebar({ activePage, onPageChange }: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="ESG navigation">
      <div className="brand">
        <span className="brand-mark">ESG</span>
        <div>
          <h1>EmploymentSkillsGuide</h1>
          <p>岗位信息研究台</p>
        </div>
      </div>

      <nav className="nav-list">
        {pageOrder.map((page) => (
          <button
            key={page}
            className={activePage === page ? 'active' : ''}
            type="button"
            onClick={() => onPageChange(page)}
          >
            {pageLabels[page]}
          </button>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar
