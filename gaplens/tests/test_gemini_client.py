"""Gemini client, fully offline: a stub client stands in for the SDK."""
import json
from types import SimpleNamespace

import pytest
from google.genai import errors

from core import gemini_client as gc
from core import suggestions
from core.gemini_client import GeminiError


class StubModels:
    def __init__(self, replies, listed=()):
        self.replies = list(replies)  # per call: text (str) or an exception to raise
        self.listed = list(listed)
        self.calls = []
        self.list_calls = 0

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return SimpleNamespace(text=reply)

    def list(self):
        self.list_calls += 1
        return iter(self.listed)


def stub_factory(replies, listed=()):
    models = StubModels(replies, listed)
    keys = []

    def factory(api_key):
        keys.append(api_key)
        return SimpleNamespace(models=models)

    return factory, models, keys


def not_found():
    return errors.ClientError(404, {"error": {"code": 404, "message": "model not found",
                                              "status": "NOT_FOUND"}})


def model(name, actions=("generateContent",)):
    return SimpleNamespace(name=f"models/{name}", supported_actions=list(actions))


PLAN = {"subject_code": " mca233 ", "subject_name": "Design and  Analysis of Algorithms",
        "units": [{"unit_no": 1, "title": "Basics", "topics": [" Asymptotic notation ", "", "Recurrences"]},
                  {"unit_no": "Unit 2", "title": "D&C", "topics": ["Merge sort", "asymptotic notation"]},
                  {"unit_no": 3, "title": "Empty", "topics": ["  "]}]}

REVIEW = {"strengths": ["Neat headings on every answer", "Labelled diagrams"],
          "improvements": [{"area": "Margins", "observation": "Text runs into the margin.",
                            "tip": "Leave a 2 cm margin."}],
          "summary": "Clear script; tidy the margins."}


# --- parse_json_response -------------------------------------------------------
def test_parse_json_response_reads_clean_json():
    assert gc.parse_json_response('{"a": [1, 2]}') == {"a": [1, 2]}


def test_parse_json_response_reads_fenced_json():
    text = 'Here you go:\n```json\n{"subject_code": "X1"}\n```\n'
    assert gc.parse_json_response(text) == {"subject_code": "X1"}


@pytest.mark.parametrize("text", ["not json at all", "```json\n{oops}\n```", "", None])
def test_parse_json_response_rejects_invalid_text(text):
    with pytest.raises(GeminiError):
        gc.parse_json_response(text)


# --- parse_course_plan -----------------------------------------------------------
def test_parse_course_plan_normalises_units_and_topics():
    factory, models, keys = stub_factory([json.dumps(PLAN)])
    out = gc.parse_course_plan(b"%PDF", "application/pdf", "k", client_factory=factory)
    assert out == {"subject_code": "MCA233", "subject_name": "Design and Analysis of Algorithms",
                   "units": [{"unit_no": 1, "title": "Basics",
                              "topics": ["Asymptotic notation", "Recurrences"]},
                             {"unit_no": 2, "title": "D&C", "topics": ["Merge sort"]}]}
    assert keys == ["k"] and len(models.calls) == 1
    call = models.calls[0]
    assert call["model"] == "gemini-flash-latest"
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].temperature <= 0.3
    part, prompt = call["contents"]
    assert part.inline_data.data == b"%PDF" and part.inline_data.mime_type == "application/pdf"
    assert "not invent" in prompt.lower()


@pytest.mark.parametrize("reply", [
    "[1, 2]", '{"units": "Unit 1"}', '{"units": ["topic"]}',
    '{"units": [{"unit_no": 1, "topics": "a, b"}]}', '{"units": [{"unit_no": 1, "topics": [{"x": 1}]}]}',
    '{"units": []}', '{"units": [{"unit_no": 1, "topics": ["", " "]}]}'])
def test_parse_course_plan_rejects_malformed_shapes(reply):
    factory, _m, _k = stub_factory([reply])
    with pytest.raises(GeminiError):
        gc.parse_course_plan(b"x", "image/png", "k", client_factory=factory)


@pytest.mark.parametrize("fn", [gc.parse_course_plan, gc.review_ese_script])
@pytest.mark.parametrize("key", [None, "", "   "])
def test_no_key_raises_before_any_client_is_created(fn, key):
    factory, models, keys = stub_factory(["{}"])
    with pytest.raises(GeminiError, match="key"):
        fn(b"x", "application/pdf", key, client_factory=factory)
    assert keys == [] and models.calls == []


