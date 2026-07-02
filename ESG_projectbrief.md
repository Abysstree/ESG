# EmploymentSkillsGuide Project Brief

## English Version

### 1. Project Identity

EmploymentSkillsGuide, abbreviated as ESG, is a local-first career research tool. It turns real job postings into structured job cards, role category profiles, company profiles, and learning maps.

The product idea comes from a simple observation: studying against real hiring requirements is often more direct than studying only against university training plans, course outlines, or exam scopes. Job postings expose what companies currently ask for: responsibilities, hard skills, tools, domain knowledge, research habits, collaboration traits, and bonus signals.

### 2. One-Line Vision

ESG helps users convert scattered job postings into an evidence-backed map of what to learn, what to build, and which roles they are moving toward.

### 3. Target Users

The initial target user is a student or early-career job seeker exploring career directions and learning paths. Later versions may also serve career switchers, mentors, career advisors, and university employment-support scenarios.

### 4. Core Problem

The current manual workflow is inefficient:

- users browse recruitment apps and websites.
- interesting companies and postings are saved in separate platforms.
- highly relevant job descriptions are copied into notes.
- similar roles must be summarized manually.
- company background, role classification, learning priorities, and skill trees remain hard to maintain over time.

ESG should turn this process into a structured, editable, and accumulated personal knowledge base.

### 5. MVP Product Direction

The first version is a local personal tool, not a cloud account product. This keeps cost low, reduces privacy risk, and lets the project focus on the core job-information pipeline.

Primary input modes:

- pasted job text.
- publicly accessible job URLs.
- screenshots with optional local OCR.
- browser extension import from the visible page.

Primary outputs:

- job cards.
- company profiles.
- role category profiles.
- role-aligned learning maps.
- extraction debug views for checking LLM behavior.

### 6. Core User Flow

1. The user imports a job posting through pasted text, URL, screenshot, or browser extension.
2. ESG stores the raw import.
3. ESG extracts structured job fields with field sources and evidence.
4. ESG enriches company information through external search when configured.
5. ESG creates or updates a job card.
6. ESG classifies the job into a role category.
7. ESG aggregates similar job cards into a role profile.
8. ESG generates or updates a learning map for that role category.
9. The user edits incorrect fields, categories, company facts, and map nodes.

### 7. Current Technical Stack

- Backend: FastAPI, Python, SQLite, SQLAlchemy, Pydantic.
- Frontend: React, Vite, TypeScript, React Flow.
- Local data: SQLite database plus local raw/screenshot folders.
- OCR: optional PaddleOCR service with lazy loading.
- LLM providers: DeepSeek, OpenAI-compatible APIs, Anthropic, Google Gemini, and custom API base URLs.
- Search providers: Exa/Tavily-style abstraction for external company enrichment.
- Browser extension: local Chrome/Edge MVP for visible-page import.

### 8. Key Product Outputs

#### Job Card

A job card should include:

- title.
- company name.
- role category.
- salary range and salary period.
- base location, limited to city or city plus district.
- education requirement.
- experience requirement.
- responsibilities.
- requirements.
- bonus points.
- skills and tools.
- source URL or import source.
- field sources, evidence snippets, and confidence.
- user edits.

Hard facts such as salary, base location, education, experience, responsibilities, and requirements must come from the original posting or user edits. The model may infer analytical fields such as possible bonus points and skills, but those fields must be clearly marked as model inference.

#### Company Profile

A company profile should include:

- company name.
- summary.
- industry.
- financing or listing stage.
- scale.
- headquarters.
- official website.
- official careers page.
- source URLs.
- field sources and confidence.

When external search is configured, company enrichment should use search first and mark confirmed fields as `external_search`. If no useful search result exists, ordinary model inference may be used only with clear labeling.

#### Role Category Profile

A role category profile should include:

- role category name.
- representative titles.
- sample count.
- common responsibilities.
- common requirements.
- high-frequency skills.
- bonus signals.
- company and location patterns.
- inference notes and confidence.

Role categories must be user-correctable because role boundaries can be fuzzy.

#### Learning Map

Learning maps should align to role categories, not isolated job cards. The LLM output contract should preserve a tree:

