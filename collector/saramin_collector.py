"""사람인 채용공고 API 수집기.

사람인 오픈 API(https://oapi.saramin.co.kr/guide/job-search)에서
채용공고를 검색해 SQLite에 저장한다. 일일 호출 한도(500회)를 넘지 않도록
페이지당 최대 건수(110)로 요청한다.
"""

import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

API_URL = "https://oapi.saramin.co.kr/job-search"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"

# 검색 조건 (키 발급 후 관심 직무/지역에 맞게 조정)
SEARCH_PARAMS = {
    "keywords": "기획",
    "count": 110,
    "sort": "pd",  # 게시일 역순
}


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            company_url TEXT,
            location TEXT,
            job_type TEXT,
            experience TEXT,
            education TEXT,
            salary TEXT,
            url TEXT,
            posted_at TEXT,
            expires_at TEXT,
            collected_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.commit()


def fetch_page(access_key: str, start: int) -> dict:
    params = {"access-key": access_key, "start": start, **SEARCH_PARAMS}
    resp = requests.get(API_URL, params=params, headers={"Accept": "application/json"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_jobs(conn: sqlite3.Connection, jobs: list[dict]) -> int:
    saved = 0
    for job in jobs:
        position = job.get("position", {})
        company = job.get("company", {}).get("detail", {})
        row = (
            job.get("id"),
            position.get("title"),
            company.get("name"),
            company.get("href"),
            position.get("location", {}).get("name"),
            position.get("job-type", {}).get("name"),
            position.get("experience-level", {}).get("name"),
            position.get("required-education-level", {}).get("name"),
            job.get("salary", {}).get("name"),
            job.get("url"),
            job.get("posting-timestamp"),
            job.get("expiration-timestamp"),
        )
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO jobs
            (id, title, company, company_url, location, job_type,
             experience, education, salary, url, posted_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )
        saved += cur.rowcount
    conn.commit()
    return saved


def main() -> None:
    access_key = os.environ.get("SARAMIN_ACCESS_KEY")
    if not access_key:
        sys.exit("SARAMIN_ACCESS_KEY 환경변수를 설정해주세요 (.env.example 참고)")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    start = 0
    total_saved = 0
    while True:
        data = fetch_page(access_key, start)
        result = data.get("jobs", {})
        jobs = result.get("job", [])
        if not jobs:
            break
        total_saved += save_jobs(conn, jobs)
        total = int(result.get("total", 0))
        start += 1
        if (start * SEARCH_PARAMS["count"]) >= total:
            break
        time.sleep(1)  # 호출 간격 완충

    print(f"신규 저장 {total_saved}건 → {DB_PATH}")


if __name__ == "__main__":
    main()
