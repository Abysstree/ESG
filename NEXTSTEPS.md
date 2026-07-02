# ESG Roadmap and Project Log

## English Version

This document tracks the implementation route for EmploymentSkillsGuide. Completed work stays checked so the file can also serve as a lightweight project log.

### Confirmed Direction

ESG starts as a local personal tool. Account systems and cloud sync are intentionally deferred to reduce cost, protect privacy, and keep the first milestone focused on the job-information pipeline.

Initial priority:

1. pasted job text.
2. public URL reading.
3. screenshot OCR.
4. browser extension import.
5. LLM extraction and role learning maps.

LLM calls prefer cloud APIs first, while the architecture keeps room for local model providers later.

### Current Stack

- Backend: FastAPI, Python, SQLite, SQLAlchemy, Pydantic.
- Frontend: React, Vite, TypeScript, React Flow.
- Backend environment: `uv`.
- Frontend package manager: `npm`.
- Optional OCR: PaddleOCR.
- Browser import: local Chrome/Edge extension MVP.

### Completed Work

#### Foundation

- [x] Initialize git repository.
- [x] Add `.gitignore`.
- [x] Create backend and frontend folders.
- [x] Add `.env.example`.
- [x] Add local data folders with `.gitkeep` placeholders.
- [x] Select FastAPI, React, Vite, TypeScript, SQLite, `uv`, and `npm`.
- [x] Keep local agent guidance in `AGENTS.md`.
- [x] Remove legacy `AGENT.md`.
- [x] Ignore `AGENTS.md` so local agent instructions are not published.

#### Backend

- [x] Create FastAPI app.
- [x] Add health check endpoint.
- [x] Add raw import endpoints.
- [x] Add job card endpoints.
- [x] Add SQLite models and schema creation.
- [x] Add tests for API startup and database behavior.
- [x] Isolate backend tests from the local personal SQLite database.
- [x] Add CRUD support for job cards.
- [x] Add ordering and pinning support for job cards.

#### Import and Ingestion

- [x] Support pasted-text imports.
- [x] Support screenshot imports.
- [x] Support screenshot drag-and-drop, clipboard paste, and file picker.
- [x] Support public URL reading.
- [x] Add BOSS Zhipin micro-JD detection that reports platform protection instead of bypassing it.
- [x] Add raw import list in the frontend.
- [x] Collapse recent imports under the import page.
- [x] Add deletion for recent imports and generated cards from those imports.
- [x] Add Chrome/Edge browser extension MVP for visible-page text import.
- [x] Add extension popup preview editing.
- [x] Add BOSS visible-DOM cleanup for extension imports without bypassing platform protections.

#### OCR

- [x] Decide OCR should use a dedicated OCR engine instead of LLM vision for the first local MVP.
- [x] Choose PaddleOCR as the first OCR engine to try.
- [x] Add optional backend screenshot OCR with lazy loading.
- [x] Keep OCR optional so text/URL imports and tests still work without PaddleOCR installed.

#### Extraction

- [x] Add mock extractor for pasted recruitment text.
- [x] Improve company detection, section stop handling, and confidence labels.
- [x] Add extraction of salary range, salary period, base location, education, and experience.
- [x] Design formal LLM extraction JSON schema.
- [x] Add OpenAI-compatible provider interface.
- [x] Add DeepSeek official provider and make it the first default provider.
- [x] Add Anthropic and Google Gemini provider interfaces.
- [x] Add custom API base URL support.
- [x] Encrypt locally saved provider API keys.
- [x] Store provider configs with key, base URL, model, enabled state, and active provider.
- [x] Connect active cloud LLM extraction to job card creation.
- [x] Add LLM extraction debug panel with prompt, schema output, normalized JobCard, field sources, evidence, and quality checks.
- [x] Add individual and bulk LLM re-extraction controls.
- [x] Normalize campus and intern titles into suffix format such as `AI算法工程师（应届生）`.
- [x] Preserve multi-city base locations.
- [x] Normalize single base locations to city or city plus district.
- [x] Preserve full work addresses as evidence.
- [x] Prevent model-inferred hard facts from being saved for salary, base location, education, experience, responsibilities, and requirements.
- [x] Allow model-inferred bonus points and skills when clearly marked.

#### Provider and Search Configuration

- [x] Add frontend provider settings inspired by CherryStudio-style workflows.
- [x] Saving an enabled provider with an API key makes it current.
- [x] Surface provider HTTP errors with clearer response details.
- [x] Add `SearchProvider` abstraction.
- [x] Add external-search configuration to API settings.
- [x] Add Exa/Tavily-style search provider support.
- [x] Upgrade company completion from ordinary LLM fill to external-search-first enrichment.
- [x] Mark search-supported fields as `external_search`.
- [x] Fall back to `model_inference` only when search has no useful result.

