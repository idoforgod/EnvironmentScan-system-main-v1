# YouTube Collector Skill

유튜브 채널을 등록하고, 새 컨텐츠를 수집하여 자막 기반 요약을 생성하는 Claude Code skill입니다.

## 주요 기능

- **채널 등록/관리**: 유튜브 채널을 등록하고 관리
- **컨텐츠 수집**: 등록된 채널의 최신 영상 정보 수집
- **자막 수집**: 영상의 자막(transcript) 자동 수집
- **요약 생성**: 자막 또는 설명 기반 요약 생성
- **중복 방지**: 이미 수집된 영상은 자동 스킵

## 초기 설정

### 1. 필수 패키지 설치
```bash
pip install google-api-python-client youtube-transcript-api pyyaml
```

### 2. API 키 설정
```bash
python3 .claude/skills/youtube-collector/scripts/setup_api_key.py
```

## 사용 프롬프트 예시

### 채널 등록

```
유튜브 채널 @channelname 등록해줘
```

```
이 유튜브 채널 등록해줘: https://youtube.com/@examplechannel
```

```
다음 채널들을 등록해줘:
- @channel1
- @channel2
- @channel3
```

### 컨텐츠 수집

```
등록된 유튜브 채널들의 새 영상 수집해줘
```

```
유튜브 채널 @channelname의 최신 영상 5개 수집해줘
```

```
모든 채널에서 새로운 컨텐츠 있는지 확인하고 수집해줘
```

### 수집된 데이터 조회

```
수집된 유튜브 컨텐츠 목록 보여줘
```

```
@channelname 채널에서 수집된 영상들 보여줘
```

```
최근 수집된 영상 요약 보여줘
```

### 채널 관리

```
등록된 유튜브 채널 목록 보여줘
```

```
@channelname 채널 등록 해제해줘
```

### API 키 관리

```
유튜브 API 키 설정 상태 확인해줘
```

```
유튜브 API 키 새로 설정해줘
```

## 데이터 저장 위치

| 데이터 | 경로 |
|--------|------|
| API 키 | `~/.config/youtube-collector/config.yaml` |
| 프로젝트 설정 | `.reference/youtube-config.yaml` |
| 등록된 채널 | `.reference/channels.yaml` |
| 수집된 컨텐츠 | `.reference/contents/{channel}/` |

## 스크립트

| 스크립트 | 설명 |
|----------|------|
| `setup_api_key.py` | API 키 설정 |
| `fetch_videos.py` | 채널 영상 목록 조회 |
| `fetch_transcript.py` | 영상 자막 수집 |
