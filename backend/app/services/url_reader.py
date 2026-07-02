from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx


MIN_EXTRACTED_TEXT_LENGTH = 80
REQUEST_TIMEOUT_SECONDS = 12
SUPPORTED_SCHEMES = {"http", "https"}


@dataclass(frozen=True)
class URLReadResult:
    text: str | None
    status: str
    error: str | None = None
    final_url: str | None = None

    @property
    def is_success(self) -> bool:
        return bool(self.text)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_stack: list[str] = []
        self._in_title = False
        self.title_parts: list[str] = []
        self.meta_parts: list[str] = []
        self.body_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if tag_name in {"script", "style", "noscript", "svg", "canvas"}:
            self._skip_stack.append(tag_name)
            return

        if tag_name == "title":
            self._in_title = True
            return

        if tag_name == "meta":
            attr_map = {key.lower(): value or "" for key, value in attrs}
            meta_name = attr_map.get("name", "").lower()
            meta_property = attr_map.get("property", "").lower()
            if meta_name in {"description", "keywords"} or meta_property in {
                "og:description",
                "twitter:description",
            }:
                self.meta_parts.append(attr_map.get("content", ""))

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if self._skip_stack and self._skip_stack[-1] == tag_name:
            self._skip_stack.pop()
            return

        if tag_name == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_stack:
            return

        cleaned = _normalize_text(data)
        if not cleaned:
            return

        if self._in_title:
            self.title_parts.append(cleaned)
        else:
            self.body_parts.append(cleaned)

    def text(self) -> str:
        parts = [*self.title_parts, *self.meta_parts, *self.body_parts]
        return _normalize_text("\n".join(parts))


def read_url_text(url: str) -> URLReadResult:
    parsed_url = urlparse(url.strip())
    if parsed_url.scheme not in SUPPORTED_SCHEMES or not parsed_url.netloc:
        return URLReadResult(
            text=None,
            status="url_fetch_unsupported",
            error="仅支持 http/https 链接。",
        )

    with httpx.Client(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "User-Agent": "EmploymentSkillsGuide/0.1",
        },
    ) as client:
        adapter_result = _read_with_platform_adapter(client, parsed_url, url)
        if adapter_result and adapter_result.is_success:
            return adapter_result

        generic_result = _read_generic_html(client, url)
        if generic_result.is_success:
            return generic_result

        return adapter_result or generic_result


def _read_with_platform_adapter(
    client: httpx.Client,
    parsed_url,
    source_url: str,
) -> URLReadResult | None:
    if _is_zhipin_weijd_job_url(parsed_url):
        return _read_zhipin_weijd_job(client, parsed_url, source_url)

    return None


def _is_zhipin_weijd_job_url(parsed_url) -> bool:
    return (
        parsed_url.netloc.endswith("zhipin.com")
        and "/mpa/html/weijd/weijd-job/" in parsed_url.path
    )