#### Job Card UI

- [x] Add first job card display.
- [x] Add editable job cards.
- [x] Add save and delete actions.
- [x] Add drag-and-drop custom ordering.
- [x] Add pin/unpin support.
- [x] Add compact job card summaries.
- [x] Expand job card details in place.
- [x] Hide field sources and evidence by default.
- [x] Add company-only hover/focus popover.
- [x] Raise company popovers above following cards.
- [x] Remove irrelevant tags such as extraction provider labels from job cards.
- [x] Hide missing optional tags such as unknown salary or education.

#### Company Profiles

- [x] Add `company_profiles` storage.
- [x] Add company profile read/enrich endpoints.
- [x] Add company profile schema and provider hooks.
- [x] Add frontend company-profile state.
- [x] Add company-only popover with solid background.
- [x] Persist company enrichment.
- [x] Show clear fallback text when ordinary LLM cannot browse or confirm facts.

#### Role Categories

- [x] Add frontend-derived role category summaries.
- [x] Add role category page.
- [x] Add role-category switching inside the learning map page.
- [x] Add active LLM role-profile endpoint.
- [x] Aggregate same-category JobCards for role-profile generation.
- [x] Add role profile generation buttons in role categories and learning map pages.

#### Learning Map

- [x] Add first skill tree and knowledge tree views.
- [x] Replace split skill/knowledge trees with one unified learning map.
- [x] Define LLM role learning-map output schema with `learning_map.branches`.
- [x] Replace fixed-coordinate map with React Flow.
- [x] Add draggable nodes, smooth edges, MiniMap, zoom, pan, and built-in controls.
- [x] Add role-category-specific maps.
- [x] Make role maps open with branches collapsed.
- [x] Make selecting a node open only its next level.
- [x] Keep topic evidence details independently retained.
- [x] Add full expand for all visible final-level details.
- [x] Remove node-level expand/collapse buttons.
- [x] Use double-click to collapse expanded nodes.
- [x] Make reset recenter the canvas and collapse all expanded nodes.
- [x] Keep final learning-point text complete instead of shortening it with ellipses.
- [x] Reserve layout space so expanded nodes do not overlap siblings.

#### Frontend Structure and Design

- [x] Split the frontend into sidebar-driven module pages.
- [x] Move API configuration before job import in the sidebar.
- [x] Refactor frontend files into `pages`, `components`, `utils`, `constants`, and frontend-only `types`.
- [x] Add light, dark, and auto theme modes.
- [x] Fix learning-map light-theme center-node readability.
- [x] Add ReactBits-inspired visual polish: aurora background, spotlight cards, gradient headings, glassy panels, hover states, and reduced-motion protection.
- [x] Split the UI into separate module pages instead of crowding all content on one page.

#### Documentation

- [x] Add project brief.
- [x] Add roadmap and project log.
- [x] Expand README for public GitHub display.
- [x] Rewrite public docs in English-first and Chinese-second format.
- [x] Choose the MIT License and add a root `LICENSE` file.

### Open Work

- [ ] Preserve the full nested LLM learning-map tree in frontend state instead of flattening it into branch item strings.
- [ ] Render arbitrary-depth learning-map nodes with recursive layout and progressive expansion.
- [ ] Add user editing for role profiles and learning-map nodes.
- [ ] Add learning stages such as beginner, intermediate, advanced, project practice, and portfolio.
- [ ] Add frequency and representative evidence for each role requirement.
- [ ] Add better filtering and search across job cards.
- [ ] Add export/import of local data.
- [ ] Add recommendation page for related roles, companies, and official links.
- [ ] Decide whether to move local encryption keys into the OS keychain.
- [ ] Decide when to support a local model provider such as Ollama.
- [ ] Decide whether to add PostgreSQL, accounts, or cloud sync later.
- [x] Choose an open-source license before publishing broadly. MIT was selected on 2026-07-02.

### Project Log

