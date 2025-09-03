import ui_components


class Dummy:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_styled_container_wraps_extras(monkeypatch):
    called = {}

    def fake_sc(key, css_styles):
        called["key"] = key
        called["css"] = css_styles
        return Dummy()

    monkeypatch.setattr(ui_components, "stylable_container", fake_sc)
    container = ui_components.styled_container("k", "css")
    assert called == {"key": "k", "css": "css"}
    assert isinstance(container, Dummy)


def test_chip_uses_styled_container(monkeypatch):
    sc_called = {}

    class Dummy:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    def fake_sc(key, css):
        sc_called["key"] = key
        sc_called["css"] = css
        return Dummy()

    markdown_called = {}

    def fake_markdown(text):
        markdown_called["text"] = text

    monkeypatch.setattr(ui_components, "styled_container", fake_sc)
    monkeypatch.setattr(ui_components.st, "markdown", fake_markdown)

    ui_components.chip("A", "1")

    assert sc_called["key"].startswith("chip-A")
    assert "A: **1**" == markdown_called["text"]


def test_external_badge_calls_badge(monkeypatch):
    called = {}

    def fake_badge(kind, name=None, url=None):
        called.update({"kind": kind, "name": name, "url": url})

    monkeypatch.setattr(ui_components, "_badge", fake_badge)

    ui_components.external_badge("github", name="repo")

    assert called == {"kind": "github", "name": "repo", "url": None}

