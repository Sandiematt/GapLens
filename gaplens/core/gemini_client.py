"""Optional Gemini features: course-plan parsing and ESE presentation review.

Every failure raises ``GeminiError`` with a short, readable message, so pages can
show it and fall back to the manual path. No Streamlit imports here.

Testability: the SDK client comes from ``client_factory(api_key)``. Tests replace the
module-level ``client_factory`` (or pass ``client_factory=``) with a stub, so no test
touches the network or needs a key. No client is created before a key is checked.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Iterator

import config


class GeminiError(Exception):
    """The single error type for every Gemini failure."""


# --- client -----------------------------------------------------------------------
def _sdk():
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:  # ImportError, or a broken install
        raise GeminiError("The google-genai package is not installed, so Gemini is unavailable.") from exc
    return genai, types


def _default_client_factory(api_key: str):
    genai, types = _sdk()
    try:
        return genai.Client(api_key=api_key,
                            http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_S * 1000))
    except Exception as exc:
        raise GeminiError(f"Could not start the Gemini client: {_short(exc)}") from exc


client_factory: Callable[[str], Any] = _default_client_factory


# --- pure helpers -------------------------------------------------------------------
_FENCE = re.compile(r"```(?:json|JSON)?\s*(.*?)\s*```", re.DOTALL)

_MIME_BY_EXT = {".pdf": "application/pdf", ".png": "image/png",
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def guess_mime(filename: str, given: str | None = None) -> str:
    """The upload's MIME type, or one guessed from the file extension."""
    if given and given != "application/octet-stream":
        return given
    return _MIME_BY_EXT.get(Path(filename or "").suffix.lower(), given or "application/octet-stream")


def parse_json_response(text: str | None) -> Any:
    """Read clean JSON, or JSON inside a ```json code block. Anything else raises."""
    raw = (text or "").strip()
    if not raw:
        raise GeminiError("Gemini returned an empty response.")
    candidates = [raw] + [m.group(1) for m in _FENCE.finditer(raw)]
    for chunk in candidates:
        try:
            return json.loads(chunk)
        except (ValueError, TypeError):
            continue
    raise GeminiError("Gemini's reply was not valid JSON. Try again, or use the manual option.")


def _short(exc: BaseException, limit: int = 160) -> str:
    msg = " ".join(str(getattr(exc, "message", None) or exc).split())
    return msg if len(msg) <= limit else msg[: limit - 1] + "…"


def _is_not_found(exc: BaseException) -> bool:
    return getattr(exc, "code", None) == 404 or "NOT_FOUND" in str(getattr(exc, "status", "") or exc)


def _friendly(exc: BaseException) -> GeminiError:
    """Map any SDK or network error to a short GeminiError."""
    if isinstance(exc, GeminiError):
        return exc
    code = getattr(exc, "code", None)
    text = f'{getattr(exc, "status", "")} {exc}'.upper()
    name = type(exc).__name__.lower()
    if isinstance(exc, TimeoutError) or "timeout" in name or "TIMED OUT" in text or "DEADLINE" in text:
        return GeminiError(f"Gemini did not answer within {config.GEMINI_TIMEOUT_S} seconds. Try again later.")
    if code == 429 or "RESOURCE_EXHAUSTED" in text or "QUOTA" in text:
        return GeminiError("The Gemini free-tier quota is used up for now. Try again later.")
    if code in (401, 403) or "API_KEY_INVALID" in text or "API KEY NOT VALID" in text \
            or "PERMISSION_DENIED" in text:
        return GeminiError("Gemini rejected the API key. Check GEMINI_API_KEY in secrets.toml.")
    if isinstance(code, int) and code >= 500:
        return GeminiError("Gemini is unavailable right now (server error). Try again later.")
    if _is_not_found(exc):
        return GeminiError("No usable Gemini Flash model was found for this key. "
                           "Set GEMINI_MODEL to a model your key can use.")
    if "connect" in name or "network" in name or "CONNECTION" in text:
        return GeminiError("Could not reach Gemini. Check the internet connection.")
    return GeminiError(f"Gemini request failed: {_short(exc)}")


# --- model choice ------------------------------------------------------------------
_EXCLUDE = ("lite", "image", "tts", "live", "audio", "embedding")