- 2026-06-29: Initialized the local MVP with backend, frontend, git, SQLite, README, and starter import UI.
- 2026-06-29: Added screenshot import, drag-and-drop, clipboard paste, screenshot storage, and OCR direction.
- 2026-06-29: Added mock extraction and first frontend job-card display.
- 2026-06-29: Added job-card edit, save, delete, salary/base/education/experience fields, and first LLM provider interface.
- 2026-06-29: Isolated tests from the personal local SQLite database.
- 2026-06-29: Added job-card ordering and pinning.
- 2026-06-29: Added provider configuration UI for OpenAI-compatible, Anthropic, Gemini, and custom providers.
- 2026-06-30: Added DeepSeek, encrypted API keys, formal LLM extraction schema, and active cloud extraction.
- 2026-06-30: Added theme switching, role summaries, initial learning maps, and agent guidance.
- 2026-06-30: Split frontend pages and replaced split skill/knowledge trees with one learning map.
- 2026-06-30: Added expandable job cards and optional PaddleOCR backend service.
- 2026-06-30: Added URL reading, BOSS protected-page reporting, and browser extension MVP.
- 2026-07-01: Added role-category switching in learning maps and ReactBits-inspired visual polish.
- 2026-07-01: Added extension popup preview editing and BOSS visible-DOM cleanup.
- 2026-07-01: Added LLM extraction debug page and improved DeepSeek testing flow.
- 2026-07-01: Added LLM role-profile and learning-map generation endpoint.
- 2026-07-01: Normalized Base display and added company popovers.
- 2026-07-01: Added company profile storage, endpoints, provider hooks, and frontend state.
- 2026-07-01: Reworked job-card expansion, evidence display, raw import deletion, and inferred bonus/skill handling.
- 2026-07-02: Added external search provider abstraction and external-search-first company enrichment.
- 2026-07-02: Reworked the learning map into a React Flow Xmind-like canvas with progressive expansion.
- 2026-07-02: Refined learning-map interactions: single-click opens next level, double-click collapses, reset recenters and collapses, final nodes keep complete text.
- 2026-07-02: Rewrote public documentation in English-first and Chinese-second format, retained local `AGENTS.md`, and removed legacy `AGENT.md`.
- 2026-07-02: Added the MIT License and updated public documentation to reflect the license decision.

---

## 中文版本

本文档记录 EmploymentSkillsGuide 的实现路线。已完成任务保留勾选状态，因此它也可以作为轻量项目日志。

### 已确认方向

ESG 第一版是本地个人工具。账号系统和云端同步暂时延后，以降低成本、保护隐私，并让第一个里程碑聚焦在岗位信息处理链路。

初始优先级：

1. 粘贴岗位文本。
2. 公开 URL 读取。
3. 截图 OCR。
4. 浏览器扩展导入。
5. LLM 抽取和岗位学习地图。

LLM 优先使用云端 API，同时架构上保留后续接入本地模型提供商的空间。

### 当前技术栈

- 后端：FastAPI、Python、SQLite、SQLAlchemy、Pydantic。
- 前端：React、Vite、TypeScript、React Flow。
- 后端环境：`uv`。
- 前端包管理：`npm`。
- 可选 OCR：PaddleOCR。
- 浏览器导入：本地 Chrome/Edge 扩展 MVP。

### 已完成工作

#### 项目基础

- [x] 初始化 git 仓库。
- [x] 添加 `.gitignore`。
- [x] 创建 backend 和 frontend 目录。
- [x] 添加 `.env.example`。
- [x] 添加本地数据目录和 `.gitkeep` 占位。
- [x] 选择 FastAPI、React、Vite、TypeScript、SQLite、`uv` 和 `npm`。
- [x] 将本地 agent 指南保留为 `AGENTS.md`。
- [x] 删除旧的 `AGENT.md`。
- [x] 忽略 `AGENTS.md`，避免本地 agent 指南发布到公开仓库。

#### 后端

- [x] 创建 FastAPI 应用。
- [x] 添加健康检查接口。
- [x] 添加原始导入接口。
- [x] 添加岗位卡接口。
- [x] 添加 SQLite 模型和 schema 创建。
- [x] 添加 API 启动和数据库行为测试。
- [x] 将后端测试与个人本地 SQLite 数据库隔离。
- [x] 添加岗位卡 CRUD。
- [x] 添加岗位卡排序和置顶支持。

#### 导入与采集

- [x] 支持粘贴文本导入。
- [x] 支持截图导入。
- [x] 支持截图拖拽、剪贴板粘贴和文件选择。
- [x] 支持公开 URL 读取。
- [x] 添加 BOSS 直聘微 JD 检测，遇到平台保护时报告而不是绕过。
- [x] 在前端显示原始导入列表。
- [x] 将最近导入折叠到导入页下方。
- [x] 添加最近导入删除，并同步删除该导入生成的岗位卡。
- [x] 添加 Chrome/Edge 浏览器扩展 MVP，用于导入可见页面文本。
- [x] 添加扩展弹窗预览编辑。
- [x] 添加 BOSS 可见 DOM 清洗，不绕过平台保护。

