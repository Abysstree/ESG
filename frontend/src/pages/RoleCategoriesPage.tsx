import type { LLMRoleProfileResult } from '../types/api'
import type { RoleSummary } from '../types/app'

type RoleCategoriesPageProps = {
  roleSummaries: RoleSummary[]
  selectedRole: RoleSummary | null
  roleProfileResult: LLMRoleProfileResult | null
  generatingRoleProfileName: string | null
  errorMessage: string | null
  onSelectedRoleChange: (roleName: string) => void
  onGenerateRoleProfile: (roleName: string) => void
}

function RoleCategoriesPage({
  roleSummaries,
  selectedRole,
  roleProfileResult,
  generatingRoleProfileName,
  errorMessage,
  onSelectedRoleChange,
  onGenerateRoleProfile,
}: RoleCategoriesPageProps) {
  return (
    <section className="records-section role-section" id="roles">
      <div className="section-heading">
        <p className="eyebrow">Role Categories</p>
        <h3>岗位大类</h3>
      </div>

      {errorMessage ? <p className="form-error">{errorMessage}</p> : null}

      {roleSummaries.length === 0 ? (
        <div className="empty-state">
          <p>还没有可聚合的岗位大类。</p>
        </div>
      ) : (
        <div className="role-layout">
          <div className="role-list" aria-label="岗位大类列表">
            {roleSummaries.map((role) => (
              <button
                key={role.name}
                className={selectedRole?.name === role.name ? 'selected' : ''}
                type="button"
                onClick={() => onSelectedRoleChange(role.name)}
              >
                <span>{role.name}</span>
                <small>{role.jobCount} 个岗位</small>
              </button>
            ))}
          </div>

          {selectedRole ? (
            <div className="role-profile">
              <header>
                <div>
                  <h4>{selectedRole.name}</h4>
                  <p>{selectedRole.titles.slice(0, 3).join(' / ') || '岗位样本待补全'}</p>
                </div>
                <div className="role-profile-actions">
                  <span>{selectedRole.jobCount} jobs</span>
                  <button
                    className="text-action"
                    type="button"
                    onClick={() => onGenerateRoleProfile(selectedRole.name)}
                    disabled={generatingRoleProfileName === selectedRole.name}
                  >
                    {generatingRoleProfileName === selectedRole.name
                      ? 'LLM生成中'
                      : 'LLM生成画像'}
                  </button>
                </div>
              </header>

              {roleProfileResult ? (
                <section className="role-llm-profile">
                  <div>
                    <strong>LLM岗位画像</strong>
                    <span>
                      {roleProfileResult.provider} · {roleProfileResult.mode} ·{' '}
                      {roleProfileResult.role_profile.confidence}
                    </span>
                  </div>
                  <p>{roleProfileResult.role_profile.summary}</p>
                  {roleProfileResult.role_profile.inference_notes.length > 0 ? (
                    <small>
                      {roleProfileResult.role_profile.inference_notes.slice(0, 2).join(' / ')}
                    </small>
                  ) : null}
                </section>
              ) : null}

              <div className="role-facts">
                <div>
                  <strong>公司</strong>
                  <span>{selectedRole.companies.join('、') || '待补全'}</span>
                </div>
                <div>
                  <strong>Base</strong>
                  <span>{selectedRole.baseLocations.join('、') || '待补全'}</span>
                </div>
                <div>
                  <strong>薪资</strong>
                  <span>{selectedRole.salarySamples.join('、') || '待补全'}</span>
                </div>
                <div>
                  <strong>门槛</strong>
                  <span>
                    {[
                      ...selectedRole.educationRequirements,
                      ...selectedRole.experienceRequirements,
                    ].join('、') || '待补全'}
                  </span>
                </div>
              </div>

              <div className="role-columns">
                <section>
                  <h5>高频技能</h5>
                  <div className="skill-list">
                    {selectedRole.topSkills.slice(0, 10).map((skill) => (
                      <span key={skill}>{skill}</span>
                    ))}
                  </div>
                </section>
                <section>
                  <h5>共同职责</h5>
                  <ul>
                    {selectedRole.commonResponsibilities.slice(0, 4).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>
                <section>
                  <h5>共同要求</h5>
                  <ul>
                    {selectedRole.commonRequirements.slice(0, 4).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}

export default RoleCategoriesPage
