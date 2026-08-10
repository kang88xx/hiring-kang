# hiring-kang

개인 구직 활동을 위한 채용공고 수집·정리 프로젝트입니다.

## 목적

- [사람인 채용정보 API](https://oapi.saramin.co.kr/)와 [워크넷 채용정보 API](https://www.data.go.kr/data/3038225/openapi.do)를 활용해 관심 직무의 채용공고를 주기적으로 수집합니다.
- 수집한 공고를 회사 정보와 함께 로컬 DB(SQLite)에 정리하고, 마감일 관리 및 지원 이력 트래킹에 활용합니다.
- 수집 데이터는 개인 구직 용도로만 사용하며, 재배포·상업적 이용을 하지 않습니다.

## 구성

```
collector/
  saramin_collector.py   # 사람인 채용공고 API 수집기
  worknet_collector.py   # 워크넷 채용정보 API 수집기 (예정)
data/                    # 수집 결과 (git 미포함)
```

## 사용법

```bash
pip install -r requirements.txt
cp .env.example .env     # 발급받은 API 키 입력
python collector/saramin_collector.py
```

## 환경변수

| 변수 | 설명 |
|------|------|
| `SARAMIN_ACCESS_KEY` | 사람인 오픈 API access-key |
| `WORKNET_SERVICE_KEY` | 공공데이터포털 워크넷 API 인증키 |
