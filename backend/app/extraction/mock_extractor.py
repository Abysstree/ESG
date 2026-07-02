from dataclasses import dataclass, field
import re


@dataclass
class ExtractedJobCard:
    title: str
    company_name: str | None
    role_category: str
    salary_range: str | None = None
    salary_period: str | None = None
    base_location: str | None = None
    education_requirement: str | None = None
    experience_requirement: str | None = None
    responsibilities: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    bonus_points: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    field_sources: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, str | None] = field(default_factory=dict)
    inference_notes: list[str] = field(default_factory=list)
    confidence: str = "low"


SECTION_ALIASES = {
    "responsibilities": (
        "岗位职责",
        "工作职责",
        "职位职责",
        "职责描述",
        "工作内容",
        "岗位描述",
        "职位描述",
    ),
    "requirements": (
        "任职要求",
        "岗位要求",
        "职位要求",
        "任职资格",
        "任职条件",
        "能力要求",
        "基本要求",
    ),
    "bonus_points": (
        "加分项",
        "优先条件",
        "优先考虑",
        "加分条件",
        "bonus",
        "nice to have",
    ),
    "traits": (
        "我们希望你具备的特质",
        "希望你具备的特质",
        "个人特质",
        "素质要求",
    ),
}

SKILL_KEYWORDS = (
    "Python",
    "C++",
    "C语言",
    "MATLAB",
    "PyTorch",
    "TensorFlow",
    "OpenCV",
    "Linux",
    "ROS",
    "CUDA",
    "Git",
    "SQL",
    "Docker",
    "MCU",
    "FreeRTOS",
    "RTOS",
    "SLAM",
    "深度学习",
    "机器学习",
    "图像处理",
    "计算机视觉",
    "目标检测",
    "语义分割",
    "医学影像",
    "传感器融合",
    "自动驾驶",
    "光学设计",
    "Zemax",
    "Rust",
    "CT",
    "CTA",
    "MRI",
    "4D-CT",
    "4D-CTA",
    "VTK",
    "ITK",
    "SimpleITK",
    "Open3D",
    "PyVista",
    "CGAL",
    "scikit-image",
    "mesh",
    "STL",
    "点云",
    "三维重建",
    "刚性配准",
    "非刚性配准",
    "ICP",
    "B-spline",
    "Demons",
    "光流",
    "中心线",
)


def extract_job_card(raw_text: str) -> ExtractedJobCard:
    lines = _normalize_lines(raw_text)
    sections = _collect_sections(lines)
    plain_text = "\n".join(lines)

    responsibilities = sections["responsibilities"] or _guess_responsibilities(lines)
    requirements = sections["requirements"] or _guess_requirements(lines)
    bonus_points = sections["bonus_points"] or _guess_bonus_points(lines)

    title = _extract_title(lines)
    company_name = _extract_company_name(lines)
    role_category = _infer_role_category(plain_text)
    salary_range, salary_period = _extract_salary(plain_text)
    base_location = _extract_base_location(lines)
    education_requirement = _extract_education_requirement(plain_text)
    experience_requirement = _extract_experience_requirement(plain_text)
    skills = _extract_skills(plain_text)
    confidence = "medium" if any(sections.values()) else "low"

    return ExtractedJobCard(
        title=title,
        company_name=company_name,
        role_category=role_category,
        salary_range=salary_range,
        salary_period=salary_period,
        base_location=base_location,
        education_requirement=education_requirement,
        experience_requirement=experience_requirement,
        responsibilities=responsibilities,
        requirements=requirements,
        bonus_points=bonus_points,
        skills=skills,
        confidence=confidence,
        field_sources={
            "title": "original_posting" if title != "未命名岗位" else "model_inference",
            "company_name": "original_posting" if company_name else "missing",
            "role_category": "model_inference",
            "salary_range": "original_posting" if salary_range else "missing",
            "salary_period": "model_inference" if salary_range else "missing",
            "base_location": "original_posting" if base_location else "missing",
            "education_requirement": "original_posting" if education_requirement else "missing",
            "experience_requirement": "original_posting" if experience_requirement else "missing",
            "responsibilities": "original_posting",
            "requirements": "original_posting",
            "bonus_points": "original_posting" if bonus_points else "missing",
            "skills": "model_inference",
        },
    )