def _listed_flash_models(client) -> list[str]:
    """Flash-tier models that support generateContent; non-preview before preview."""
    try:
        listed = list(client.models.list())
    except Exception as exc:
        raise _friendly(exc) from exc
    stable, preview = [], []
    for m in listed:
        name = str(getattr(m, "name", "") or "").removeprefix("models/")
        low = name.lower()
        actions = getattr(m, "supported_actions", None) or []
        if "flash" not in low or any(x in low for x in _EXCLUDE):
            continue
        if actions and "generateContent" not in actions:
            continue
        (preview if ("preview" in low or "exp" in low) else stable).append(name)
    return stable + preview


def _candidates(client, model: str | None) -> Iterator[str]:
    """The configured model only, else the default then listed Flash models (lazily)."""
    if model:
        yield model
        return
    seen = {config.GEMINI_DEFAULT_MODEL}
    yield config.GEMINI_DEFAULT_MODEL
    for name in _listed_flash_models(client):  # listed only if the default was not found
        if name not in seen:
            seen.add(name)
            yield name


def _generate(data: bytes, mime: str, prompt: str, api_key: str | None, model: str | None,
              factory: Callable[[str], Any] | None) -> Any:
    """Send one file plus prompt; return the parsed JSON reply."""
    if not (api_key or "").strip():
        raise GeminiError("No Gemini API key is configured. Add GEMINI_API_KEY to "
                          ".streamlit/secrets.toml, or use the manual option.")
    if not data:
        raise GeminiError("The file is empty.")
    _genai, types = _sdk()
    client = (factory or client_factory)(api_key.strip())
    try:
        cfg = types.GenerateContentConfig(response_mime_type="application/json",
                                          temperature=config.GEMINI_TEMPERATURE)
        contents = [types.Part.from_bytes(data=data, mime_type=mime), prompt]
    except Exception as exc:
        raise _friendly(exc) from exc
    tried = 0
    last: BaseException | None = None
    for name in _candidates(client, model):
        if tried >= config.GEMINI_MAX_CANDIDATES:
            break
        tried += 1
        try:
            response = client.models.generate_content(model=name, contents=contents, config=cfg)
        except Exception as exc:
            if _is_not_found(exc):
                if model:
                    raise GeminiError(f'The Gemini model "{model}" was not found for this key. '
                                      "Check GEMINI_MODEL.") from exc
                last = exc
                continue
            raise _friendly(exc) from exc
        try:
            text = response.text
        except Exception as exc:
            raise GeminiError("Gemini returned no usable text (the reply may have been blocked).") from exc
        return parse_json_response(text)
    if last is not None:
        raise _friendly(last) from last
    raise GeminiError("No usable Gemini Flash model was found for this key. "
                      "Set GEMINI_MODEL to a model your key can use.")


# --- course plan -------------------------------------------------------------------
COURSE_PLAN_PROMPT = """You read a university course plan (syllabus) and extract its structure.
Return ONLY JSON of this shape:
{"subject_code": "string", "subject_name": "string",
 "units": [{"unit_no": 1, "title": "string", "topics": ["short topic", "..."]}]}
Rules:
- Copy only what the document says. Do not invent, expand or guess any content.
- If the code or name is not in the document, use an empty string.
- Topics are short (2 to 8 words), one idea each, in document order, without unit numbers.
- Leave out hours, outcomes, references, textbooks, assessment and lab lists.
- unit_no is the unit's number as an integer."""


def _text_field(value: Any, what: str) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return " ".join(str(value).split())
    raise GeminiError(f"Gemini returned an unexpected {what}.")


def _unit_no(value: Any, position: int) -> int:
    if isinstance(value, bool):
        raise GeminiError("Gemini returned an unexpected unit number.")
    if isinstance(value, (int, float)) and value >= 1:
        return int(value)
    if isinstance(value, str):
        m = re.search(r"\d+", value)
        if m and int(m.group()) >= 1:
            return int(m.group())
    if value is None or isinstance(value, str):
        return position
    raise GeminiError("Gemini returned an unexpected unit number.")


