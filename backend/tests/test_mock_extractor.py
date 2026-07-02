from app.extraction.mock_extractor import extract_job_card


def test_mock_extractor_extracts_sections() -> None:
    result = extract_job_card(
        """
        公司名称：示例科技
        岗位名称：自动驾驶感知算法工程师
        岗位职责：
        1. 负责自动驾驶感知算法开发
        2. 优化目标检测模型
        任职要求：
        1. 熟悉 Python 和 PyTorch
        2. 掌握计算机视觉和深度学习
        加分项：
        1. 有 ROS 或 CUDA 经验优先
        """
    )

    assert result.company_name == "示例科技"
    assert result.title == "自动驾驶感知算法工程师"
    assert result.role_category == "自动驾驶算法工程师"
    assert "负责自动驾驶感知算法开发" in result.responsibilities
    assert "Python" in result.skills
    assert result.confidence == "medium"


def test_mock_extractor_handles_boss_style_company_block() -> None:
    result = extract_job_card(
        """
        医学影像处理算法工程师

        芯动云图 未融资
        南京·1-3年·硕士
        10-15K
        职位详情

        岗位职责
        1.负责三维及动态医学影像数据的处理、分析和算法开发；
        2.参与 CT、CTA、MRI 等医学影像的多相位数据整理、配准和时序一致性分析；
        任职要求
        硬性要求，不符合请勿投递
        1.硕士及以上学历，计算机、图形学、人工智能、生物医学工程、医学影像、数学、自动化、力学等相关专业；
        2.必须有三维数据处理经验，包括三维医学影像、点云、mesh、STL、VTK、Open3D、三维重建、中心线、配准、形变场、位移场等至少一种；
        加分项
        1.做过 4D-CT/4D-CTA、心脏 CT、cine MRI、PC-MRI 等动态医学影像；
        我们希望你具备的特质
        1.对三维空间结构敏感，能理解医学影像中的空间关系；
        工作地点
        南京建邺区阿里巴巴江苏总部T5栋905-2、906

        所在公司

        南京芯动云图技术有限公司
        未融资·0-20人·医疗健康
        """
    )

    assert result.company_name == "南京芯动云图技术有限公司"
    assert result.title == "医学影像处理算法工程师"
    assert result.role_category == "医学影像处理算法工程师"
    assert result.salary_range == "10-15K"
    assert result.salary_period == "monthly"
    assert result.base_location == "南京"
    assert result.education_requirement == "硕士"
    assert result.experience_requirement == "1-3年"
    assert "工作地点" not in result.bonus_points
    assert "VTK" in result.skills


def test_mock_extractor_infers_salary_periods() -> None:
    daily = extract_job_card("医学影像算法实习生\n150-300元/天\n在校生\n本科")
    yearly = extract_job_card("算法专家\n15w\n5-10年\n硕士")

    assert daily.salary_range == "150-300元/天"
    assert daily.salary_period == "daily"
    assert daily.experience_requirement == "在校生"
    assert yearly.salary_range == "15w"
    assert yearly.salary_period == "yearly"
    assert yearly.experience_requirement == "5-10年"
