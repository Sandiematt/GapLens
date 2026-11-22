from urllib.parse import quote_plus

from core import suggestions


def R(title, rtype, diff):
    return {"title": title, "rtype": rtype, "difficulty": diff}


def test_search_links_are_encoded_and_built_from_names():
    links = suggestions.search_links("Data Structures & Algo", "C++ trees")
    assert [l["kind"] for l in links] == ["youtube", "nptel", "practice"]
    yt, nptel, prac = (l["url"] for l in links)
    assert yt == "https://www.youtube.com/results?search_query=" + quote_plus(
        "Data Structures & Algo C++ trees")
    assert nptel.startswith("https://www.google.com/search?q=")
    assert quote_plus("site:nptel.ac.in") in nptel and "C%2B%2B" in nptel
    assert "practice" in prac and " " not in prac and "&Algo" not in prac
    assert all(l["title"] for l in links)


def test_big_gap_orders_video_reading_course_practice_then_easiest():
    res = [R("p", "practice", "beginner"), R("c", "course", "beginner"),
           R("r-adv", "reading", "advanced"), R("r-beg", "reading", "beginner"),
           R("v", "video", "intermediate")]
    out = suggestions.order_resources(res, 50)
    assert [r["title"] for r in out] == ["v", "r-beg", "r-adv", "c", "p"]


def test_small_gap_puts_practice_first():
    res = [R("v", "video", "beginner"), R("p2", "practice", "advanced"),
           R("p1", "practice", "beginner"), R("r", "reading", "beginner")]
    out = suggestions.order_resources(res, 49.9)
    assert [r["title"] for r in out][:2] == ["p1", "p2"]
    assert out[2]["title"] == "v"


def test_validate_resource():
    ok = dict(title="T", link="https://a.b/c", topic_id=3, rtype="video",
              difficulty="beginner")
    assert suggestions.validate_resource(**ok) == []
    assert suggestions.validate_resource(**{**ok, "link": "http://x.y"}) == []
    assert suggestions.validate_resource(**{**ok, "link": "ftp://x"})
    assert suggestions.validate_resource(**{**ok, "link": "youtube.com"})
    assert suggestions.validate_resource(**{**ok, "title": "  "})
    assert suggestions.validate_resource(**{**ok, "topic_id": None})