def normalise_course_plan(data: Any) -> dict:
    """Validate and clean Gemini's course-plan JSON.

    Topics are stripped; empty ones and repeats (anywhere in the subject) are dropped,
    and so are units left with no topics. A malformed shape raises GeminiError.
    """
    if not isinstance(data, dict):
        raise GeminiError("Gemini's reply did not have the expected course-plan shape.")
    units_in = data.get("units")
    if not isinstance(units_in, list):
        raise GeminiError("Gemini's reply had no list of units.")
    seen: set[str] = set()
    units = []
    for i, u in enumerate(units_in, 1):
        if not isinstance(u, dict):
            raise GeminiError("Gemini's reply had a unit in an unexpected shape.")
        topics_in = u.get("topics") or []
        if not isinstance(topics_in, list):
            raise GeminiError("Gemini's reply had topics in an unexpected shape.")
        topics = []
        for t in topics_in:
            title = _text_field(t, "topic")
            if title and title.casefold() not in seen:
                seen.add(title.casefold())
                topics.append(title)
        if topics:
            units.append({"unit_no": _unit_no(u.get("unit_no"), i),
                          "title": _text_field(u.get("title"), "unit title"), "topics": topics})
    if not units:
        raise GeminiError("Gemini found no units or topics in this file. Use the manual option.")
    return {"subject_code": _text_field(data.get("subject_code"), "subject code").upper(),
            "subject_name": _text_field(data.get("subject_name"), "subject name"),
            "units": units}


def parse_course_plan(data: bytes, mime: str, api_key: str | None, model: str | None = None,
                      client_factory: Callable[[str], Any] | None = None) -> dict:
    """{subject_code, subject_name, units: [{unit_no, title, topics}]} from a course plan."""
    return normalise_course_plan(_generate(data, mime, COURSE_PLAN_PROMPT, api_key, model,
                                           client_factory))


# --- ESE presentation review --------------------------------------------------------
REVIEW_PROMPT = """You review a student's handwritten end-semester exam answer script for PRESENTATION ONLY.
Look at: legibility of handwriting; structure (headings, sub-points, paragraphs); diagrams and
labelling; question numbering and answer order; answer length compared with the marks;
use of examples; margins, neatness and corrections; signs of running out of time
(rushed or unfinished final answers).
Do NOT judge whether the subject content is correct, and do not mention marks or grades.
Base every point on what is visible in the script. Be specific, kind and practical.
Return ONLY JSON of this shape:
{"strengths": ["string"],
 "improvements": [{"area": "string", "observation": "string", "tip": "string"}],
 "summary": "one or two sentences"}
Give 2 to 4 strengths and 2 to 5 improvements."""


def format_review(data: Any) -> str:
    """Markdown with the 'Doing well' / 'Improve' headings that split_review expects."""
    if not isinstance(data, dict):
        raise GeminiError("Gemini's reply did not have the expected review shape.")
    strengths, improvements = data.get("strengths") or [], data.get("improvements") or []
    if not isinstance(strengths, list) or not isinstance(improvements, list):
        raise GeminiError("Gemini's reply did not have the expected review shape.")
    good = [s for s in (_text_field(x, "strength") for x in strengths) if s]
    fix = []
    for item in improvements:
        if not isinstance(item, dict):
            raise GeminiError("Gemini's reply had an improvement in an unexpected shape.")
        area = _text_field(item.get("area"), "improvement area")
        obs = _text_field(item.get("observation"), "observation")
        tip = _text_field(item.get("tip"), "tip")
        if not (area or obs or tip):
            continue
        body = " ".join(p for p in (obs, f"*Tip:* {tip}" if tip else "") if p)
        fix.append(f"- **{area.rstrip('.')}.** {body}".rstrip() if area else f"- {body}")
    summary = _text_field(data.get("summary"), "summary")
    if not (good or fix or summary):
        raise GeminiError("Gemini returned an empty review. Use the manual checklist instead.")
    text = ("**Doing well**\n" + ("\n".join(f"- {s}" for s in good) or "- Nothing stood out yet.")
            + "\n\n**Improve**\n" + ("\n".join(fix) or "- Nothing to fix. Keep it up."))
    return text + (f"\n\n**In short:** {summary}" if summary else "")


def review_ese_script(data: bytes, mime: str, api_key: str | None, model: str | None = None,
                      client_factory: Callable[[str], Any] | None = None) -> str:
    """A presentation-only review of an answer script, as Markdown."""
    return format_review(_generate(data, mime, REVIEW_PROMPT, api_key, model, client_factory))
