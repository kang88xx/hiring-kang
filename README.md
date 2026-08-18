# hiring-kang

개인 구직 활동을 위한 채용공고 수집·정리 프로젝트입니다.

- 웹 대시보드: **https://hiring.kang88.io** (GitHub Pages)
- 수집 데이터는 개인 구직 용도로만 사용하며, 재배포·상업적 이용을 하지 않습니다.

## 구성

```
collector/
  work24_collector.py    # 고용24 공채속보·공채기업·채용행사 수집기
  dart_collector.py      # DART 기업 고유번호 수집기
  saramin_collector.py   # 사람인 채용공고 API 수집기 (API 승인 대기 중)
  export_site.py         # jobs.db → docs/data.json 변환 (사이트 데이터 빌드)
data/jobs.db             # 수집 결과 (SQLite)
docs/                    # 정적 사이트 (GitHub Pages 배포 대상)
  index.html             # 대시보드 — 타입 탭·검색·필터, 행 클릭 시 원본 페이지 이동
  data.json              # export_site.py가 생성
  CNAME                  # hiring.kang88.io
```

## 사용법

```bash
pip install -r requirements.txt
cp .env.example .env               # 발급받은 API 키 입력

python collector/work24_collector.py   # 고용24 수집
python collector/dart_collector.py     # DART 기업 목록 수집
python collector/export_site.py        # 사이트용 data.json 재생성
```

수집 → `export_site.py` → 커밋·푸시하면 GitHub Pages에 자동 반영됩니다.

## 환경변수

| 변수 | 설명 |
|------|------|
| `SARAMIN_ACCESS_KEY` | 사람인 오픈 API access-key |
| `WORK24_JOB_KEY` | 고용24 Open API 인증키 (채용) |
| `WORK24_CODE_KEY` | 고용24 Open API 인증키 (공통코드) |
| `DART_API_KEY` | DART 전자공시 API 인증키 |
