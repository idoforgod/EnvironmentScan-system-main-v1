# Changelog - RLM Memory Optimization

## [1.0.1] - 2026-01-30 (Critical Fixes)

### 🐛 버그 수정

#### RecursiveArchiveLoader 날짜 필드 불일치 (Critical)
- **문제:** `_filter_by_date()`가 'first_detected'/'date' 필드만 찾음
- **실제:** 데이터는 'collected_at'/'scan_date' 필드 사용
- **영향:** 모든 신호를 건너뛰어 0개 로드됨
- **수정:** 6개 날짜 필드 모두 지원하도록 확장
  ```python
  signal_date_str = (
      signal.get('first_detected') or      # Legacy
      signal.get('date') or                 # Legacy
      signal.get('collected_at') or         # ✅ New
      signal.get('scan_date') or            # ✅ New
      signal.get('added_to_db_at') or       # ✅ New
      signal.get('source', {}).get('published_date')  # ✅ New
  )
  ```
- **검증:** 181/181 신호 정상 로드 확인

### ✨ 기능 추가

#### Entities 필드 자동 추출
- **파일:** `env-scanning/utils/entity_extractor.py` (신규)
- **기능:** 제목/초록에서 명명된 엔티티 자동 추출
  - Organizations: OpenAI, Microsoft, WHO, etc.
  - Technologies: GPT, Quantum Computing, CRISPR, etc.
  - Policy terms: Regulation, Framework, Bill, etc.
  - 캐피탈라이즈된 구문 (고유명사)
  - 약어 (3+ 글자)
- **통합:**
  - `base_scanner.py`: `create_standard_signal()`에 entities 매개변수 추가
  - `arxiv_scanner.py`: EntityExtractor 사용하여 자동 추출
- **효과:** Stage 4 deduplication (entity matching) 활성화

### 📊 검증 결과

#### 현재 데이터셋 (181 signals)
- RecursiveArchiveLoader: 181/181 로드 (100%)
- Filter ratio: 100% (모든 신호 오늘 수집)
- SharedContextManager: 75x 메모리 절감 (0.2KB vs 15KB)
- Entities 추출: 평균 9-10개/signal

#### 예상 프로덕션 성능
- 10,000 signals, 90일 아카이브
- RecursiveArchiveLoader: 10-20x 메모리 절감
- SharedContextManager: 4-8x 메모리 절감
- 전체: 5-8x 메모리 절감

---

## [1.0.0] - 2026-01-30 (Initial Release)

### ✨ 주요 기능

#### Phase 1: SharedContextManager
- Field-level selective loading
- 8개 필드별 getter/setter
- Lazy loading with caching
- Dirty field tracking (partial updates)
- Atomic writes (corruption prevention)
- Backward compatible (get_full_context)

#### Phase 2: RecursiveArchiveLoader
- Time-based filtering (7-day default)
- Index building (URL, title, entity)
- Multiple date format support
- Backward compatible (load_full_archive)

### 📚 문서

- Memory Optimization Guide (600+ lines)
- Quick Reference Card (400+ lines)
- Visual Summary (500+ lines)
- Implementation Summary (800+ lines)
- Implementation Reflection (검증 보고서)

### ✅ 검증

- Unit tests: ✅ 통과
- Integration tests: ✅ 통과
- Backward compatibility: ✅ 100% 유지
- Performance: ⚠️  소규모만 검증 (대규모 필요)

---

## 향후 계획

### 단기 (1-2주)
- [ ] 10,000+ 신호 테스트 데이터 생성
- [ ] 메모리 프로파일링 스크립트
- [ ] 성능 벤치마크 실행
- [ ] 대규모 환경 검증

### 장기 (1-2개월)
- [ ] Phase 3: 교차영향 분석 압축
- [ ] Phase 4: 임베딩 중복제거
- [ ] 추가 메모리 최적화

---

**버전:** 1.0.1
**날짜:** 2026-01-30
**상태:** 프로덕션 준비 (대규모 검증 필요)
