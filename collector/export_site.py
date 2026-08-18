"""jobs.db → 정적 사이트용 data.json 내보내기.

data/jobs.db의 고용24 수집 데이터를 읽어 docs/data.json으로 변환한다.
docs/는 GitHub Pages 배포 대상 디렉터리.

사용법:
    python collector/export_site.py
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"
OUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "data.json"




def fmt_date(yyyymmdd: str) -> str:
    s = (yyyymmdd or "").strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s


def load(conn: sqlite3.Connection, table: str) -> list[dict]:
    rows = conn.execute(f"SELECT fields FROM {table}").fetchall()
    return [json.loads(r[0]) for r in rows]


def export_open_emp(conn: sqlite3.Connection) -> list[dict]:
    out = []
    for r in load(conn, "work24_open_emp"):
        out.append(
            {
                "id": r.get("empSeqno", ""),
                "title": r.get("empWantedTitle", ""),
                "company": r.get("empBusiNm", ""),
                "corpType": r.get("coClcdNm", ""),
                "empType": r.get("empWantedTypeNm", ""),
                "start": fmt_date(r.get("empWantedStdt", "")),
                "end": fmt_date(r.get("empWantedEndt", "")),
                "url": r.get("empWantedHomepgDetail") or r.get("empWantedMobileUrl") or "",
            }
        )
    out.sort(key=lambda x: (x["end"] or "9999", x["company"]))
    return out


def export_events(conn: sqlite3.Connection) -> list[dict]:
    out = []
    for r in load(conn, "work24_events"):
        # url은 용량 절약을 위해 프런트에서 행사명 검색 링크로 조립한다.
        out.append(
            {
                "id": r.get("eventNo", ""),
                "name": r.get("eventNm", ""),
                "area": r.get("area", ""),
                "term": r.get("eventTerm", ""),
                "start": r.get("startDt", ""),
            }
        )
    out.sort(key=lambda x: x["start"] or "9999", reverse=False)
    return out


def export_companies(conn: sqlite3.Connection) -> list[dict]:
    out = []
    for r in load(conn, "work24_companies"):
        intro = (r.get("coIntroCont") or "").replace("\r\n", " ").replace("\n", " ").strip()
        out.append(
            {
                "id": r.get("empCoNo", ""),
                "name": r.get("coNm", ""),
                "corpType": r.get("coClcdNm", ""),
                "summary": r.get("coIntroSummaryCont", "") or intro[:80],
                "intro": intro[:160],
                "url": r.get("homepg", ""),
            }
        )
    out.sort(key=lambda x: x["name"])
    return out


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "open_emp": export_open_emp(conn),
        "events": export_events(conn),
        "companies": export_companies(conn),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(
        f"공채속보 {len(data['open_emp'])}건, 채용행사 {len(data['events'])}건, "
        f"공채기업 {len(data['companies'])}건 → {OUT_PATH} ({size_kb:.0f} KB)"
    )


if __name__ == "__main__":
    main()
