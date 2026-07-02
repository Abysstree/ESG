import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.extraction.mock_extractor import ExtractedJobCard


FieldSource = Literal[
    "original_posting",
    "external_search",
    "model_inference",
    "user_edit",
    "missing",
]
Confidence = Literal["low", "medium", "high"]
SalaryPeriod = Literal["monthly", "daily", "yearly"]
LearningNodeType = Literal["skill", "knowledge", "method", "tool", "project", "milestone"]
LearningLevel = Literal["foundation", "intermediate", "advanced", "portfolio"]


JOB_CARD_FIELD_NAMES = (
    "title",
    "company_name",
    "role_category",
    "salary_range",
    "salary_period",
    "base_location",
    "education_requirement",
    "experience_requirement",
    "responsibilities",
    "requirements",
    "bonus_points",
    "skills",
)


class LLMExtractedJobCard(BaseModel):
    title: str = Field(description="岗位名称。无法确定时填 未命名岗位。")
    company_name: str | None = Field(default=None, description="公司名称。")
    role_category: str = Field(description="岗位大类，例如 自动驾驶算法工程师、医学影像处理算法工程师。")
    salary_range: str | None = Field(default=None, description="薪资范围原样归一化，例如 10-15K、150-300元、15w。")
    salary_period: SalaryPeriod | None = Field(default=None, description="薪资周期：monthly、daily、yearly。")
    base_location: str | None = Field(
        default=None,
        description=(
            "岗位 base 的城市或城市+区摘要，不要填写楼栋、门牌、园区、办公室号。"
            "如果原文列出多个城市，保留完整城市列表，不要只取第一个；完整地址可放入 evidence.base_location。"
        ),
    )
    education_requirement: str | None = Field(
        default=None,
        description="学历要求，例如 本科、硕士、博士；只有原文明确出现学历要求时才填写。",
    )
    experience_requirement: str | None = Field(default=None, description="经验要求，例如 应届生、1-3年、3-5年。")
    responsibilities: list[str] = Field(default_factory=list, description="岗位职责，逐条列出。")
    requirements: list[str] = Field(default_factory=list, description="任职要求，逐条列出。")
    bonus_points: list[str] = Field(
        default_factory=list,
        description=(
            "加分项，逐条列出。原文没有明确加分项时，可以根据岗位职责和任职要求推测可能加分项，"
            "但必须把 field_sources.bonus_points 标为 model_inference。"
        ),
    )
    skills: list[str] = Field(default_factory=list, description="技能、工具、知识点标签。")
    field_sources: dict[str, FieldSource] = Field(
        default_factory=dict,
        description="每个字段的来源，必须覆盖主要岗位字段。",
    )
    evidence: dict[str, str | None] = Field(
        default_factory=dict,
        description="每个字段对应的原文证据短句；推测或缺失字段填 null。",
    )
    inference_notes: list[str] = Field(
        default_factory=list,
        description="模型推测、补全、不确定点的说明。",
    )
    confidence: Confidence = Field(description="整体抽取置信度。")

    @field_validator(
        "responsibilities",
        "requirements",
        "bonus_points",
        "skills",
        mode="before",
    )
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    def to_extracted_job_card(self) -> ExtractedJobCard:
        field_sources = {
            field_name: self.field_sources.get(
                field_name,
                "missing" if getattr(self, field_name, None) in (None, [], "") else "model_inference",
            )
            for field_name in JOB_CARD_FIELD_NAMES
        }
        if self.inference_notes:
            field_sources["inference_notes"] = "model_inference"

        return ExtractedJobCard(
            title=self.title or "未命名岗位",
            company_name=self.company_name,
            role_category=self.role_category or "待分类岗位",
            salary_range=self.salary_range,
            salary_period=self.salary_period,
            base_location=self.base_location,
            education_requirement=self.education_requirement,
            experience_requirement=self.experience_requirement,
            responsibilities=self.responsibilities,
            requirements=self.requirements,
            bonus_points=self.bonus_points,
            skills=self.skills,
            field_sources=field_sources,
            evidence=self.evidence,
            inference_notes=self.inference_notes,
            confidence=self.confidence,
        )


class LLMLearningMapNode(BaseModel):
    id: str = Field(description="Stable node id, such as skill.python or knowledge.linear_algebra.")
    title: str = Field(description="Node display title.")
    node_type: LearningNodeType = Field(description="Node category.")
    level: LearningLevel = Field(description="Learning stage for this node.")
    source_fields: list[str] = Field(
        default_factory=list,
        description="JobCard fields that support this node, such as skills or requirements.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Short evidence snippets from aggregated job cards.",
    )
    children: list["LLMLearningMapNode"] = Field(default_factory=list)


