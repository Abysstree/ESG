# EmploymentSkillsGuide

## English Version

EmploymentSkillsGuide, abbreviated as ESG, is a local-first tool for turning real job postings into structured job cards, company profiles, role category profiles, and learning maps.

ESG is built around a practical learning idea: instead of studying only from university syllabi or exam outlines, users can study from the requirements that companies actually publish in job postings. The app helps collect, extract, compare, and aggregate those requirements into a personal career-learning workspace.

### What ESG Can Do

- Import job postings from pasted text, public URLs, screenshots, or a local browser extension.
- Extract job title, company, salary, base location, education, experience, responsibilities, requirements, bonus points, skills, and tools.
- Distinguish original posting facts, external search results, user edits, model inference, and missing data.
- Configure cloud LLM providers, including DeepSeek, OpenAI-compatible APIs, Anthropic, Google Gemini, and custom API bases.
- Encrypt locally saved provider API keys.
- Configure external search providers for company enrichment.
- Create editable job cards.
- Group jobs into role categories.
- Generate role category profiles.
- Render Xmind-like learning maps with progressive expansion, zoom, pan, MiniMap, reset, and double-click collapse.
- Debug LLM extraction through a preview panel before saving results.
- Use optional local OCR for screenshot imports.
- Use a Chrome/Edge extension MVP to import visible page content from recruitment pages the user can already access.

### Product Principles

- Facts and inference must be separated.
- Hard facts such as salary, base location, education, experience, responsibilities, and requirements must come from the original posting or user edits.
- Model inference may help with analytical fields such as likely skills or bonus points, but inferred content must be labeled.
- Company enrichment should use external search first when configured.
- ESG does not bypass login walls, anti-bot systems, or recruitment platform protections.
- User data is private local personal data by default.

### Current Stack

Backend:

- FastAPI.
- Python.
- SQLite.
- SQLAlchemy.
- Pydantic.
- Optional PaddleOCR integration.

Frontend:

- React.
- Vite.
- TypeScript.
- React Flow.
- Oxlint.

Local tooling:

- `uv` for the backend Python environment.
- `npm` for the frontend.
- Chrome/Edge unpacked extension for local page import.

### Repository Structure

```text
ESG/
  backend/
    app/
      api/
      db/
      extraction/
      llm/
      services/
    tests/
  frontend/
    src/
      api/
      components/
      constants/
      pages/
      types/
      utils/
  browser-extension/
  data/
    raw/
    screenshots/
  ESG_projectbrief.md
  NEXTSTEPS.md
  README.md
```

### Local Development

#### Backend

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Default backend URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
GET http://127.0.0.1:8000/api/health
```

#### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Default frontend URL:

```text
http://127.0.0.1:5173
```

### Environment Configuration

Copy `.env.example` and fill in local values as needed. Do not commit real API keys.

LLM and search provider settings can also be configured from the frontend settings page. Saved API keys are encrypted before being stored in the local SQLite database.

### Optional Screenshot OCR

Screenshot OCR is optional. The backend tries to lazy-load PaddleOCR only when a screenshot import needs OCR. If PaddleOCR is not installed, screenshot records can still be saved and ordinary text/URL imports continue to work.

To enable real local OCR, install PaddleOCR and a PaddlePaddle package compatible with your Python version, operating system, and hardware.

### Browser Extension MVP

The `browser-extension/` folder contains a local Chrome/Edge extension.

Usage:

1. Start the backend.
2. Open Chrome or Edge extension management.
3. Enable developer mode.
4. Load `browser-extension/` as an unpacked extension.
5. Open a recruitment page that you can already access.
6. Select the job description text if the page contains too much unrelated content.
7. Use the extension popup to preview, edit, and import visible text into ESG.

The extension is not an anti-bot or login-bypass tool. It only imports content visible to the user.

### Useful Commands

Backend tests:

```powershell
cd backend
uv run pytest
```

Frontend lint:

```powershell
cd frontend
npm run lint
```

Frontend build:

```powershell
cd frontend
npm run build
```

### Documentation

- `ESG_projectbrief.md`: product vision, scope, data contracts, risks, and open questions.
- `NEXTSTEPS.md`: implementation roadmap and project log.
- `browser-extension/README.md`: extension-specific usage notes.

### Privacy and Safety

ESG is local-first. Local databases, screenshots, raw imports, secrets, and generated artifacts are excluded from git by default.

Before publishing or sharing a fork, check that you are not committing:

- `.env` files.
- SQLite databases.
- screenshots.
- raw imported job text.
- API key encryption material.
- provider API keys.

### Project Status

ESG is an early local MVP. The current implementation already covers the main loop from import to extraction, job cards, provider settings, company enrichment, role profiles, and interactive learning maps. The next major product step is to preserve full nested LLM learning-map trees in the frontend instead of flattening them into simple branch item lists.

### License

No license has been selected yet.

---

## 中文版本

EmploymentSkillsGuide，简称 ESG，是一个本地优先工具，用于将真实岗位招聘信息转化为结构化岗位卡、公司画像、岗位大类画像和学习地图。

ESG 的核心学习理念很朴素：相比只按照大学培养方案或考试大纲学习，用户也可以直接按照公司真实发布的岗位要求学习。这个应用帮助用户收集、抽取、比较和聚合这些要求，把它们变成个人职业学习工作台。

### ESG 能做什么

- 通过粘贴文本、公开 URL、截图或本地浏览器扩展导入岗位。
- 抽取岗位名称、公司、薪资、Base、学历、经验、岗位职责、任职要求、加分项、技能和工具。
- 区分原文事实、外部搜索结果、用户编辑、模型推断和缺失数据。
- 配置云端 LLM 提供商，包括 DeepSeek、OpenAI 兼容 API、Anthropic、Google Gemini 和自定义 API 地址。
- 加密本地保存的模型 API key。
- 配置外部搜索提供商，用于公司信息补全。
- 创建可编辑岗位卡。
- 将岗位归入岗位大类。
- 生成岗位大类画像。
- 渲染类似 Xmind 的学习地图，支持渐进展开、缩放、平移、MiniMap、复位和双击收起。
- 通过抽取调试面板在保存前查看 LLM 抽取效果。
- 使用可选本地 OCR 处理截图导入。
- 使用 Chrome/Edge 扩展 MVP 导入用户已经能访问的招聘页面可见内容。

### 产品原则

- 事实和推断必须分开。
- 薪资、Base、学历、经验、岗位职责和任职要求等硬事实必须来自原始岗位或用户编辑。
- 模型可以辅助分析可能技能或加分项，但推断内容必须标记。
- 配置外部搜索后，公司补全应优先使用外部搜索。
- ESG 不绕过登录墙、反爬系统或招聘平台保护。
- 用户数据默认是本地个人隐私数据。

### 当前技术栈

后端：

- FastAPI。
- Python。
- SQLite。
- SQLAlchemy。
- Pydantic。
- 可选 PaddleOCR 集成。

前端：

- React。
- Vite。
- TypeScript。
- React Flow。
- Oxlint。

本地工具：

- 后端 Python 环境使用 `uv`。
- 前端使用 `npm`。
- 本地页面导入使用 Chrome/Edge 未打包扩展。

### 仓库结构

```text
ESG/
  backend/
    app/
      api/
      db/
      extraction/
      llm/
      services/
    tests/
  frontend/
    src/
      api/
      components/
      constants/
      pages/
      types/
      utils/
  browser-extension/
  data/
    raw/
    screenshots/
  ESG_projectbrief.md
  NEXTSTEPS.md
  README.md
