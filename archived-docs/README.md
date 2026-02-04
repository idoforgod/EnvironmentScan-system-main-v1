# Archived Documentation

이 폴더는 개발 과정에서 생성된 **임시 문서, 완료 보고서, 테스트 결과** 등을 보관합니다.

## 📁 폴더 구조

```
archived-docs/
├── completed-reports/     # 완료 보고서 (COMPLETE.md)
├── test-results/          # 테스트 결과 (TEST_*.md, VALIDATION_*.md)
├── design-docs/           # 설계/구현 문서 (DESIGN_*.md, IMPLEMENTATION_*.md)
├── analysis-reports/      # 분석 보고서 (ANALYSIS_*.md, REPORT.md)
└── [기타 임시 문서]
```

## 📝 문서 분류 기준

### ✅ 루트에 보관 (시스템 핵심 문서)
- `README.md` - 프로젝트 설명
- `USER_GUIDE.md` - 사용자 가이드
- `IMPLEMENTATION_GUIDE.md` - 구현 가이드
- `CHANGELOG.md` - 변경 이력
- `QUICK_START.md` - 빠른 시작

### 📦 archived-docs에 보관 (임시/완료 문서)
- `*_COMPLETE.md` → completed-reports/
- `*_REPORT.md`, `*_ANALYSIS_*.md` → analysis-reports/
- `TEST_*.md`, `VALIDATION_*.md` → test-results/
- `DESIGN_*.md`, `IMPLEMENTATION_STATUS.md` → design-docs/
- 기타 임시 문서 → archived-docs/ (루트)

## 🤖 자동화 규칙

**개발 과정에서 새로운 문서 생성 시:**

1. **완료 보고서** (*_COMPLETE.md, 완료_*.md)
   ```bash
   mv *_COMPLETE.md archived-docs/completed-reports/
   ```

2. **테스트 결과** (TEST_*.md, VALIDATION_*.md)
   ```bash
   mv TEST_*.md VALIDATION_*.md archived-docs/test-results/
   ```

3. **분석 보고서** (*_REPORT.md, *_ANALYSIS_*.md)
   ```bash
   mv *_REPORT.md *_ANALYSIS_*.md archived-docs/analysis-reports/
   ```

4. **설계/구현 문서** (DESIGN_*.md, IMPLEMENTATION_STATUS.md 등)
   ```bash
   mv DESIGN_*.md IMPLEMENTATION_STATUS.md archived-docs/design-docs/
   ```

## 📌 원칙

> **루트는 깔끔하게, 이력은 체계적으로 보관**

- 프로젝트 루트는 **영구적인 시스템 문서만** 유지
- 개발 과정의 산출물은 **즉시 archived-docs로 이동**
- 이력 추적이 필요한 경우 git history 활용
- 정기적으로 archived-docs 정리 (6개월~1년 단위)

---

**생성일**: 2026-01-30
**관리자**: Environmental Scanning System Team
