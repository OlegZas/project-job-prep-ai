from streamlit.testing.v1 import AppTest


def test_app_renders_without_exceptions():
    app = AppTest.from_file("app.py", default_timeout=20).run()

    assert not app.exception
    assert app.title[0].value.strip() == "DataPrep AI"
    assert len(app.tabs) == 2
