# YouTube Collector 데이터 스키마

## 설정 파일 구조

### API 키 (사용자 홈 디렉토리)

보안을 위해 API 키는 코드베이스 외부에 저장됨.

**경로:**
- macOS/Linux: `~/.config/youtube-collector/config.yaml`
- Windows: `%APPDATA%\youtube-collector\config.yaml`

```yaml
api_key: "YOUR_YOUTUBE_DATA_API_KEY"
```

**설정 명령:**
```bash
python3 scripts/setup_api_key.py
```

### 프로젝트 설정 (.reference/)

```
.reference/
├── youtube-config.yaml     # 프로젝트 설정 (API 키 제외)
├── channels.yaml           # 등록된 채널 목록
└── contents/
    └── {channel_handle}/   # 채널별 폴더 (@ 제외)
        └── {video_id}.yaml # 영상별 데이터
```

## youtube-config.yaml

```yaml
# 자막 우선 언어 (기본: ko)
default_language: "ko"

# 채널당 최대 수집 개수 (기본: 10)
max_results: 10
```

## channels.yaml

```yaml
channels:
  - id: "UCxxxxxxxxxxxxxxxxxxxxxx"    # 채널 ID (UC로 시작)
    handle: "@channelname"            # 채널 핸들
    name: "채널 표시 이름"              # 사람이 읽기 쉬운 이름
    added_at: "2025-12-13"            # 등록일
```

## contents/{channel_handle}/{video_id}.yaml

```yaml
# 기본 정보
video_id: "abc123xyz"
title: "영상 제목"
published_at: "2025-12-10T10:00:00Z"
url: "https://youtube.com/watch?v=abc123xyz"
thumbnail: "https://i.ytimg.com/vi/abc123xyz/maxresdefault.jpg"
description: |
  영상 설명 전체 텍스트
duration: "PT10M30S"                   # ISO 8601 형식
collected_at: "2025-12-13T15:00:00Z"   # 수집 시점

# 자막 정보
transcript:
  available: true                      # 자막 존재 여부
  language: "ko"                       # 자막 언어
  text: |
    자막 전체 텍스트...

# 요약 정보 (초기값: null, AI가 생성하여 추가)
summary:
  source: "transcript"                 # "transcript" 또는 "description"
  content: |
    ## 서론
    - 문제 제기 또는 주제 소개
    - 영상의 목적/배경

    ## 본론
    - 핵심 내용 상세 설명
    - 해결책, 방법론, 예시 등
    - 주요 포인트별 정리

    ## 결론
    - 핵심 요약
    - 시사점 또는 다음 단계
```

### 자막이 없는 경우

```yaml
transcript:
  available: false
  language: null
  text: null

summary:
  source: "description"
  content: |
    (설명 기반 요약 내용)
```

## 중복 방지 규칙

- 파일명이 `{video_id}.yaml` 형식
- 수집 전 해당 파일 존재 여부로 중복 체크
- 이미 존재하는 video_id는 스킵
