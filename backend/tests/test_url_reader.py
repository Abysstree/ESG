from app.services.url_reader import extract_visible_text_from_html


def test_extract_visible_text_from_html_ignores_scripts_and_styles() -> None:
    html = """
    <html>
      <head>
        <title>算法工程师招聘</title>
        <meta name="description" content="负责医学影像算法开发">
        <style>.hidden { display: none; }</style>
        <script>window.__DATA__ = "不要进入正文";</script>
      </head>
      <body>
        <h1>医学影像处理算法工程师</h1>
        <p>任职要求：熟悉 Python、SimpleITK、Open3D。</p>
      </body>
    </html>
    """

    text = extract_visible_text_from_html(html)

    assert "算法工程师招聘" in text
    assert "负责医学影像算法开发" in text
    assert "医学影像处理算法工程师" in text
    assert "不要进入正文" not in text


def test_extract_visible_text_from_html_reads_json_ld() -> None:
    html = """
    <html>
      <body>
        <script type="application/ld+json">
          {"title": "光学工程师", "description": "负责镜头评测和 Zemax 设计"}
        </script>
      </body>
    </html>
    """

    text = extract_visible_text_from_html(html)

    assert "光学工程师" in text
    assert "Zemax" in text
