#!/usr/bin/env python3
"""
YouTube 채널의 최신 영상 목록을 가져오는 스크립트

Usage:
    python fetch_videos.py --channel-id UC... [--api-key YOUR_API_KEY] [--max-results 10]
    python fetch_videos.py --channel-handle @channelname

API 키는 다음 위치에서 자동으로 로드됩니다:
    - macOS/Linux: ~/.config/youtube-collector/config.yaml
    - Windows: %APPDATA%\\youtube-collector\\config.yaml

Output:
    JSON 형식으로 영상 목록 출력

Requirements:
    pip install google-api-python-client pyyaml
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print(json.dumps({
        "error": "google-api-python-client가 설치되어 있지 않습니다.",
        "install": "pip install google-api-python-client"
    }))
    sys.exit(1)

try:
    import yaml
except ImportError:
    print(json.dumps({
        "error": "pyyaml이 설치되어 있지 않습니다.",
        "install": "pip install pyyaml"
    }))
    sys.exit(1)


def get_api_key_config_path() -> str:
    """OS별 API 키 설정 파일 경로 반환"""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "youtube-collector", "config.yaml")
    else:  # macOS, Linux
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(xdg_config, "youtube-collector", "config.yaml")


def load_api_key() -> str:
    """설정 파일에서 API 키 로드"""
    config_path = get_api_key_config_path()

    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('api_key') if config else None
    except Exception:
        return None


def get_channel_id_from_handle(youtube, handle: str) -> str:
    """채널 핸들(@username)로 채널 ID 조회"""
    # @를 제거
    handle = handle.lstrip('@')

    try:
        response = youtube.search().list(
            part="snippet",
            q=f"@{handle}",
            type="channel",
            maxResults=1
        ).execute()

        if response.get('items'):
            return response['items'][0]['snippet']['channelId']
        return None
    except HttpError as e:
        return None


def get_channel_uploads_playlist_id(youtube, channel_id: str) -> str:
    """채널의 업로드 재생목록 ID 조회 (UC... -> UU...)"""
    try:
        response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()

        if response.get('items'):
            return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return None
    except HttpError:
        return None


def fetch_videos(youtube, channel_id: str, max_results: int = 10) -> list:
    """채널의 최신 영상 목록 조회"""
    videos = []

    # 업로드 재생목록 ID 가져오기
    uploads_playlist_id = get_channel_uploads_playlist_id(youtube, channel_id)
    if not uploads_playlist_id:
        return videos

    try:
        # 재생목록에서 영상 ID 목록 가져오기
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(max_results, 50)
        ).execute()

        video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]

        if not video_ids:
            return videos

        # 영상 상세 정보 가져오기
        videos_response = youtube.videos().list(
            part="snippet,contentDetails",
            id=','.join(video_ids)
        ).execute()

        for item in videos_response.get('items', []):
            snippet = item['snippet']
            content_details = item['contentDetails']

            # 썸네일 URL (최대 해상도 우선)
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = (
                thumbnails.get('maxres', {}).get('url') or
                thumbnails.get('high', {}).get('url') or
                thumbnails.get('medium', {}).get('url') or
                thumbnails.get('default', {}).get('url', '')
            )

            videos.append({
                'video_id': item['id'],
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'published_at': snippet.get('publishedAt', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'thumbnail': thumbnail_url,
                'duration': content_details.get('duration', ''),
                'url': f"https://youtube.com/watch?v={item['id']}"
            })

        return videos

    except HttpError as e:
        print(json.dumps({
            "error": f"YouTube API 오류: {e.resp.status}",
            "message": str(e)
        }), file=sys.stderr)
        return videos


def main():
    parser = argparse.ArgumentParser(description='YouTube 채널의 최신 영상 목록 조회')
    parser.add_argument('--channel-id', help='채널 ID (UC...)')
    parser.add_argument('--channel-handle', help='채널 핸들 (@username)')
    parser.add_argument('--api-key', help='YouTube Data API 키 (미지정시 설정 파일에서 로드)')
    parser.add_argument('--max-results', type=int, default=10, help='최대 결과 수 (기본: 10)')

    args = parser.parse_args()

    if not args.channel_id and not args.channel_handle:
        print(json.dumps({
            "error": "--channel-id 또는 --channel-handle 중 하나를 지정해야 합니다."
        }))
        sys.exit(1)

    # API 키 결정: 인자 > 설정 파일
    api_key = args.api_key or load_api_key()

    if not api_key:
        config_path = get_api_key_config_path()
        print(json.dumps({
            "error": "YouTube Data API 키가 설정되지 않았습니다.",
            "help": f"다음 명령으로 API 키를 설정하세요: python3 setup_api_key.py",
            "config_path": config_path
        }))
        sys.exit(1)

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
    except Exception as e:
        print(json.dumps({
            "error": "YouTube API 초기화 실패",
            "message": str(e)
        }))
        sys.exit(1)

    # 채널 ID 결정
    channel_id = args.channel_id
    if not channel_id and args.channel_handle:
        channel_id = get_channel_id_from_handle(youtube, args.channel_handle)
        if not channel_id:
            print(json.dumps({
                "error": f"채널을 찾을 수 없습니다: {args.channel_handle}"
            }))
            sys.exit(1)

    # 영상 목록 조회
    videos = fetch_videos(youtube, channel_id, args.max_results)

    print(json.dumps({
        "channel_id": channel_id,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "count": len(videos),
        "videos": videos
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