- `learning_map.center_title`.
- `learning_map.center_subtitle`.
- `learning_map.branches[]`.
- `learning_map.branches[].nodes[]`.
- nested `children`.
- each node has `node_type`, `level`, `source_fields`, `evidence`, and optional children.

The frontend should render this as an Xmind-like map:

- default view shows the center and first-level branches.
- selecting a node reveals only its next level.
- final learning points show complete text.
- double-click collapses expanded nodes.
- reset recenters the canvas and collapses all expansions.

### 9. Data Quality Principles

- Every important field should distinguish fact, external search, user edit, model inference, and missing data.
- Evidence snippets or source URLs should be preserved whenever possible.
- If evidence is unavailable, mark that explicitly.
- Model inference must not be presented as confirmed fact.
- User edits are authoritative.
- Private local data should not be uploaded unnecessarily.

### 10. Platform and Compliance Principles

ESG should not bypass login walls, anti-bot systems, or recruitment platform protections. For protected pages, the MVP should rely on:

- user-pasted text.
- screenshots.
- browser extension import of content the user can already see.
- public pages that are accessible without evasion.

### 11. Important Risks

- LLM hallucination can produce false job or company facts.
- Recruitment pages vary greatly by platform and may be protected.
- Company facts require reliable sourcing.
- Role categories can overlap.
- Learning maps can become visually crowded without careful progressive disclosure.
- Local API keys and personal job data must be protected.

### 12. Open Questions

- When should the project move from SQLite to PostgreSQL?
- Should cloud sync and accounts be added later?
- Which recruitment platforms deserve dedicated adapters?
- Which local model provider should be supported first?
- How should user resumes, current skills, courses, and projects connect to role gap analysis?
- How should learning-map trees evolve from local heuristics to full LLM-generated nested maps?

### 13. License

ESG uses the MIT License for public code. This keeps the early project easy to try, fork, learn from, and contribute to.

---

## 中文版本

### 1. 项目身份

EmploymentSkillsGuide，简称 ESG，是一个本地优先的职业研究工具。它将真实岗位招聘信息转化为结构化岗位卡、岗位大类画像、公司画像和学习地图。

这个产品想法来自一个很直接的观察：相比只围绕大学培养方案、课程大纲或考试范围学习，对照真实招聘要求学习往往更贴近行业需求。岗位招聘信息会暴露公司当前真正需要的内容：岗位职责、硬技能、工具链、领域知识、研究习惯、协作特质和加分信号。

### 2. 一句话愿景

ESG 帮助用户把零散岗位信息转化为有证据支撑的学习地图，明确应该学什么、做什么项目、朝哪个岗位方向成长。

### 3. 目标用户

初始目标用户是正在探索职业方向和学习路径的学生或早期求职者。后续也可以扩展到转行者、导师、职业规划顾问和高校就业指导场景。

### 4. 核心问题

当前手动流程效率很低：

- 用户浏览招聘软件和招聘网站。
- 感兴趣的公司和岗位分散收藏在不同平台。
- 特别相关的岗位描述会被复制到备忘录。
- 相似岗位需要人工反复总结。
- 公司背景、岗位分类、学习优先级和技能树很难长期维护。

ESG 要把这个流程变成结构化、可编辑、可长期积累的个人知识库。

### 5. MVP 产品方向

第一版是本地个人工具，不做云端账号产品。这样可以降低成本、减少隐私风险，并把注意力集中在岗位信息处理链路本身。

主要输入方式：

- 粘贴岗位文本。
- 公开可访问岗位 URL。
- 截图与可选本地 OCR。
- 浏览器扩展导入当前可见页面。

主要输出：

- 岗位卡。
- 公司画像。
- 岗位大类画像。
- 岗位大类对齐的学习地图。
- 用于检查 LLM 行为的抽取调试面板。

### 6. 核心用户流程

1. 用户通过粘贴文本、URL、截图或浏览器扩展导入岗位。
2. ESG 保存原始导入记录。
3. ESG 抽取结构化岗位字段，并保存字段来源和证据。
4. 配置联网检索后，ESG 用外部搜索补全公司信息。
5. ESG 创建或更新岗位卡。
6. ESG 将岗位归入岗位大类。
7. ESG 聚合同类岗位卡生成岗位大类画像。
8. ESG 为该岗位大类生成或更新学习地图。
9. 用户修正错误字段、岗位大类、公司事实和学习地图节点。

