from streamlit.testing.v1 import AppTest


def test_app_renders_without_exceptions():
    app = AppTest.from_file("app.py", default_timeout=20).run()

    assert not app.exception
    assert app.title[0].value.strip() == "DataPrep AI"
    assert [tab.label for tab in app.tabs] == [
        "Document Q&A",
        "Career Match",
        "Interview Lab",
        "Market Knowledge",
    ]
    assert len(app.dataframe) == 1
    assert len(app.dataframe[0].value) == 3
    assert set(app.dataframe[0].value["Status"]) == {"Indexed"}
