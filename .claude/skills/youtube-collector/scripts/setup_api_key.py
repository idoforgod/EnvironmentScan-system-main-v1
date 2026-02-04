#!/usr/bin/env python3
"""
YouTube Data API 키를 설정하는 스크립트

사용자로부터 API 키를 입력받아 OS별 적절한 경로에 저장합니다.

저장 경로:
    - macOS/Linux: ~/.config/youtube-collector/config.yaml
    - Windows: %APPDATA%\\youtube-collector\\config.yaml

Usage:
    python setup_api_key.py                    # 대화형 입력
    python setup_api_key.py --api-key KEY      # 직접 지정
    python setup_api_key.py --show             # 현재 설정 확인
    python setup_api_key.py --path             # 설정 파일 경로 출력
"""

import argparse
import os
import platform
import sys


def get_config_path() -> str:
    """OS별 설정 파일 경로 반환"""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "youtube-collector", "config.yaml")
    else:  # macOS, Linux
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(xdg_config, "youtube-collector", "config.yaml")


def load_config(config_path: str) -> dict:
    """기존 설정 로드"""
    if not os.path.exists(config_path):
        return {}

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # yaml 없으면 간단히 파싱
        config = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip().strip('"\'')
        return config
    except Exception:
        return {}


def save_config(config_path: str, config: dict):
    """설정 저장"""
    # 디렉토리 생성
    config_dir = os.path.dirname(config_path)
    os.makedirs(config_dir, exist_ok=True)

    try:
        import yaml
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("# YouTube Collector API 설정\n")
            f.write("# 이 파일은 자동 생성되었습니다.\n\n")
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        # yaml 없으면 수동 작성
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("# YouTube Collector API 설정\n")
            f.write("# 이 파일은 자동 생성되었습니다.\n\n")
            for key, value in config.items():
                f.write(f'{key}: "{value}"\n')


def mask_api_key(key: str) -> str:
    """API 키 마스킹 (앞 8자, 뒤 4자만 표시)"""
    if not key or len(key) < 16:
        return "***"
    return f"{key[:8]}...{key[-4:]}"


def main():
    parser = argparse.ArgumentParser(description='YouTube Data API 키 설정')
    parser.add_argument('--api-key', help='설정할 API 키')
    parser.add_argument('--show', action='store_true', help='현재 설정 확인')
    parser.add_argument('--path', action='store_true', help='설정 파일 경로 출력')

    args = parser.parse_args()

    config_path = get_config_path()

    # 경로만 출력
    if args.path:
        print(config_path)
        return

    # 현재 설정 확인
    if args.show:
        if os.path.exists(config_path):
            config = load_config(config_path)
            api_key = config.get('api_key', '')
            print(f"설정 파일: {config_path}")
            print(f"API 키: {mask_api_key(api_key) if api_key else '(설정되지 않음)'}")
        else:
            print(f"설정 파일이 없습니다: {config_path}")
        return

    # API 키 설정
    api_key = args.api_key

    if not api_key:
        # 대화형 입력
        print("YouTube Data API 키 설정")
        print("-" * 40)
        print(f"설정 파일 경로: {config_path}")
        print()
        print("API 키 발급 방법:")
        print("1. https://console.cloud.google.com/ 접속")
        print("2. 프로젝트 생성/선택")
        print("3. YouTube Data API v3 활성화")
        print("4. 사용자 인증 정보 > API 키 생성")
        print()

        try:
            api_key = input("API 키를 입력하세요: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n취소되었습니다.")
            sys.exit(1)

    if not api_key:
        print("API 키가 입력되지 않았습니다.")
        sys.exit(1)

    # 기존 설정 로드 및 업데이트
    config = load_config(config_path)
    config['api_key'] = api_key

    # 저장
    save_config(config_path, config)

    print()
    print(f"API 키가 저장되었습니다: {config_path}")
    print(f"저장된 키: {mask_api_key(api_key)}")


if __name__ == "__main__":
    main()
