import ui_components


class Dummy:
    def markdown(self, text, unsafe_allow_html=False):
        self.calls.append((text, unsafe_allow_html))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_styled_container_injects_style(monkeypatch):
    dummy = Dummy()
    dummy.calls = []

    monkeypatch.setattr(ui_components.st, "container", lambda: dummy)

    with ui_components.styled_container("k", "{color:red;}"):
        pass

    assert ("<div style=\"color:red;\">", True) in dummy.calls
    assert ("</div>", True) in dummy.calls


def test_chip_renders_span(monkeypatch):
    captured = {}

    def fake_markdown(text, unsafe_allow_html=False):
        captured["text"] = text
        captured["unsafe"] = unsafe_allow_html

    monkeypatch.setattr(ui_components.st, "markdown", fake_markdown)

    ui_components.chip("A", "1")

    assert "A" in captured["text"] and "1" in captured["text"]
    assert captured["unsafe"]


def test_external_badge_renders_link(monkeypatch):
    captured = {}

    def fake_markdown(text, unsafe_allow_html=False):
        captured["text"] = text
        captured["unsafe"] = unsafe_allow_html

    monkeypatch.setattr(ui_components.st, "markdown", fake_markdown)

    ui_components.external_badge("github", url="https://example.com")

    assert "github" in captured["text"]
    assert "https://example.com" in captured["text"]
    assert captured["unsafe"]

