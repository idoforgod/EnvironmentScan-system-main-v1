#!/usr/bin/env python3
"""
YouTube 채널을 channels.yaml에 등록하는 스크립트

Usage:
    python register_channel.py --channel-handle @channelname --output-dir .reference/
    python register_channel.py --channel-url https://youtube.com/@channelname --output-dir .reference/

Output:
    JSON 형식으로 등록 결과 출력

Requirements:
    pip install google-api-python-client pyyaml
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

# 같은 디렉토리의 모듈 import
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from fetch_videos import (
        load_api_key,
        get_channel_id_from_handle,
    )
    from googleapiclient.discovery import build
except ImportError as e:
    print(json.dumps({
        "error": "필요한 모듈을 import할 수 없습니다.",
        "detail": str(e),
        "install": "pip install google-api-python-client pyyaml"
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


def extract_handle_from_url(url: str) -> str:
    """YouTube URL에서 채널 핸들 추출"""
    # URL 디코딩
    url = unquote(url)

    # URL 파싱
    parsed = urlparse(url)
    path = parsed.path

    # @username 형식 (예: youtube.com/@channelname)
    match = re.match(r'^/@([^/]+)', path)
    if match:
        return '@' + match.group(1)

    # /channel/UC... 형식
    match = re.match(r'^/channel/(UC[a-zA-Z0-9_-]+)', path)
    if match:
        return match.group(1)  # 채널 ID 반환

    # /c/customname 형식
    match = re.match(r'^/c/([^/]+)', path)
    if match:
        return '@' + match.group(1)

    # /user/username 형식
    match = re.match(r'^/user/([^/]+)', path)
    if match:
        return '@' + match.group(1)

    return None


def get_channel_info(youtube, channel_id: str) -> dict:
    """채널 ID로 채널 상세 정보 조회"""
    try:
        response = youtube.channels().list(
            part="snippet",
            id=channel_id
        ).execute()

        if response.get('items'):
            snippet = response['items'][0]['snippet']
            return {
                'id': channel_id,
                'name': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'custom_url': snippet.get('customUrl', '')
            }
        return None
    except Exception:
        return None


def load_channels(channels_file: Path) -> dict:
    """channels.yaml 로드"""
    if not channels_file.exists():
        return {'channels': []}

    try:
        with open(channels_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data else {'channels': []}
    except Exception:
        return {'channels': []}


def save_channels(channels_file: Path, data: dict):
    """channels.yaml 저장"""
    # 부모 폴더 생성
    channels_file.parent.mkdir(parents=True, exist_ok=True)

    with open(channels_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description='YouTube 채널 등록')
    parser.add_argument('--channel-handle', help='채널 핸들 (@username)')
    parser.add_argument('--channel-url', help='채널 URL')
    parser.add_argument('--channel-id', help='채널 ID (UC...)')
    parser.add_argument('--output-dir', default='.reference', help='저장 디렉토리 (기본: .reference)')
    parser.add_argument('--api-key', help='YouTube Data API 키 (미지정시 설정 파일에서 로드)')

    args = parser.parse_args()

    # 옵션 검증
    if not args.channel_handle and not args.channel_url and not args.channel_id:
        print(json.dumps({
            "error": "--channel-handle, --channel-url, --channel-id 중 하나를 지정해야 합니다."
        }))
        sys.exit(1)

    # API 키 로드
    api_key = args.api_key or load_api_key()
    if not api_key:
        print(json.dumps({
            "error": "YouTube Data API 키가 설정되지 않았습니다.",
            "help": "python3 scripts/setup_api_key.py로 설정해주세요."
        }))
        sys.exit(1)

    # YouTube API 초기화
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
    except Exception as e:
        print(json.dumps({
            "error": "YouTube API 초기화 실패",
            "message": str(e)
        }))
        sys.exit(1)

    # 채널 핸들/ID 결정
    channel_handle = args.channel_handle
    channel_id = args.channel_id

    if args.channel_url:
        extracted = extract_handle_from_url(args.channel_url)
        if not extracted:
            print(json.dumps({
                "error": "URL에서 채널 정보를 추출할 수 없습니다.",
                "url": args.channel_url
            }))
            sys.exit(1)

        if extracted.startswith('UC'):
            channel_id = extracted
        else:
            channel_handle = extracted

    # 채널 ID 조회
    if not channel_id and channel_handle:
        channel_id = get_channel_id_from_handle(youtube, channel_handle)
        if not channel_id:
            print(json.dumps({
                "error": f"채널을 찾을 수 없습니다: {channel_handle}"
            }))
            sys.exit(1)

    # 채널 상세 정보 조회
    channel_info = get_channel_info(youtube, channel_id)
    if not channel_info:
        print(json.dumps({
            "error": f"채널 정보를 가져올 수 없습니다: {channel_id}"
        }))
        sys.exit(1)

    # 핸들 결정 (없으면 custom_url 사용)
    if not channel_handle:
        custom_url = channel_info.get('custom_url', '')
        if custom_url:
            channel_handle = custom_url if custom_url.startswith('@') else '@' + custom_url
        else:
            channel_handle = '@' + channel_id  # fallback

    # channels.yaml 로드
    channels_file = Path(args.output_dir) / "channels.yaml"
    data = load_channels(channels_file)

    # 중복 체크
    existing_ids = {ch.get('id') for ch in data.get('channels', [])}
    if channel_id in existing_ids:
        print(json.dumps({
            "status": "already_registered",
            "message": f"채널이 이미 등록되어 있습니다: {channel_info['name']}",
            "channel": {
                "id": channel_id,
                "handle": channel_handle,
                "name": channel_info['name']
            }
        }))
        sys.exit(0)

    # 채널 추가
    new_channel = {
        'id': channel_id,
        'handle': channel_handle,
        'name': channel_info['name'],
        'added_at': datetime.now().strftime('%Y-%m-%d')
    }

    data['channels'].append(new_channel)

    # 저장
    save_channels(channels_file, data)

    print(json.dumps({
        "status": "registered",
        "message": f"채널이 등록되었습니다: {channel_info['name']}",
        "channel": new_channel,
        "file": str(channels_file)
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
