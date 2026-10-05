# 디스코드 봇 토큰 설정 가이드

봇을 실행하려면 디스코드 개발자 포털에서 봇을 만들고, 발급받은 토큰을 `.env` 파일에 넣어야 합니다.

## 1. 애플리케이션 만들기

1. [Discord Developer Portal](https://discord.com/developers/applications)에 로그인합니다.
2. 오른쪽 위 **New Application**을 누르고 이름을 입력한 뒤 생성합니다.

## 2. 봇 토큰 발급

1. 왼쪽 메뉴에서 **Bot**을 엽니다.
2. **Reset Token**을 누르고 표시된 토큰을 복사합니다.
   - 토큰은 이 화면에서 한 번만 보여집니다. 잃어버리면 다시 Reset 해야 합니다.

## 3. Privileged Gateway Intents 켜기

같은 **Bot** 페이지 아래쪽에서 다음 두 항목을 켜고 **Save Changes**를 누릅니다.

| 항목 | 필요한 이유 |
|---|---|
| **Message Content Intent** | 메시지 내용을 읽어 금지어를 검사 |
| **Server Members Intent** | 경고·타임아웃 대상 멤버 정보 조회 |

> Message Content Intent가 꺼져 있으면 봇이 메시지 내용을 빈 문자열로 받아 **검열이 동작하지 않습니다.**

## 4. `.env` 파일에 토큰 넣기

프로젝트 폴더에서 예시 파일을 복사합니다.

```powershell
Copy-Item .env.example .env
```

`.env`를 열어 `DISCORD_TOKEN`에 복사한 토큰을 붙여 넣습니다. 따옴표는 필요 없습니다.

```env
DISCORD_TOKEN=여기에_복사한_토큰_붙여넣기
WARN_LIMIT=3
TIMEOUT_MINUTES=10
EXEMPT_MODS=false
```

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DISCORD_TOKEN` | (필수) | 봇 토큰 |
| `WARN_LIMIT` | `3` | 경고가 이 횟수의 배수가 될 때마다 타임아웃 |
| `TIMEOUT_MINUTES` | `10` | 타임아웃 시간(분) |
| `EXEMPT_MODS` | `false` | `true`면 메시지 관리 권한자는 검열 제외 |
| `DB_PATH` | `mbot.db` | SQLite DB 파일 경로 |

## 5. 봇을 서버에 초대

1. 왼쪽 메뉴 **General Information**에서 **Application ID**를 복사합니다.
2. 아래 주소의 `여기에_APPLICATION_ID`를 바꿔 브라우저에서 엽니다.

```
https://discord.com/oauth2/authorize?client_id=여기에_APPLICATION_ID&scope=bot+applications.commands&permissions=1099511720960
```

이 주소는 `bot`, `applications.commands` scope와 다음 권한을 요청합니다.

- 채널 보기, 메시지 보내기, 링크 첨부(임베드), 메시지 기록 보기
- 메시지 관리 (금지어 메시지 삭제)
- 멤버 타임아웃 (경고 누적 시 타임아웃)

초대 후 **서버 설정 → 역할**에서 봇 역할을 타임아웃할 유저들의 역할보다 **위로** 올려야 타임아웃이 동작합니다.

## 6. 실행 확인

```powershell
.venv\Scripts\python bot.py
```

콘솔에 `로그인: 봇이름#0000 (id=...)`이 나오면 성공입니다. 슬래시 명령어는 전역 등록이라 처음 표시되기까지 시간이 걸릴 수 있습니다.

## 문제 해결

| 증상 | 원인 / 해결 |
|---|---|
| `.env 파일에 DISCORD_TOKEN을 설정하세요.` | `.env` 파일이 없거나 `DISCORD_TOKEN`이 비어 있음 |
| `LoginFailure: Improper token has been passed.` | 토큰이 잘못됨 → 포털에서 Reset 후 다시 붙여넣기 |
| `PrivilegedIntentsRequired` | 3단계의 Intents가 꺼져 있음 |
| 금지어를 써도 반응 없음 | Message Content Intent 확인, 또는 `EXEMPT_MODS=true`인 상태에서 관리자로 테스트 중 |
| 타임아웃 실패 메시지 | 봇 역할 순서가 낮거나 대상이 서버 주인 |

## ⚠️ 토큰 보안

- 토큰은 봇 계정의 비밀번호와 같습니다. **절대 GitHub, 디스코드 채팅, 스크린샷 등에 공유하지 마세요.**
- `.env`는 `.gitignore`에 포함되어 있어 커밋되지 않습니다. `git status`에 `.env`가 보이면 커밋하지 마세요.
- 토큰이 유출됐다면 즉시 포털의 **Bot → Reset Token**으로 재발급하세요. 이전 토큰은 바로 무효화됩니다.