class LLMLearningMapBranch(BaseModel):
    id: str = Field(description="Stable branch id, such as core_skills or domain_knowledge.")
    title: str = Field(description="Branch display title.")
    focus: str = Field(
        description="Branch focus, such as 核心技能、领域知识、项目实践、面试作品 or 质控研究.",
    )
    source_fields: list[str] = Field(
        default_factory=list,
        description="Aggregated JobCard fields that support this branch.",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Short evidence snippets from aggregated job cards.",
    )
    nodes: list[LLMLearningMapNode] = Field(default_factory=list)


class LLMLearningMindMap(BaseModel):
    center_title: str = Field(default="", description="Central mind-map topic.")
    center_subtitle: str | None = Field(
        default=None,
        description="Optional short subtitle, such as sample count or role summary.",
    )
    branches: list[LLMLearningMapBranch] = Field(default_factory=list)


class LLMRoleCategoryProfile(BaseModel):
    role_category: str = Field(description="Target role category name.")
    summary: str = Field(description="Short category-level description.")
    job_count: int = Field(ge=0, description="Number of job cards aggregated.")
    representative_titles: list[str] = Field(default_factory=list)
    core_responsibilities: list[str] = Field(default_factory=list)
    common_requirements: list[str] = Field(default_factory=list)
    high_frequency_skills: list[str] = Field(default_factory=list)
    bonus_signals: list[str] = Field(default_factory=list)
    learning_map: LLMLearningMindMap = Field(default_factory=LLMLearningMindMap)
    field_sources: dict[str, FieldSource] = Field(default_factory=dict)
    evidence: dict[str, list[str]] = Field(default_factory=dict)
    inference_notes: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


COMPANY_PROFILE_FIELD_NAMES = (
    "company_name",
    "summary",
    "industry",
    "financing_stage",
    "scale",
    "headquarters",
    "official_website",
    "official_careers_url",
)


class LLMCompanyProfile(BaseModel):
    company_name: str = Field(description="公司全称或可确认的公司名称。")
    summary: str | None = Field(default=None, description="公司业务简介，无法确认时填 null。")
    industry: str | None = Field(default=None, description="所属行业，例如 医疗健康、汽车、半导体。")
    financing_stage: str | None = Field(
        default=None,
        description="融资或上市阶段，例如 未融资、A轮、已上市；无法确认时填 null。",
    )
    scale: str | None = Field(default=None, description="人员规模，例如 0-20人；无法确认时填 null。")
    headquarters: str | None = Field(default=None, description="总部或主要办公城市；无法确认时填 null。")
    official_website: str | None = Field(default=None, description="公司官网 URL；无法确认时填 null。")
    official_careers_url: str | None = Field(
        default=None,
        description="官方招聘页或官方职位页 URL；无法确认时填 null。",
    )
    source_urls: list[str] = Field(
        default_factory=list,
        description="支持上述信息的来源 URL，优先官网、官方招聘页、官方公众号或权威公开页面。",
    )
    field_sources: dict[str, FieldSource] = Field(default_factory=dict)
    evidence: dict[str, str | None] = Field(
        default_factory=dict,
        description="每个字段对应的证据短句或来源说明；没有证据填 null。",
    )
    inference_notes: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


def job_extraction_json_schema() -> dict[str, Any]:
    return LLMExtractedJobCard.model_json_schema()


def role_learning_map_json_schema() -> dict[str, Any]:
    return LLMRoleCategoryProfile.model_json_schema()


def company_profile_json_schema() -> dict[str, Any]:
    return LLMCompanyProfile.model_json_schema()


def build_role_learning_map_prompt(role_payload: dict[str, Any]) -> str:
    schema_json = json.dumps(role_learning_map_json_schema(), ensure_ascii=False, indent=2)
    role_json = json.dumps(role_payload, ensure_ascii=False, indent=2)
    return (
        "请基于同一岗位大类下的多张岗位卡，聚合生成岗位大类画像和一张学习地图。"
        "必须严格返回 JSON，不要输出 Markdown。\n"
        "learning_map 是单一思维导图：center_title 是中心主题，branches 是主分支。"
        "主分支可覆盖核心技能、领域知识、工具链、项目实践、质控研究、面试作品等方向；"
        "每个分支的 nodes 可以继续用 children 表达子主题。\n"
        "所有概括和推断必须在 field_sources 标为 model_inference，并在 inference_notes 说明；"
        "能被岗位卡原文字段支持的内容要写入 evidence。\n"
        "JSON Schema 如下：\n"
        f"{schema_json}\n\n"
        "岗位大类输入：\n"
        f"{role_json}"
    )