def _normalize_lines(raw_text: str) -> list[str]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in normalized.split("\n"):
        cleaned = re.sub(r"^[\s\-*•·]+", "", line.strip())
        cleaned = re.sub(r"^\d+\s*[.、）)]\s*", "", cleaned)
        if cleaned:
            lines.append(cleaned)
    return lines


def _collect_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "responsibilities": [],
        "requirements": [],
        "bonus_points": [],
        "traits": [],
    }
    current_section: str | None = None

    for line in lines:
        section_name = _match_section_header(line)
        if section_name:
            current_section = section_name
            remainder = _strip_header(line, SECTION_ALIASES[section_name])
            if remainder:
                sections[current_section].append(remainder)
            continue

        if current_section:
            sections[current_section].append(line)

    return {key: _dedupe(_filter_section_items(key, values)) for key, values in sections.items()}


def _match_section_header(line: str) -> str | None:
    lower_line = line.lower()
    for section_name, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if lower_line.startswith(alias.lower()):
                return section_name
    return None


def _strip_header(line: str, aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        pattern = rf"^{re.escape(alias)}\s*[:：\-]?\s*"
        stripped = re.sub(pattern, "", line, flags=re.IGNORECASE)
        if stripped != line:
            return stripped.strip()
    return ""


def _extract_title(lines: list[str]) -> str:
    patterns = (
        r"^(?:岗位名称|职位名称|招聘岗位|岗位|职位)\s*[:：]\s*(.+)$",
        r"^(.{2,40}(?:工程师|算法|开发|研究员|实习生))$",
    )
    for line in lines[:10]:
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1).strip()
    return lines[0] if lines else "未命名岗位"


