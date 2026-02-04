#!/usr/bin/env python3
"""
YouTube 영상의 자막(transcript)을 가져오는 스크립트

Usage:
    python fetch_transcript.py --video-id VIDEO_ID [--language ko]

Output:
    JSON 형식으로 자막 출력

Requirements:
    pip install youtube-transcript-api
"""

import argparse
import json
import sys

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
        CouldNotRetrieveTranscript
    )
except ImportError:
    print(json.dumps({
        "error": "youtube-transcript-api가 설치되어 있지 않습니다.",
        "install": "pip install youtube-transcript-api"
    }))
    sys.exit(1)


def fetch_transcript(video_id: str, preferred_language: str = 'ko') -> dict:
    """
    영상 자막 가져오기

    Args:
        video_id: YouTube 영상 ID
        preferred_language: 우선 언어 코드 (기본: ko)

    Returns:
        dict: {
            'available': bool,
            'language': str or None,
            'text': str or None,
            'segments': list or None,
            'error': str or None
        }
    """
    result = {
        'available': False,
        'language': None,
        'text': None,
        'segments': None,
        'error': None
    }

    try:
        # 사용 가능한 자막 목록 조회
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None

        # 1. 우선 언어의 수동 자막 시도
        try:
            transcript = transcript_list.find_manually_created_transcript([preferred_language])
        except NoTranscriptFound:
            pass

        # 2. 우선 언어의 자동 생성 자막 시도
        if not transcript:
            try:
                transcript = transcript_list.find_generated_transcript([preferred_language])
            except NoTranscriptFound:
                pass

        # 3. 영어 자막 시도 (한국어 없을 경우)
        if not transcript and preferred_language != 'en':
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except NoTranscriptFound:
                    pass

        # 4. 아무 자막이나 가져오기
        if not transcript:
            try:
                for t in transcript_list:
                    transcript = t
                    break
            except:
                pass

        if transcript:
            segments = transcript.fetch()
            full_text = ' '.join([segment['text'] for segment in segments])

            result['available'] = True
            result['language'] = transcript.language_code
            result['text'] = full_text
            result['segments'] = segments

    except TranscriptsDisabled:
        result['error'] = "이 영상은 자막이 비활성화되어 있습니다."
    except CouldNotRetrieveTranscript:
        result['error'] = "이 영상에는 사용 가능한 자막이 없습니다."
    except VideoUnavailable:
        result['error'] = "영상을 찾을 수 없습니다."
    except Exception as e:
        result['error'] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description='YouTube 영상 자막 가져오기')
    parser.add_argument('--video-id', required=True, help='영상 ID')
    parser.add_argument('--language', default='ko', help='우선 언어 (기본: ko)')
    parser.add_argument('--include-segments', action='store_true',
                        help='타임스탬프가 포함된 세그먼트 정보 포함')

    args = parser.parse_args()

    result = fetch_transcript(args.video_id, args.language)

    # 세그먼트 정보 제외 옵션
    if not args.include_segments and result.get('segments'):
        del result['segments']

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
