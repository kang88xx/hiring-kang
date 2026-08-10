"""고용24(워크넷) Open API 수집기 — 개인회원 이용 가능 범위.

개인회원 인증키로 이용 가능한 3개 API를 전량 수집한다.
(채용정보목록/상세 API는 개인회원 이용 불가)

  - 공채속보   (210L21): 진행 중인 공채 공고
  - 공채기업정보(210L31): 공채 진행 기업 정보 (사업자등록번호 포함)
  - 채용행사   (210L11): 채용박람회 등 행사 일정

사용법:
    python collector/work24_collector.py
"""

import json
import os
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BASE_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo{code}.do"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"
PAGE_SIZE = 100

SERVICES = {
    "work24_open_emp": {
        "code": "210L21",
        "list_tag": "dhsOpenEmpInfo",
        "id_tag": "empSeqno",
        "label": "공채속보",
    },
    "work24_companies": {
        "code": "210L31",
        "list_tag": "dhsOpenEmpHireInfo",
        "id_tag": "empCoNo",
        "label": "공채기업정보",
    },
    "work24_events": {
        "code": "210L11",
        "list_tag": "empEvent",
        "id_tag": "eventNo",
        "label": "채용행사",
    },
}


def api_key() -> str:
    key = os.environ.get("WORK24_JOB_KEY")
    if not key:
        sys.exit("WORK24_JOB_KEY 환경변수를 설정해주세요 (.env 참고)")
    return key


def init_db(conn: sqlite3.Connection) -> None:
    for table in SERVICES:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id TEXT PRIMARY KEY,
                title TEXT,
                fields TEXT,
                collected_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
    conn.commit()


def fetch_page(code: str, start_page: int) -> ET.Element:
    resp = requests.get(
        BASE_URL.format(code=code),
        params={
            "authKey": api_key(),
            "callTp": "L",
            "returnType": "XML",
            "startPage": start_page,
            "display": PAGE_SIZE,
        },
        timeout=30,
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    error = root.findtext("error")
    if error:
        raise RuntimeError(f"API 오류({code}): {error}")
    return root


def title_of(record: dict) -> str:
    for key in ("empWantedTitle", "coNm", "eventNm"):
        if record.get(key):
            return record[key]
    return ""


def collect(conn: sqlite3.Connection, table: str, svc: dict) -> None:
    page, saved, total = 1, 0, None
    while True:
        root = fetch_page(svc["code"], page)
        total = int(root.findtext("total", "0"))
        items = root.findall(svc["list_tag"])
        if not items:
            break
        for item in items:
            record = {child.tag: (child.text or "").strip() for child in item}
            cur = conn.execute(
                f"INSERT OR REPLACE INTO {table} (id, title, fields) VALUES (?, ?, ?)",
                (record.get(svc["id_tag"]), title_of(record), json.dumps(record, ensure_ascii=False)),
            )
            saved += cur.rowcount
        conn.commit()
        if page * PAGE_SIZE >= total:
            break
        page += 1
        time.sleep(0.3)
    print(f"{svc['label']}: 전체 {total}건 중 {saved}건 저장")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    for table, svc in SERVICES.items():
        collect(conn, table, svc)
    print(f"→ {DB_PATH}")


if __name__ == "__main__":
    main()
