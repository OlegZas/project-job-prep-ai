from streamlit.testing.v1 import AppTest


def test_app_renders_without_exceptions():
    app = AppTest.from_file("app.py", default_timeout=20).run()

    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Ask My Documents",
        "Resume & Job Match",
        "Practice Interview",
        "Current Trends",
        "Project Metrics",
    ]
    assert len(app.dataframe) == 1
    assert len(app.dataframe[0].value) == 3
    assert set(app.dataframe[0].value["Status"]) == {"Ready"}