def build_company_profile_prompt(company_payload: dict[str, Any]) -> str:
    schema_json = json.dumps(company_profile_json_schema(), ensure_ascii=False, indent=2)
    company_json = json.dumps(company_payload, ensure_ascii=False, indent=2)
    fields = "、".join(COMPANY_PROFILE_FIELD_NAMES)
    return (
        "请为 EmploymentSkillsGuide 补全公司画像，输出严格 JSON，不要输出 Markdown，不要解释。\n"
        "只填写能从输入、可靠公开事实或明确来源判断的信息。无法确认的信息填 null，并在 field_sources 标为 missing。\n"
        "如果你根据常识或模型记忆推测，必须在 field_sources 标为 model_inference，并在 inference_notes 说明；"
        "不要编造官网、招聘页、融资阶段或规模。\n"
        "如果能给出来源 URL，请放入 source_urls；没有可靠 URL 就留空数组。\n"
        f"field_sources 必须至少覆盖这些字段：{fields}。\n"
        "公司画像 JSON Schema 如下：\n"
        f"{schema_json}\n\n"
        "公司输入：\n"
        f"{company_json}"
    )


def build_job_extraction_prompt(raw_text: str) -> str:
    schema_json = json.dumps(job_extraction_json_schema(), ensure_ascii=False, indent=2)
    fields = "、".join(JOB_CARD_FIELD_NAMES)
    return (
        "请把下面的招聘信息抽取成严格 JSON，不要输出 Markdown，不要输出解释。\n"
        "所有推测、概括、补全必须在 field_sources 标为 model_inference，"
        "并在 inference_notes 说明。原文明确出现的信息标为 original_posting；"
        "无法确定的信息填 null 或空数组，并标为 missing。\n"
        "硬事实字段不能推测：salary_range、base_location、education_requirement、"
        "experience_requirement、responsibilities、requirements 必须来自原文，"
        "否则填 null 或空数组并标为 missing。\n"
        "允许模型分析/推测的字段：role_category、bonus_points、skills；"
        "其中 bonus_points、skills 若含推测内容，必须标为 model_inference 并说明。\n"
        f"field_sources 必须至少覆盖这些字段：{fields}。\n"
        "salary_period 只能是 monthly、daily、yearly 或 null。"
        "salary_period 可由明确薪资格式推断：10-15K 这类通常是 monthly，"
        "150-300元/天是 daily，15w/年或 15w 是 yearly；没有薪资依据时填 null。\n"
        "base_location 只写城市或城市+区，例如 南京 或 南京建邺区；不要把楼栋、门牌、园区、办公室号写入 base_location。"
        "如果包含多个城市，必须保留完整城市列表，例如 深圳/上海/北京，不要只抽第一个城市；"
        "完整地址请放入 evidence.base_location。\n"
        "education_requirement 只有在原文明确出现 本科、硕士、博士、大专、不限 等学历词时才填写；"
        "专业要求、应届生、在校生不能被当作学历要求。\n"
        "bonus_points 如果原文明确列出加分项，按原文抽取并标为 original_posting；"
        "如果原文没有加分项，请基于岗位职责、任职要求、技能工具推测 3-5 条可能加分项，"
        "field_sources.bonus_points 标为 model_inference，evidence.bonus_points 填 null，"
        "并在 inference_notes 中说明“加分项为模型推测”。\n"
        "JSON Schema 如下：\n"
        f"{schema_json}\n\n"
        "招聘原文：\n"
        f"{raw_text}"
    )


def parse_llm_extracted_job_card(content: str | dict[str, Any]) -> LLMExtractedJobCard:
    payload = content if isinstance(content, dict) else _loads_json_object(content)
    try:
        return LLMExtractedJobCard.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(f"LLM extraction response did not match schema: {exc}") from exc


def parse_llm_role_category_profile(content: str | dict[str, Any]) -> LLMRoleCategoryProfile:
    payload = content if isinstance(content, dict) else _loads_json_object(content)
    try:
        return LLMRoleCategoryProfile.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(f"LLM role profile response did not match schema: {exc}") from exc


def parse_llm_company_profile(content: str | dict[str, Any]) -> LLMCompanyProfile:
    payload = content if isinstance(content, dict) else _loads_json_object(content)
    try:
        return LLMCompanyProfile.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(f"LLM company profile response did not match schema: {exc}") from exc


def _loads_json_object(content: str) -> dict[str, Any]:
    cleaned = _strip_markdown_fence(content.strip())
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise RuntimeError("LLM extraction response did not contain a JSON object.")
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise RuntimeError("LLM extraction response must be a JSON object.")
    return parsed


def _strip_markdown_fence(content: str) -> str:
    fenced_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", content, flags=re.DOTALL)
    return fenced_match.group(1).strip() if fenced_match else content