def _read_zhipin_weijd_job(
    client: httpx.Client,
    parsed_url,
    source_url: str,
) -> URLReadResult:
    sjid = parsed_url.path.rstrip("/").split("/")[-1]
    if not sjid:
        return URLReadResult(
            text=None,
            status="url_fetch_unsupported",
            error="无法从 BOSS 直聘微 JD 链接中识别职位 ID。",
        )

    query = parse_qs(parsed_url.query)
    api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/wapi/zpjob/wjd/job/{sjid}"
    try:
        response = client.get(
            api_url,
            params={
                "aid": _first_query_value(query, "aid", ""),
                "fromSource": _first_query_value(query, "fromSource", "-1"),
            },
            headers={
                "Accept": "application/json,text/plain,*/*",
                "Referer": source_url,
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return URLReadResult(
            text=None,
            status="url_fetch_failed",
            error=f"BOSS 直聘微 JD 接口请求失败：{exc}",
            final_url=api_url,
        )

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return URLReadResult(
            text=None,
            status="url_fetch_failed",
            error="BOSS 直聘微 JD 接口没有返回 JSON。",
            final_url=str(response.url),
        )

    code = payload.get("code")
    rescode = payload.get("rescode")
    if code == 37 or "环境存在异常" in str(payload.get("message", "")):
        return URLReadResult(
            text=None,
            status="url_fetch_protected",
            error="BOSS 直聘返回环境校验，ESG 不做登录或反爬绕过；请粘贴页面正文或截图作为备份。",
            final_url=str(response.url),
        )

    if rescode not in {None, 1} and code not in {None, 0}:
        return URLReadResult(
            text=None,
            status="url_fetch_failed",
            error=f"BOSS 直聘微 JD 接口返回异常：{payload.get('message') or payload.get('msg') or payload}",
            final_url=str(response.url),
        )

    data = payload.get("data") or payload.get("zpData") or payload
    text = _zhipin_payload_to_text(data)
    if not text or len(text) < MIN_EXTRACTED_TEXT_LENGTH:
        return URLReadResult(
            text=None,
            status="url_fetch_empty",
            error="BOSS 直聘微 JD 返回中没有足够的岗位正文。",
            final_url=str(response.url),
        )

    return URLReadResult(text=text, status="url_fetched", final_url=str(response.url))


def _read_generic_html(client: httpx.Client, url: str) -> URLReadResult:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return URLReadResult(
            text=None,
            status="url_fetch_failed",
            error=f"网页请求失败：{exc}",
        )

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return URLReadResult(
            text=None,
            status="url_fetch_unsupported",
            error=f"暂不支持读取该内容类型：{content_type or 'unknown'}。",
            final_url=str(response.url),
        )

    text = extract_visible_text_from_html(response.text)
    if len(text) < MIN_EXTRACTED_TEXT_LENGTH:
        return URLReadResult(
            text=None,
            status="url_fetch_empty",
            error="网页 HTML 中没有足够的可见正文，可能需要登录、JS 二次加载或平台限制。",
            final_url=str(response.url),
        )

    return URLReadResult(text=text, status="url_fetched", final_url=str(response.url))


def extract_visible_text_from_html(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)

    json_ld_texts: list[str] = []
    for match in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        json_text = match.group(1).strip()
        if not json_text:
            continue
        try:
            json_ld_texts.append(_json_to_text(json.loads(json_text)))
        except json.JSONDecodeError:
            continue

    return _normalize_text("\n".join([parser.text(), *json_ld_texts]))


def _zhipin_payload_to_text(data: Any) -> str:
    if not isinstance(data, dict):
        return ""

    job = _dict_value(data, "job")
    boss_info = _dict_value(data, "bossInfo")
    brand_info = _dict_value(data, "brandComInfo")

    lines = [
        _line("岗位名称", _first_string(job, ["jobName", "name", "title"])),
        _line("公司", _first_string(brand_info, ["brandName", "name"]) or _first_string(job, ["brandName"])),
        _line("融资阶段", _first_string(brand_info, ["stageName"]) or _first_string(job, ["stageName"])),
        _line("行业", _first_string(brand_info, ["industryName"]) or _first_string(job, ["industryName"])),
        _line("规模", _first_string(brand_info, ["scaleName"]) or _first_string(job, ["scaleName"])),
        _line("地点", _first_string(job, ["locationName", "cityName", "address"])),
        _line("经验", _first_string(job, ["experienceName"])),
        _line("学历", _first_string(job, ["degreeName"])),
        _line("薪资", _first_string(job, ["salaryDesc"])),
        _line("招聘者", _first_string(boss_info, ["name"])),
        _line("招聘者职位", _first_string(boss_info, ["title"])),
        _line("所属部门", _first_string(job, ["department"])),
        _line("汇报对象", _first_string(job, ["reportObject"])),
        _section("岗位职责/职位详情", _first_string(job, ["postDescription", "description"])),
        _section("岗位亮点", _first_string(job, ["performance"])),
    ]

    skills = _list_strings(job.get("skillLabels") if isinstance(job, dict) else None)
    if skills:
        lines.append("技能标签：" + "、".join(skills))

    return _normalize_text("\n".join(line for line in lines if line))


def _first_query_value(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    return values[0] if values else default


def _dict_value(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _first_string(data: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return _normalize_text(value)
        if isinstance(value, int | float):
            return str(value)
    return None


def _line(label: str, value: str | None) -> str:
    return f"{label}：{value}" if value else ""


def _section(label: str, value: str | None) -> str:
    return f"{label}\n{value}" if value else ""


def _list_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(_normalize_text(item))
        elif isinstance(item, dict):
            label = _first_string(item, ["label", "name", "value"])
            if label:
                result.append(label)
    return result


def _json_to_text(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join(_json_to_text(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(_json_to_text(item) for item in value)
    if isinstance(value, str):
        return value
    return ""


def _normalize_text(value: str) -> str:
    text = unescape(value)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n+ *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
