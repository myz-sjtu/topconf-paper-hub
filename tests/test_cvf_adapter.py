from app.adapters.cvf import CVFAdapter


def test_cvf_parser_rejects_workshop_paths() -> None:
    adapter = CVFAdapter()
    html = """
    <a href="/content/CVPR2025/html/Main_Paper_CVPR_2025_paper.html">Main Paper</a>
    <a href="/content/CVPR2025W/html/Workshop_Paper_CVPRW_2025_paper.html">Workshop Paper</a>
    """

    records = adapter._parse_listing(
        html,
        "https://openaccess.thecvf.com/CVPR2025?day=all",
        venue="CVPR",
        year=2025,
    )

    assert [record.title for record in records] == ["Main Paper"]
