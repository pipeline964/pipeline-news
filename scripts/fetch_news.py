"""Google 뉴스 RSS를 모아 news.json으로 저장 (GitHub Actions에서 실행)."""
import json, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

TOPICS = [
    ("주요 뉴스", ""),
    ("스타트업 투자", "스타트업 투자 유치"),
    ("IT 외주", "IT 외주 개발"),
    ("개발자 채용", "개발자 채용 스타트업"),
    ("미국 테크", "미국 테크 스타트업"),
]
MAX_ITEMS = 15

def feed_url(q):
    if not q:
        return "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    return ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:7d")
            + "&hl=ko&gl=KR&ceid=KR:ko")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (pipeline-news)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        src = (it.findtext("source") or "").strip()
        if not src and " - " in title:
            title, src = title.rsplit(" - ", 1)
        elif src and title.endswith(" - " + src):
            title = title[: -len(" - " + src)]
        try:
            ts = int(parsedate_to_datetime(it.findtext("pubDate")).timestamp())
        except Exception:
            ts = 0
        out.append({"title": title, "src": src, "link": (it.findtext("link") or "").strip(), "ts": ts})
    out.sort(key=lambda x: x["ts"], reverse=True)
    return out[:MAX_ITEMS]

def main():
    try:
        with open("news.json", encoding="utf-8") as f:
            prev = json.load(f).get("topics", {})
    except Exception:
        prev = {}
    topics = {}
    for label, q in TOPICS:
        try:
            topics[label] = parse(fetch(feed_url(q)))
        except Exception as e:
            print("fail", label, e)
            topics[label] = prev.get(label, [])
        time.sleep(1)
    data = {"updated": int(time.time()), "order": [t[0] for t in TOPICS], "topics": topics}
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