# --- review_ese_script ----------------------------------------------------------------
def test_review_ese_script_formats_markdown_that_splits_into_two_cards():
    factory, models, _k = stub_factory([f"```json\n{json.dumps(REVIEW)}\n```"])
    text = gc.review_ese_script(b"\x89PNG", "image/png", "k", client_factory=factory)
    good, improve = suggestions.split_review(text)
    assert "Neat headings on every answer" in good and "Labelled diagrams" in good
    assert "**Margins.**" in improve and "Text runs into the margin." in improve
    assert "Leave a 2 cm margin." in improve and "Clear script; tidy the margins." in text
    prompt = models.calls[0]["contents"][1].lower()
    assert "presentation only" in prompt and "do not judge" in prompt


@pytest.mark.parametrize("reply", [
    '["a"]', '{"strengths": "good"}', '{"strengths": [], "improvements": ["tip"]}',
    '{"strengths": [], "improvements": [], "summary": ""}'])
def test_review_ese_script_rejects_malformed_shapes(reply):
    factory, _m, _k = stub_factory([reply])
    with pytest.raises(GeminiError):
        gc.review_ese_script(b"x", "application/pdf", "k", client_factory=factory)


# --- model choice and errors -------------------------------------------------------
def test_falls_back_to_next_flash_model_when_first_is_not_found():
    listed = [model("gemini-2.5-flash-lite"), model("gemini-3-flash-preview"),
              model("gemini-2.5-flash-image"), model("gemini-2.5-pro"),
              model("gemini-2.5-flash-tts"), model("gemini-2.5-flash"),
              model("gemini-2.0-flash", actions=("embedContent",)), model("text-embedding-004")]
    factory, models, _k = stub_factory([not_found(), json.dumps(REVIEW)], listed)
    gc.review_ese_script(b"x", "application/pdf", "k", client_factory=factory)
    assert [c["model"] for c in models.calls] == ["gemini-flash-latest", "gemini-2.5-flash"]


def test_tries_at_most_three_models():
    listed = [model("gemini-2.5-flash"), model("gemini-2.0-flash"), model("gemini-3-flash-preview")]
    factory, models, _k = stub_factory([not_found()] * 5, listed)
    with pytest.raises(GeminiError):
        gc.parse_course_plan(b"x", "application/pdf", "k", client_factory=factory)
    assert [c["model"] for c in models.calls] == [
        "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]


def test_non_404_error_raises_immediately_without_trying_more_models():
    quota = errors.ClientError(429, {"error": {"code": 429, "message": "quota",
                                               "status": "RESOURCE_EXHAUSTED"}})
    factory, models, _k = stub_factory([quota, "{}"], [model("gemini-2.5-flash")])
    with pytest.raises(GeminiError, match="quota"):
        gc.parse_course_plan(b"x", "application/pdf", "k", client_factory=factory)
    assert len(models.calls) == 1 and models.list_calls == 0


def test_configured_model_is_the_only_one_tried():
    factory, models, _k = stub_factory([not_found()], [model("gemini-2.5-flash")])
    with pytest.raises(GeminiError, match="my-model"):
        gc.parse_course_plan(b"x", "application/pdf", "k", model="my-model", client_factory=factory)
    assert [c["model"] for c in models.calls] == ["my-model"] and models.list_calls == 0


@pytest.mark.parametrize("exc", [TimeoutError("read timed out"), ConnectionError("boom"),
                                 errors.ServerError(503, {"error": {"code": 503, "status": "UNAVAILABLE"}}),
                                 RuntimeError("weird")])
def test_any_sdk_or_network_failure_becomes_gemini_error(exc):
    factory, _m, _k = stub_factory([exc])
    with pytest.raises(GeminiError) as info:
        gc.review_ese_script(b"x", "application/pdf", "k", client_factory=factory)
    assert 0 < len(str(info.value)) <= 200


def test_empty_response_raises():
    factory, _m, _k = stub_factory([None])
    with pytest.raises(GeminiError, match="empty"):
        gc.review_ese_script(b"x", "application/pdf", "k", client_factory=factory)


def test_module_level_factory_is_used_by_default(monkeypatch):
    factory, models, _k = stub_factory([json.dumps(PLAN)])
    monkeypatch.setattr(gc, "client_factory", factory)
    assert gc.parse_course_plan(b"x", "application/pdf", "k")["subject_code"] == "MCA233"
    assert len(models.calls) == 1


def test_guess_mime_from_extension():
    assert gc.guess_mime("plan.PDF", "") == "application/pdf"
    assert gc.guess_mime("scan.jpg", "application/octet-stream") == "image/jpeg"
    assert gc.guess_mime("scan.png", "image/png") == "image/png"
