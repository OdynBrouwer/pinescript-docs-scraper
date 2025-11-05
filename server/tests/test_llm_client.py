import pytest

from server import llm_client


class DummyChoice:
    def __init__(self, content):
        self.message = {"content": content}


class DummyResp:
    def __init__(self, text, usage=None):
        self.choices = [DummyChoice(text)]
        self.usage = usage


def test_choose_model_based_on_prompt():
    # Short prompt should pick primary model
    model = llm_client.choose_model(prompt_tokens=100)
    assert isinstance(model, str)


def test_create_chat_completion_monkeypatch(monkeypatch):
    # Replace the OpenAI client to avoid real network calls
    class FakeClient:
        class chat:
            @staticmethod
            def completions():
                raise RuntimeError("should not be called")

        def __init__(self):
            self.chat = self

        def completions(self):
            return self

        def create(self, *args, **kwargs):
            return DummyResp("Answer from fake model", usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})

    monkeypatch.setattr("server.embed_client.init_openai_client", lambda: FakeClient())

    context_docs = [{"source_filename": "f.md", "content": "example content"}]
    out = llm_client.create_chat_completion("How do I do X?", context_docs, temperature=0.0)
    assert "response" in out
    assert out["tokens"]["completion"] >= 0
    assert out["model"] is not None
    # Should include structured sources derived from context_docs
    assert "sources" in out
    assert isinstance(out["sources"], list)
    assert out["sources"][0]["filename"] == "f.md"
