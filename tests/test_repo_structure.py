import os


def test_core_files_and_views_exist():
    assert os.path.exists("app.py"), "Missing app.py"
    assert os.path.isdir("views"), "Missing views directory"
    for fname in ("start_page.py", "chat_page.py", "feedback_page.py"):
        assert os.path.exists(os.path.join("views", fname)), f"Missing views/{fname}"