#### OCR

- [x] 确定第一版 OCR 使用专用 OCR 引擎，而不是 LLM vision。
- [x] 选择 PaddleOCR 作为第一个尝试的 OCR 引擎。
- [x] 添加可选后端截图 OCR，并使用懒加载。
- [x] 保持 OCR 可选，即使未安装 PaddleOCR，文本/URL 导入和测试仍可运行。

#### 抽取

- [x] 添加岗位文本 mock 抽取器。
- [x] 改进公司检测、章节停止规则和置信度标签。
- [x] 添加薪资范围、薪资周期、Base、学历和经验抽取。
- [x] 设计正式 LLM 抽取 JSON schema。
- [x] 添加 OpenAI 兼容提供商接口。
- [x] 添加 DeepSeek 官方提供商，并将其作为第一个默认提供商。
- [x] 添加 Anthropic 和 Google Gemini 提供商接口。
- [x] 添加自定义 API 地址支持。
- [x] 加密本地保存的提供商 API key。
- [x] 保存提供商配置：key、base URL、model、启用状态和当前提供商。
- [x] 将当前云端 LLM 抽取接入岗位卡创建。
- [x] 添加 LLM 抽取调试面板，显示 prompt、schema 输出、标准化岗位卡、字段来源、证据和质量检查。
- [x] 添加单个和批量 LLM 重抽取控制。
- [x] 将校招/实习标题标准化为 `AI算法工程师（应届生）` 这类后缀格式。
- [x] 保留多城市 Base。
- [x] 将单一 Base 标准化为城市或城市加区。
- [x] 将完整工作地址保存为证据。
- [x] 禁止模型推断的硬事实写入薪资、Base、学历、经验、职责和要求。
- [x] 允许模型推断加分项和技能，但必须明确标记。

#### 提供商与联网检索配置

- [x] 添加类似 CherryStudio 工作流的前端提供商设置。
- [x] 保存带 key 的启用提供商时自动设为当前提供商。
- [x] 更清晰地展示提供商 HTTP 错误。
- [x] 添加 `SearchProvider` 抽象。
- [x] 在 API 设置里添加联网检索配置。
- [x] 添加 Exa/Tavily 风格搜索提供商支持。
- [x] 将公司补全从普通 LLM 填写升级为外部搜索优先。
- [x] 将搜索支持字段标记为 `external_search`。
- [x] 只有没有有效搜索结果时才退回 `model_inference`。

#### 岗位卡 UI

- [x] 添加第一版岗位卡显示。
- [x] 添加岗位卡编辑。
- [x] 添加保存和删除。
- [x] 添加拖拽自定义排序。
- [x] 添加置顶/取消置顶。
- [x] 添加紧凑岗位卡摘要。
- [x] 岗位卡详情在原卡片内展开。
- [x] 字段来源和证据默认隐藏。
- [x] 添加仅公司信息悬浮窗。
- [x] 提高公司悬浮窗层级，避免被后续卡片遮挡。
- [x] 从岗位卡标签中移除抽取提供商等无关标签。
- [x] 隐藏薪资未知、学历未知等缺失可选标签。

#### 公司画像

- [x] 添加 `company_profiles` 存储。
- [x] 添加公司画像读取和补全接口。
- [x] 添加公司画像 schema 和 provider hooks。
- [x] 添加前端公司画像状态。
- [x] 添加仅公司信息的实体背景悬浮窗。
- [x] 持久化公司补全结果。
- [x] 当普通 LLM 无法浏览或确认事实时，展示清晰回退文案。

#### 岗位大类

- [x] 添加前端派生岗位大类摘要。
- [x] 添加岗位大类页面。
- [x] 在学习地图页添加岗位大类切换。
- [x] 添加当前 LLM 岗位画像接口。
- [x] 按同类岗位卡聚合生成岗位画像。
- [x] 在岗位大类页和学习地图页添加画像生成按钮。

#### 学习地图

- [x] 添加第一版技能树和知识树视图。
- [x] 将技能树/知识树合并为统一学习地图。
- [x] 定义 LLM 岗位学习地图输出 schema：`learning_map.branches`。
- [x] 用 React Flow 替换固定坐标地图。
- [x] 添加可拖拽节点、平滑连线、MiniMap、缩放、平移和内置控件。
- [x] 添加按岗位大类区分的学习地图。
- [x] 岗位地图默认以分支收起状态打开。
- [x] 选中节点只打开下一层。
- [x] 学习点证据详情可独立保留。
- [x] 全部展开会打开所有可见最终级详情。
- [x] 移除节点内展开/收起按钮。
- [x] 双击收起已展开节点。
- [x] 复位会让画布回中并收起所有展开。
- [x] 最终学习点保留完整文本，不再用省略号截断。
- [x] 为展开节点预留空间，避免覆盖同级节点。

