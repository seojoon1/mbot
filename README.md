# 간단한 디스코드 관리 봇

Python `discord.py` 기반의 검열 및 경고 봇입니다. 경고와 금지어는 서버별로 SQLite(`mbot.db`)에 저장됩니다.

## 기능

- 금지어가 포함된 메시지 자동 삭제 및 자동 경고 (띄어쓰기·특수문자 우회 방지, `EXEMPT_MODS=true`면 메시지 관리 권한자 제외)
- 경고 `WARN_LIMIT`회 누적마다 `TIMEOUT_MINUTES`분 타임아웃

| 명령어 | 설명 |
|---|---|
| `/경고 유저 [사유]` | 경고 부여 |
| `/경고목록 유저` | 경고 내역 조회 |
| `/경고삭제 유저 [번호]` | 경고 삭제 (번호 생략 시 전체 초기화) |
| `/금지어 추가 단어` | 금지어 추가 |
| `/금지어 삭제 단어` | 금지어 삭제 |
| `/금지어 목록` | 금지어 목록 조회 |

## 설치 및 실행

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env   # DISCORD_TOKEN 입력
.venv\Scripts\python bot.py
```

디스코드 개발자 포털의 Bot 설정에서 `Message Content Intent`와 `Server Members Intent`를 켜고,
봇 초대 시 `bot`, `applications.commands` scope와 메시지 관리·멤버 타임아웃 권한을 부여하세요.
봇 역할은 타임아웃할 유저의 역할보다 위에 있어야 합니다.

봇 토큰(`.env`)은 절대 저장소에 올리지 마세요.