def _extract_company_name(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        match = re.search(r"(?:公司名称|公司|企业)\s*[:：]\s*(.+)", line)
        if match:
            return _clean_company_name(match.group(1))

        if line == "所在公司" and index + 1 < len(lines):
            return _clean_company_name(lines[index + 1])

    title = _extract_title(lines)
    for line in lines[:8]:
        if line == title or _looks_like_job_meta(line):
            continue
        if _looks_like_company_name(line):
            return _clean_company_name(line)
    return None


def _clean_company_name(value: str) -> str:
    return re.split(r"\s+|·", value.strip())[0]


def _looks_like_company_name(line: str) -> bool:
    if len(line) > 40:
        return False
    if any(keyword in line for keyword in ("融资", "上市", "人", "公司", "科技", "技术", "云图")):
        return not any(keyword in line for keyword in ("岗位", "职责", "要求", "职位"))
    return False


def _looks_like_job_meta(line: str) -> bool:
    return bool(
        re.search(r"\d+-\d+K|本科|硕士|博士|年|南京|上海|北京|深圳|广州|杭州|职位详情", line)
    )


def _extract_salary(text: str) -> tuple[str | None, str | None]:
    compact_text = text.replace("－", "-").replace("—", "-").replace("～", "-")
    patterns = (
        r"(?P<salary>\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*[kK万wW])",
        r"(?P<salary>\d+(?:\.\d+)?\s*[kK万wW])",
        r"(?P<salary>\d+\s*-\s*\d+\s*元(?:/天|/日|每天|每日)?)",
        r"(?P<salary>\d+\s*元(?:/天|/日|每天|每日)?)",
    )

    for pattern in patterns:
        match = re.search(pattern, compact_text)
        if not match:
            continue

        salary = re.sub(r"\s+", "", match.group("salary"))
        return salary, _infer_salary_period(salary)

    return None, None


def _infer_salary_period(salary: str) -> str:
    lower_salary = salary.lower()
    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", lower_salary)]
    max_number = max(numbers) if numbers else 0

    if any(token in lower_salary for token in ("天", "日")):
        return "daily"
    if any(token in lower_salary for token in ("w", "万")):
        return "yearly"
    if "元" in lower_salary and max_number <= 1000:
        return "daily"
    return "monthly"


def _extract_base_location(lines: list[str]) -> str | None:
    city_pattern = r"(北京|上海|广州|深圳|杭州|南京|苏州|成都|武汉|西安|合肥|长沙|重庆|天津|宁波|厦门|青岛|郑州|无锡|常州|东莞|佛山)"
    for line in lines[:12]:
        if "·" in line:
            match = re.search(city_pattern, line)
            if match:
                return match.group(1)

    for index, line in enumerate(lines):
        if line.startswith("工作地点") and index + 1 < len(lines):
            match = re.search(city_pattern, lines[index + 1])
            return match.group(1) if match else lines[index + 1]

    for line in lines:
        match = re.search(city_pattern, line)
        if match and ("区" in line or "市" in line):
            return match.group(1)

    return None


def _extract_education_requirement(text: str) -> str | None:
    for education in ("博士", "硕士", "本科", "大专", "不限"):
        if education in text:
            return education
    return None


def _extract_experience_requirement(text: str) -> str | None:
    candidates = (
        "在校生",
        "应届生",
        "1年以内",
        "1-3年",
        "3-5年",
        "5-10年",
        "10年以上",
        "经验不限",
    )
    normalized_text = text.replace("－", "-").replace("—", "-")
    for candidate in candidates:
        if candidate in normalized_text:
            return candidate

    match = re.search(r"\d+\s*-\s*\d+\s*年", normalized_text)
    if match:
        return re.sub(r"\s+", "", match.group(0))
    return None


def _guess_responsibilities(lines: list[str]) -> list[str]:
    markers = ("负责", "参与", "完成", "设计", "开发", "搭建", "优化", "维护")
    return _dedupe([line for line in lines if line.startswith(markers)])[:8]


def _guess_requirements(lines: list[str]) -> list[str]:
    markers = ("熟悉", "掌握", "具备", "了解", "要求", "本科", "硕士", "博士", "经验")
    return _dedupe([line for line in lines if line.startswith(markers) or "经验" in line])[:10]


def _guess_bonus_points(lines: list[str]) -> list[str]:
    markers = ("优先", "加分", "有相关", "具备相关")
    return _dedupe([line for line in lines if line.startswith(markers) or "优先" in line])[:6]


def _infer_role_category(text: str) -> str:
    category_keywords = (
        ("自动驾驶算法工程师", ("自动驾驶", "感知", "规划控制", "SLAM", "BEV", "传感器融合")),
        ("医学影像处理算法工程师", ("医学影像", "CT", "MRI", "影像分割", "病灶", "医疗图像")),
        ("嵌入式软件工程师", ("嵌入式", "MCU", "单片机", "RTOS", "驱动开发", "ARM")),
        ("光学工程师", ("光学", "Zemax", "TracePro", "镜头", "光路", "成像")),
    )
    for category, keywords in category_keywords:
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return category
    return "待分类岗位"


def _extract_skills(text: str) -> list[str]:
    lower_text = text.lower()
    return [skill for skill in SKILL_KEYWORDS if skill.lower() in lower_text]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = value.strip(" ：:;；")
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _filter_section_items(section_name: str, values: list[str]) -> list[str]:
    stop_headers = {
        "responsibilities": ("任职要求", "岗位要求", "职位要求", "加分项", "工作地点", "所在公司"),
        "requirements": ("加分项", "工作地点", "所在公司", "我们希望你具备的特质"),
        "bonus_points": ("工作地点", "所在公司", "我们希望你具备的特质"),
        "traits": ("工作地点", "所在公司"),
    }
    filtered = []
    for value in values:
        if any(value.startswith(header) for header in stop_headers.get(section_name, ())):
            break
        filtered.append(value)
    return filtered