```

### 本地开发

#### 后端

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

默认后端地址：

```text
http://127.0.0.1:8000
```

健康检查：

```text
GET http://127.0.0.1:8000/api/health
```

#### 前端

```powershell
cd frontend
npm install
npm run dev
```

默认前端地址：

```text
http://127.0.0.1:5173
```

### 环境配置

复制 `.env.example` 并按需填写本地值。不要提交真实 API key。

LLM 和搜索提供商也可以在前端配置页中设置。保存的 API key 会先加密，再写入本地 SQLite 数据库。

### 可选截图 OCR

截图 OCR 是可选功能。后端只会在截图导入需要 OCR 时懒加载 PaddleOCR。如果没有安装 PaddleOCR，截图记录仍可保存，普通文本和 URL 导入不受影响。

如需启用真实本地 OCR，请安装 PaddleOCR，以及与 Python 版本、操作系统和硬件匹配的 PaddlePaddle 包。

### 浏览器扩展 MVP

`browser-extension/` 文件夹包含本地 Chrome/Edge 扩展。

使用方式：

1. 启动后端。
2. 打开 Chrome 或 Edge 扩展管理页。
3. 启用开发者模式。
4. 将 `browser-extension/` 作为未打包扩展加载。
5. 打开一个你已经可以访问的招聘页面。
6. 如果页面包含过多无关内容，先选中岗位描述文本。
7. 使用扩展弹窗预览、编辑并导入可见文本到 ESG。

扩展不是反爬或登录绕过工具。它只导入用户已经能看到的内容。

### 常用命令

后端测试：

```powershell
cd backend
uv run pytest
```

前端 lint：

```powershell
cd frontend
npm run lint
```

前端构建：

```powershell
cd frontend
npm run build
```

### 文档

- `ESG_projectbrief.md`：产品愿景、范围、数据契约、风险和开放问题。
- `NEXTSTEPS.md`：实现路线和项目日志。
- `browser-extension/README.md`：扩展专用使用说明。

### 隐私与安全

ESG 是本地优先应用。本地数据库、截图、原始导入、密钥和生成产物默认不进入 git。

发布或分享 fork 前，请确认没有提交：

- `.env` 文件。
- SQLite 数据库。
- 截图。
- 原始岗位文本。
- API key 加密材料。
- 提供商 API key。

### 项目状态

ESG 目前是早期本地 MVP。当前实现已经覆盖从导入、抽取、岗位卡、模型配置、公司补全、岗位大类画像到交互式学习地图的主链路。下一项重要产品工作是让前端完整保留 LLM 学习地图的嵌套树结构，而不是压平成简单分支列表。

### License

暂未选择开源许可证。
