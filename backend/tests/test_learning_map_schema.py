from app.extraction.llm_schema import (
    LLMRoleCategoryProfile,
    build_role_learning_map_prompt,
    role_learning_map_json_schema,
)


def test_role_learning_map_schema_contains_unified_learning_map() -> None:
    schema = role_learning_map_json_schema()

    assert "learning_map" in schema["properties"]
    assert "skill_tree" not in schema["properties"]
    assert "knowledge_tree" not in schema["properties"]


def test_role_learning_map_profile_accepts_nested_nodes() -> None:
    profile = LLMRoleCategoryProfile.model_validate(
        {
            "role_category": "医学影像处理算法工程师",
            "summary": "聚焦三维医学影像处理、配准、重建和可视化。",
            "job_count": 2,
            "representative_titles": ["医学影像处理算法工程师"],
            "core_responsibilities": ["负责三维医学影像算法开发"],
            "common_requirements": ["熟悉 Python 和三维图像处理"],
            "high_frequency_skills": ["Python", "医学影像", "配准"],
            "bonus_signals": ["做过医学图像配准优先"],
            "learning_map": {
                "center_title": "医学影像处理算法工程师",
                "center_subtitle": "2 个岗位样本",
                "branches": [
                    {
                        "id": "core_skills",
                        "title": "核心技能",
                        "focus": "工具、算法与工程能力",
                        "source_fields": ["skills", "requirements"],
                        "evidence": ["必须具备 Python 编程能力"],
                        "nodes": [
                            {
                                "id": "skill.python",
                                "title": "Python 数据处理",
                                "node_type": "skill",
                                "level": "foundation",
                                "source_fields": ["skills", "requirements"],
                                "evidence": ["必须具备 Python 编程能力"],
                                "children": [
                                    {
                                        "id": "skill.python.batch",
                                        "title": "批量脚本与统计",
                                        "node_type": "project",
                                        "level": "intermediate",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "id": "domain_knowledge",
                        "title": "领域知识",
                        "focus": "医学图像、配准、三维重建",
                        "nodes": [
                            {
                                "id": "knowledge.registration",
                                "title": "医学图像配准",
                                "node_type": "knowledge",
                                "level": "intermediate",
                            }
                        ],
                    },
                ],
            },
            "field_sources": {"learning_map": "model_inference"},
            "evidence": {"learning_map": ["Python", "配准"]},
            "inference_notes": ["由岗位技能高频项聚合。"],
            "confidence": "medium",
        }
    )

    assert (
        profile.learning_map.branches[0].nodes[0].children[0].title
        == "批量脚本与统计"
    )


def test_role_learning_map_profile_accepts_empty_map_default() -> None:
    profile = LLMRoleCategoryProfile.model_validate(
        {
            "role_category": "嵌入式软件工程师",
            "summary": "聚焦嵌入式系统软件开发。",
            "job_count": 0,
        }
    )

    assert profile.learning_map.branches == []


def test_role_learning_map_prompt_includes_input_payload() -> None:
    prompt = build_role_learning_map_prompt(
        {
            "role_category": "嵌入式软件工程师",
            "job_cards": [{"title": "嵌入式软件工程师", "skills": ["C语言"]}],
        }
    )

    assert "嵌入式软件工程师" in prompt
    assert "learning_map" in prompt
    assert "skill_tree" not in prompt
    assert "knowledge_tree" not in prompt