#### 前端结构与设计

- [x] 将前端拆分为侧边栏驱动的模块页面。
- [x] 将 API 配置放到导入岗位之前。
- [x] 将前端拆分为 `pages`、`components`、`utils`、`constants` 和前端专用 `types`。
- [x] 添加浅色、深色和自动主题。
- [x] 修复浅色模式下学习地图中心节点可读性。
- [x] 添加 ReactBits 风格视觉优化：aurora 背景、spotlight 卡片、渐变标题、玻璃面板、hover 状态和减少动画保护。
- [x] 将 UI 拆成独立模块页面，避免所有内容挤在同一页。

#### 文档

- [x] 添加项目 brief。
- [x] 添加路线图和项目日志。
- [x] 扩写 README 用于公开 GitHub 展示。
- [x] 将公开文档重写为英文在前、中文在后的格式。
- [x] 选择 MIT License，并在根目录添加 `LICENSE` 文件。

### 待完成工作

- [ ] 在前端状态中保留完整嵌套 LLM 学习地图树，而不是压平成分支字符串列表。
- [ ] 用递归布局渲染任意深度学习地图节点，并支持渐进展开。
- [ ] 添加岗位画像和学习地图节点的用户编辑。
- [ ] 添加入门、进阶、高阶、项目实践和作品集等学习阶段。
- [ ] 为每个岗位要求添加频率和代表证据。
- [ ] 添加更好的岗位卡筛选和搜索。
- [ ] 添加本地数据导出/导入。
- [ ] 添加相关岗位、公司和官方链接推荐页。
- [ ] 决定是否将本地加密密钥迁移到系统 keychain。
- [ ] 决定何时支持 Ollama 等本地模型提供商。
- [ ] 决定后续是否加入 PostgreSQL、账号系统或云同步。
- [x] 广泛公开前选择开源许可证。已于 2026-07-02 选择 MIT。

### 项目日志

- 2026-06-29：初始化本地 MVP，包含后端、前端、git、SQLite、README 和初始导入 UI。
- 2026-06-29：添加截图导入、拖拽、剪贴板粘贴、截图存储和 OCR 方向。
- 2026-06-29：添加 mock 抽取和第一版前端岗位卡显示。
- 2026-06-29：添加岗位卡编辑、保存、删除、薪资/Base/学历/经验字段和第一版 LLM provider 接口。
- 2026-06-29：将测试与个人本地 SQLite 数据库隔离。
- 2026-06-29：添加岗位卡排序和置顶。
- 2026-06-29：添加 OpenAI 兼容、Anthropic、Gemini 和自定义提供商配置 UI。
- 2026-06-30：添加 DeepSeek、API key 加密、正式 LLM 抽取 schema 和当前云端抽取。
- 2026-06-30：添加主题切换、岗位大类摘要、初始学习地图和 agent 指南。
- 2026-06-30：拆分前端页面，并将技能/知识树替换为统一学习地图。
- 2026-06-30：添加可展开岗位卡和可选 PaddleOCR 后端服务。
- 2026-06-30：添加 URL 读取、BOSS 保护页面报告和浏览器扩展 MVP。
- 2026-07-01：添加学习地图岗位大类切换和 ReactBits 风格视觉优化。
- 2026-07-01：添加扩展弹窗预览编辑和 BOSS 可见 DOM 清洗。
- 2026-07-01：添加 LLM 抽取调试页并改进 DeepSeek 测试流程。
- 2026-07-01：添加 LLM 岗位画像和学习地图生成接口。
- 2026-07-01：标准化 Base 显示并添加公司悬浮窗。
- 2026-07-01：添加公司画像存储、接口、provider hooks 和前端状态。
- 2026-07-01：重做岗位卡展开、证据显示、原始导入删除和推断加分项/技能处理。
- 2026-07-02：添加外部搜索提供商抽象和搜索优先公司补全。
- 2026-07-02：将学习地图重做为 React Flow Xmind 风格渐进画布。
- 2026-07-02：优化学习地图交互：单击打开下一层、双击收起、复位回中并收起、最终节点保留完整文本。
- 2026-07-02：将公开文档重写为英文在前、中文在后，保留本地 `AGENTS.md`，删除旧 `AGENT.md`。
- 2026-07-02：添加 MIT License，并同步更新公开文档中的许可证说明。
