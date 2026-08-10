"""DART(전자공시) 기업 데이터 수집기.

1) 전체 기업 고유번호 목록(corpCode)을 내려받아 SQLite에 저장한다.
   회사명 → corp_code 매핑의 기반 데이터로, 이후 기업개황/재무 조회에 사용한다.
2) fetch_company(corp_code)로 개별 기업개황을 조회할 수 있다.

사용법:
    python collector/dart_collector.py            # 기업 목록 전체 수집
    python collector/dart_collector.py 회사명     # 회사명 검색 + 기업개황 조회
"""

import io
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import requests

CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
COMPANY_URL = "https://opendart.fss.or.kr/api/company.json"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"


def api_key() -> str:
    key = os.environ.get("DART_API_KEY")
    if not key:
        sys.exit("DART_API_KEY 환경변수를 설정해주세요 (.env 참고)")
    return key


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dart_corps (
            corp_code TEXT PRIMARY KEY,
            corp_name TEXT,
            stock_code TEXT,
            modify_date TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dart_corps_name ON dart_corps(corp_name)")
    conn.commit()


def collect_corp_codes(conn: sqlite3.Connection) -> None:
    resp = requests.get(CORP_CODE_URL, params={"crtfc_key": api_key()}, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        xml_data = zf.read(zf.namelist()[0])

    root = ET.fromstring(xml_data)
    rows = [
        (
            corp.findtext("corp_code"),
            corp.findtext("corp_name"),
            (corp.findtext("stock_code") or "").strip(),
            corp.findtext("modify_date"),
        )
        for corp in root.iter("list")
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO dart_corps VALUES (?, ?, ?, ?)", rows
    )
    conn.commit()
    listed = sum(1 for r in rows if r[2])
    print(f"기업 {len(rows):,}곳 저장 (상장사 {listed:,}곳) → {DB_PATH}")


def fetch_company(corp_code: str) -> dict:
    resp = requests.get(
        COMPANY_URL, params={"crtfc_key": api_key(), "corp_code": corp_code}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def search_company(conn: sqlite3.Connection, name: str) -> None:
    rows = conn.execute(
        "SELECT corp_code, corp_name, stock_code FROM dart_corps "
        "WHERE corp_name LIKE ? ORDER BY stock_code DESC LIMIT 10",
        (f"%{name}%",),
    ).fetchall()
    if not rows:
        print(f"'{name}' 검색 결과 없음")
        return
    for corp_code, corp_name, stock_code in rows:
        tag = f"상장({stock_code})" if stock_code else "비상장"
        print(f"- {corp_name} [{tag}] corp_code={corp_code}")
    info = fetch_company(rows[0][0])
    if info.get("status") == "000":
        print(
            f"\n[기업개황] {info.get('corp_name')} | 대표: {info.get('ceo_nm')} | "
            f"업종코드: {info.get('induty_code')} | 설립일: {info.get('est_dt')} | "
            f"주소: {info.get('adres')}"
        )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    if len(sys.argv) > 1:
        search_company(conn, sys.argv[1])
    else:
        collect_corp_codes(conn)


if __name__ == "__main__":
    main()