### 7. 当前技术栈

- 后端：FastAPI、Python、SQLite、SQLAlchemy、Pydantic。
- 前端：React、Vite、TypeScript、React Flow。
- 本地数据：SQLite 数据库，以及本地 raw/screenshot 文件夹。
- OCR：可选 PaddleOCR 服务，懒加载。
- LLM 提供商：DeepSeek、OpenAI 兼容 API、Anthropic、Google Gemini 和自定义 API 地址。
- 搜索提供商：Exa/Tavily 风格抽象，用于公司外部补全。
- 浏览器扩展：本地 Chrome/Edge MVP，用于导入当前可见页面。

### 8. 核心产品输出

#### 岗位卡

岗位卡应包含：

- 岗位名称。
- 公司名称。
- 岗位大类。
- 薪资范围和薪资周期。
- Base 地点，限制为城市或城市加区。
- 学历要求。
- 经验要求。
- 岗位职责。
- 任职要求。
- 加分项。
- 技能与工具。
- 来源 URL 或导入来源。
- 字段来源、证据片段和置信度。
- 用户编辑。

薪资、Base、学历、经验、岗位职责和任职要求等硬事实必须来自原始岗位或用户编辑。模型可以推断加分项、技能等分析性字段，但必须清楚标记为模型推断。

#### 公司画像

公司画像应包含：

- 公司名称。
- 公司简介。
- 行业。
- 融资或上市阶段。
- 规模。
- 总部。
- 官网。
- 官方招聘页。
- 来源 URL。
- 字段来源和置信度。

如果配置了外部搜索，公司补全应先使用搜索结果，并将确认字段标记为 `external_search`。如果没有有效搜索结果，普通模型推断只能在明确标记的情况下使用。

#### 岗位大类画像

岗位大类画像应包含：

- 岗位大类名称。
- 代表岗位标题。
- 样本数量。
- 共性岗位职责。
- 共性任职要求。
- 高频技能。
- 加分信号。
- 公司和地点模式。
- 推断说明和置信度。

岗位边界可能模糊，因此岗位大类必须允许用户修正。

#### 学习地图

学习地图应对齐岗位大类，而不是孤立岗位卡。LLM 输出契约应保留树结构：

- `learning_map.center_title`。
- `learning_map.center_subtitle`。
- `learning_map.branches[]`。
- `learning_map.branches[].nodes[]`。
- 嵌套 `children`。
- 每个节点包含 `node_type`、`level`、`source_fields`、`evidence` 和可选 children。

前端应渲染成类似 Xmind 的地图：

- 默认只显示中心和一级分支。
- 选中节点只显示下一层。
- 最终学习点显示完整文本。
- 双击收起已展开节点。
- 复位会让画布回到中心并收起所有展开。

### 9. 数据质量原则

- 每个重要字段都要区分事实、外部搜索、用户编辑、模型推断和缺失。
- 尽量保留证据片段或来源 URL。
- 没有证据时明确标记。
- 模型推断不能伪装成已确认事实。
- 用户编辑具有最高优先级。
- 本地私密数据不应被不必要地上传。

### 10. 平台与合规原则

ESG 不应绕过登录墙、反爬系统或招聘平台保护。对于受保护页面，MVP 应依赖：

- 用户粘贴文本。
- 截图。
- 浏览器扩展导入用户已经能看到的内容。
- 不需要规避手段即可访问的公开页面。

### 11. 重要风险

- LLM 幻觉可能生成错误岗位或公司事实。
- 招聘页面平台差异很大，且可能有保护机制。
- 公司事实需要可靠来源。
- 岗位大类可能互相重叠。
- 学习地图如果没有渐进展开，很容易视觉拥挤。
- 本地 API key 和个人岗位数据必须被保护。

### 12. 开放问题

- 什么时候从 SQLite 迁移到 PostgreSQL？
- 后续是否加入云同步和账号体系？
- 哪些招聘平台值得做专用适配器？
- 第一个本地模型提供商应该支持哪个？
- 用户简历、当前技能、课程和项目如何接入岗位差距分析？
- 学习地图如何从本地启发式逐步升级成完整 LLM 生成的嵌套地图？

### 13. 许可证

ESG 公开代码采用 MIT License。这样早期项目更容易被试用、fork、学习和贡献。
