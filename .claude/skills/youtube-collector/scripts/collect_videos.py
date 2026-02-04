#!/usr/bin/env python3
"""
채널의 영상을 수집하고 .reference/ 폴더에 YAML 파일로 저장하는 통합 스크립트

Usage:
    python collect_videos.py --channel-id UC... --output-dir .reference/
    python collect_videos.py --channel-handle @channelname --output-dir .reference/
    python collect_videos.py --all --output-dir .reference/  # channels.yaml의 모든 채널

Output:
    JSON 형식으로 처리 결과 요약 출력

Requirements:
    pip install google-api-python-client youtube-transcript-api pyyaml
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 같은 디렉토리의 모듈 import
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from fetch_videos import (
        load_api_key,
        get_channel_id_from_handle,
        fetch_videos,
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
    from fetch_transcript import fetch_transcript
except ImportError as e:
    print(json.dumps({
        "error": "fetch_transcript 모듈을 import할 수 없습니다.",
        "detail": str(e),
        "install": "pip install youtube-transcript-api"
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


def load_channels(output_dir: str) -> list:
    """channels.yaml에서 등록된 채널 목록 로드"""
    channels_file = Path(output_dir) / "channels.yaml"

    if not channels_file.exists():
        return []

    try:
        with open(channels_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('channels', []) if data else []
    except Exception:
        return []


def get_existing_video_ids(output_dir: str, channel_handle: str) -> set:
    """채널 폴더에서 이미 수집된 video_id 목록 반환"""
    # @ 제거
    handle_clean = channel_handle.lstrip('@')
    channel_dir = Path(output_dir) / "contents" / handle_clean

    if not channel_dir.exists():
        return set()

    video_ids = set()
    for yaml_file in channel_dir.glob("*.yaml"):
        # 파일명이 video_id.yaml 형식
        video_ids.add(yaml_file.stem)

    return video_ids


def save_video_yaml(output_dir: str, channel_handle: str, video_data: dict, transcript_data: dict) -> str:
    """영상 데이터를 YAML 파일로 저장"""
    # @ 제거
    handle_clean = channel_handle.lstrip('@')
    channel_dir = Path(output_dir) / "contents" / handle_clean

    # 폴더 생성
    channel_dir.mkdir(parents=True, exist_ok=True)

    # YAML 데이터 구성
    yaml_data = {
        'video_id': video_data['video_id'],
        'title': video_data['title'],
        'published_at': video_data['published_at'],
        'url': video_data['url'],
        'thumbnail': video_data['thumbnail'],
        'description': video_data['description'],
        'duration': video_data['duration'],
        'collected_at': datetime.utcnow().isoformat() + "Z",
        'transcript': {
            'available': transcript_data['available'],
            'language': transcript_data.get('language'),
            'text': transcript_data.get('text')
        },
        'summary': None  # AI가 나중에 추가
    }

    # 파일 저장
    file_path = channel_dir / f"{video_data['video_id']}.yaml"

    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return str(file_path)


def collect_channel_videos(
    youtube,
    channel_id: str,
    channel_handle: str,
    output_dir: str,
    max_results: int = 10,
    language: str = 'ko',
    skip_existing: bool = True
) -> dict:
    """단일 채널의 영상을 수집하고 저장"""
    result = {
        'channel': channel_handle,
        'channel_id': channel_id,
        'new_videos': [],
        'skipped': 0,
        'errors': []
    }

    # 기존 video_id 목록
    existing_ids = get_existing_video_ids(output_dir, channel_handle) if skip_existing else set()

    # 영상 목록 조회
    videos = fetch_videos(youtube, channel_id, max_results)

    for video in videos:
        video_id = video['video_id']

        # 중복 체크
        if video_id in existing_ids:
            result['skipped'] += 1
            continue

        try:
            # 자막 수집
            transcript = fetch_transcript(video_id, language)

            # YAML 저장
            file_path = save_video_yaml(output_dir, channel_handle, video, transcript)

            result['new_videos'].append({
                'video_id': video_id,
                'title': video['title'],
                'file_path': file_path,
                'transcript_available': transcript['available']
            })

        except Exception as e:
            result['errors'].append({
                'video_id': video_id,
                'error': str(e)
            })

    return result


def main():
    parser = argparse.ArgumentParser(description='YouTube 채널 영상 수집 및 저장')
    parser.add_argument('--channel-id', help='채널 ID (UC...)')
    parser.add_argument('--channel-handle', help='채널 핸들 (@username)')
    parser.add_argument('--all', action='store_true', help='channels.yaml의 모든 채널 처리')
    parser.add_argument('--output-dir', default='.reference', help='저장 디렉토리 (기본: .reference)')
    parser.add_argument('--max-results', type=int, default=10, help='채널당 최대 수집 개수 (기본: 10)')
    parser.add_argument('--language', default='ko', help='자막 우선 언어 (기본: ko)')
    parser.add_argument('--no-skip-existing', action='store_true', help='기존 파일도 덮어쓰기')
    parser.add_argument('--api-key', help='YouTube Data API 키 (미지정시 설정 파일에서 로드)')

    args = parser.parse_args()

    # 옵션 검증
    if not args.all and not args.channel_id and not args.channel_handle:
        print(json.dumps({
            "error": "--all, --channel-id, --channel-handle 중 하나를 지정해야 합니다."
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

    # 처리할 채널 목록 결정
    channels_to_process = []

    if args.all:
        # channels.yaml에서 모든 채널 로드
        channels = load_channels(args.output_dir)
        if not channels:
            print(json.dumps({
                "error": "등록된 채널이 없습니다.",
                "help": "먼저 register_channel.py로 채널을 등록해주세요."
            }))
            sys.exit(1)

        for ch in channels:
            channels_to_process.append({
                'id': ch.get('id'),
                'handle': ch.get('handle', '')
            })
    else:
        # 단일 채널 처리
        channel_id = args.channel_id
        channel_handle = args.channel_handle or ''

        if not channel_id and channel_handle:
            channel_id = get_channel_id_from_handle(youtube, channel_handle)
            if not channel_id:
                print(json.dumps({
                    "error": f"채널을 찾을 수 없습니다: {channel_handle}"
                }))
                sys.exit(1)

        channels_to_process.append({
            'id': channel_id,
            'handle': channel_handle
        })

    # 결과 수집
    all_results = {
        'processed_at': datetime.utcnow().isoformat() + "Z",
        'output_dir': args.output_dir,
        'channels_processed': 0,
        'total_new_videos': 0,
        'total_skipped': 0,
        'results': [],
        'errors': []
    }

    skip_existing = not args.no_skip_existing

    for channel in channels_to_process:
        try:
            result = collect_channel_videos(
                youtube=youtube,
                channel_id=channel['id'],
                channel_handle=channel['handle'],
                output_dir=args.output_dir,
                max_results=args.max_results,
                language=args.language,
                skip_existing=skip_existing
            )

            all_results['channels_processed'] += 1
            all_results['total_new_videos'] += len(result['new_videos'])
            all_results['total_skipped'] += result['skipped']
            all_results['results'].append(result)

            if result['errors']:
                all_results['errors'].extend(result['errors'])

        except Exception as e:
            all_results['errors'].append({
                'channel': channel.get('handle') or channel.get('id'),
                'error': str(e)
            })

    print(json.dumps(all_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
