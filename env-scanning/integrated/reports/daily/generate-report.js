const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer, AlignmentType, LevelFormat, TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak } = require("docx");

const C = { navy: "1B2A4A", accent: "2E5090", light: "D5E8F0", mid: "B0C4DE", gray: "666666", red: "C0392B", border: "AAAAAA", white: "FFFFFF", black: "000000", lightGray: "F2F2F2", critBg: "FADBD8", highBg: "FEF9E7" };
const tb = { style: BorderStyle.SINGLE, size: 1, color: C.border };
const cb = { top: tb, bottom: tb, left: tb, right: tb };
const noBorder = { style: BorderStyle.NONE, size: 0, color: C.white };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const TW = 9026;

function txt(t, opts = {}) { return new TextRun({ text: t, font: "Arial", size: 22, ...opts }); }
function boldTxt(t, opts = {}) { return txt(t, { bold: true, ...opts }); }
function p(children, opts = {}) { return new Paragraph({ spacing: { after: 120 }, ...opts, children: Array.isArray(children) ? children : [children] }); }
function h1(t) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 }, children: [new TextRun({ text: t, font: "Arial", size: 32, bold: true, color: C.navy })] }); }
function h2(t) { return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 160 }, children: [new TextRun({ text: t, font: "Arial", size: 28, bold: true, color: C.accent })] }); }
function h3(t) { return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 120 }, children: [new TextRun({ text: t, font: "Arial", size: 24, bold: true, color: C.navy })] }); }
function emptyP(sz = 80) { return new Paragraph({ spacing: { after: sz }, children: [] }); }
function headerCell(t, w) {
  return new TableCell({ borders: cb, width: { size: w, type: WidthType.DXA }, shading: { fill: C.navy, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 40, after: 40 }, children: [new TextRun({ text: t, bold: true, color: C.white, font: "Arial", size: 20 })] })] });
}
function dataCell(t, w, opts = {}) {
  const fill = opts.fill || null;
  return new TableCell({ borders: cb, width: { size: w, type: WidthType.DXA }, shading: fill ? { fill, type: ShadingType.CLEAR } : undefined, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ spacing: { before: 30, after: 30 }, ...opts.pOpts, children: Array.isArray(t) ? t : [txt(typeof t === "string" ? t : String(t), opts.tOpts || {})] })] });
}
function bullet(t, ref = "bullet-list") { return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 60 }, children: Array.isArray(t) ? t : [txt(t)] }); }
function numbered(t, ref) { return new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80 }, children: Array.isArray(t) ? t : [txt(t)] }); }
function calloutBox(children, borderColor = C.accent, bgColor = "EBF5FB") {
  return new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: { top: { style: BorderStyle.SINGLE, size: 1, color: borderColor }, bottom: { style: BorderStyle.SINGLE, size: 1, color: borderColor }, left: { style: BorderStyle.SINGLE, size: 6, color: borderColor }, right: { style: BorderStyle.SINGLE, size: 1, color: borderColor } }, width: { size: TW, type: WidthType.DXA }, shading: { fill: bgColor, type: ShadingType.CLEAR }, children })] })] });
}
function quoteBox(text) {
  return new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: { top: noBorder, bottom: noBorder, left: { style: BorderStyle.SINGLE, size: 6, color: C.accent }, right: noBorder }, width: { size: TW, type: WidthType.DXA }, children: [p([txt(text, { italics: true, color: C.gray, size: 22 })], { indent: { left: 200 }, spacing: { before: 80, after: 80 } })] })] })] });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 56, bold: true, color: C.navy, font: "Arial" }, paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: C.navy, font: "Arial" }, paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: C.accent, font: "Arial" }, paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: C.navy, font: "Arial" }, paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: { config: [
    { reference: "bullet-list", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num-method", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num-imm", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num-mid", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num-stalin", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: [
    // ══════════════════════════════
    // COVER PAGE
    // ══════════════════════════════
    {
      properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }, size: { width: 11906, height: 16838 } } },
      children: [
        emptyP(600), emptyP(600), emptyP(600), emptyP(600),
        new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: { top: noBorder, bottom: { style: BorderStyle.SINGLE, size: 6, color: C.navy }, left: noBorder, right: noBorder }, width: { size: TW, type: WidthType.DXA }, children: [emptyP(20)] })] })] }),
        emptyP(300),
        p([txt("통합 환경스캐닝 분석 보고서", { size: 22, color: C.gray })], { alignment: AlignmentType.CENTER }),
        p([txt("일반 환경스캐닝 + 학술 심층스캐닝 통합", { size: 20, color: C.gray, italics: true })], { alignment: AlignmentType.CENTER }),
        emptyP(200),
        p([txt("중국 정치군사 영역의 권력 투쟁과 대규모 숙청", { size: 44, bold: true, color: C.navy, font: "Arial" })], { alignment: AlignmentType.CENTER, spacing: { after: 80 } }),
        p([txt("확실한 결과 분석", { size: 36, bold: true, color: C.accent })], { alignment: AlignmentType.CENTER }),
        emptyP(100),
        p([txt("시진핑의 승패와 무관한 구조적 영향 평가", { size: 24, color: C.gray, italics: true })], { alignment: AlignmentType.CENTER }),
        emptyP(300),
        calloutBox([
          p([boldTxt("핵심 명제", { size: 22, color: C.accent })], { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 80 } }),
          p([txt("시진핑의 승패와 무관하게, 현재 중국 내 군부 숙청사건이 초래하는 확실한 결과:", { size: 22 })], { alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
          p([boldTxt("(1) 중국 군대의 전력 약화", { size: 24, color: C.navy })], { alignment: AlignmentType.CENTER, spacing: { after: 40 } }),
          p([boldTxt("(2) 중국 공산당 내 신뢰 및 충성심 약화", { size: 24, color: C.navy })], { alignment: AlignmentType.CENTER, spacing: { after: 120 } }),
        ]),
        emptyP(400),
        new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: { top: { style: BorderStyle.SINGLE, size: 6, color: C.navy }, bottom: noBorder, left: noBorder, right: noBorder }, width: { size: TW, type: WidthType.DXA }, children: [emptyP(20)] })] })] }),
        emptyP(100),
        new Table({ columnWidths: [2500, 6526], rows: [
          new TableRow({ children: [new TableCell({ borders: noBorders, width: { size: 2500, type: WidthType.DXA }, children: [p([boldTxt("보고서 ID:", { size: 20, color: C.gray })])] }), new TableCell({ borders: noBorders, width: { size: 6526, type: WidthType.DXA }, children: [p([txt("INT-2026-02-04-CHINA-MIL-PURGE", { size: 20 })])] })] }),
          new TableRow({ children: [new TableCell({ borders: noBorders, width: { size: 2500, type: WidthType.DXA }, children: [p([boldTxt("날짜:", { size: 20, color: C.gray })])] }), new TableCell({ borders: noBorders, width: { size: 6526, type: WidthType.DXA }, children: [p([txt("2026년 2월 4일", { size: 20 })])] })] }),
          new TableRow({ children: [new TableCell({ borders: noBorders, width: { size: 2500, type: WidthType.DXA }, children: [p([boldTxt("보안등급:", { size: 20, color: C.gray })])] }), new TableCell({ borders: noBorders, width: { size: 6526, type: WidthType.DXA }, children: [p([boldTxt("내부용 (INTERNAL)", { size: 20, color: C.red })])] })] }),
          new TableRow({ children: [new TableCell({ borders: noBorders, width: { size: 2500, type: WidthType.DXA }, children: [p([boldTxt("분석 방법:", { size: 20, color: C.gray })])] }), new TableCell({ borders: noBorders, width: { size: 6526, type: WidthType.DXA }, children: [p([txt("이중 워크플로우 통합 분석 (35개 이상 소스)", { size: 20 })])] })] }),
        ] }),
      ]
    },
    // ══════════════════════════════
    // TOC + MAIN CONTENT
    // ══════════════════════════════
    {
      properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }, size: { width: 11906, height: 16838 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [txt("INT-2026-02-04 | ", { size: 16, color: C.gray, italics: true }), txt("내부용", { size: 16, color: C.red, bold: true })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [txt("- ", { size: 18, color: C.gray }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: C.gray }), txt(" -", { size: 18, color: C.gray })] })] }) },
      children: [
        h1("목 차"),
        new TableOfContents("", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 1. 경영진 요약
        // ══════════════════════════════
        h1("1. 경영진 요약"),
        h2("1.1 핵심 발견 (상위 5개 신호)"),

        // ── Signal 1 ──
        h3("신호 1: 중앙군사위원회(Central Military Commission) 사실상 와해 — 문화대혁명 이후 최초"),
        new Table({ columnWidths: [2200, 6826], rows: [
          new TableRow({ children: [dataCell("분석 유형", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("일반 환경스캐닝 (미디어, 싱크탱크, 정책 소스)", 6826)] }),
          new TableRow({ children: [dataCell("도메인", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("정치(Political)", 6826)] }),
          new TableRow({ children: [dataCell("중요도", 2200, { fill: C.critBg, tOpts: { bold: true } }), dataCell([boldTxt("최고 위험", { color: C.red }), txt(" (신뢰도 92점)")], 6826, { fill: C.critBg })] }),
          new TableRow({ children: [dataCell("핵심 내용", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("중앙군사위원회 7인 중 5인 연속 낙마(71.4%), 시진핑과 장성민만 잔류. 합참참모장 공석, 동부전구사령관(대만 담당) 공석, 로켓군 사령관 공석", 6826)] }),
          new TableRow({ children: [dataCell("전략적 시사점", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("군 최고 지휘부 구조적 공백으로 합동작전 능력 5년 이상 복구 소요", 6826)] }),
        ] }), emptyP(120),

        // ── Signal 2 ──
        h3("신호 2: 스탈린 논리(Stalin Logic)의 제도화 — 숙청의 자기강화적 순환"),
        new Table({ columnWidths: [2200, 6826], rows: [
          new TableRow({ children: [dataCell("분석 유형", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("학술 심층 분석 (학술 논문, 연구 보고서)", 6826)] }),
          new TableRow({ children: [dataCell("도메인", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("가치/이념(Spiritual)", 6826)] }),
          new TableRow({ children: [dataCell("중요도", 2200, { fill: C.highBg, tOpts: { bold: true } }), dataCell([boldTxt("높음", { color: "D4AC0D" }), txt(" (신뢰도 88점)")], 6826, { fill: C.highBg })] }),
          new TableRow({ children: [dataCell("핵심 내용", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("시진핑의 숙청은 '의심 → 숙청 → 더 큰 의심 → 더 많은 숙청'의 자기강화적 순환에 진입. 이 논리는 구조적으로 멈출 수 없음", 6826)] }),
          new TableRow({ children: [dataCell("전략적 시사점", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("향후 추가 숙청은 불가피하며, 체제의 장기적 취약성은 누적적으로 증가", 6826)] }),
        ] }), emptyP(120),

        // ── Signal 3 ──
        h3("신호 3: 인민해방군(People's Liberation Army) 전투력 구조적 약화 — 충성이 역량을 대체"),
        new Table({ columnWidths: [2200, 6826], rows: [
          new TableRow({ children: [dataCell("분석 유형", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("일반 환경스캐닝 (미디어, 싱크탱크, 정책 소스)", 6826)] }),
          new TableRow({ children: [dataCell("도메인", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("정치(Political)", 6826)] }),
          new TableRow({ children: [dataCell("중요도", 2200, { fill: C.highBg, tOpts: { bold: true } }), dataCell([boldTxt("높음", { color: "D4AC0D" }), txt(" (신뢰도 88점)")], 6826, { fill: C.highBg })] }),
          new TableRow({ children: [dataCell("핵심 내용", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("실전 경험 있는 마지막 장성(장유샤) 숙청. 영국 왕립합동군사연구소(Royal United Services Institute)는 '정치적 충성이 전투준비태세보다 우선'한다고 평가. 대만 침공 2027년 시한표 사실상 불가능", 6826)] }),
          new TableRow({ children: [dataCell("전략적 시사점", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("단기 안정과 중기 불확실성의 역설적 안보 환경 형성", 6826)] }),
        ] }), emptyP(120),

        // ── Signal 4 ──
        h3("신호 4: 역량-충성 트레이드오프(Competence-Loyalty Tradeoff) — 실증적 효율성 손실"),
        new Table({ columnWidths: [2200, 6826], rows: [
          new TableRow({ children: [dataCell("분석 유형", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("학술 심층 분석 (학술 논문, 연구 보고서)", 6826)] }),
          new TableRow({ children: [dataCell("도메인", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("정치(Political)", 6826)] }),
          new TableRow({ children: [dataCell("중요도", 2200, { fill: C.highBg, tOpts: { bold: true } }), dataCell([boldTxt("높음", { color: "D4AC0D" }), txt(" (신뢰도 83점)")], 6826, { fill: C.highBg })] }),
          new TableRow({ children: [dataCell("핵심 내용", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("1994-2017년 중국 관료 데이터 분석 결과, 충성 우선 인사는 효율성 손실을 비례적으로 증가시킴. 이론적 추측이 아닌 경험적 사실", 6826)] }),
          new TableRow({ children: [dataCell("전략적 시사점", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("인민해방군 전투력 저하는 예측 가능하며 구조적", 6826)] }),
        ] }), emptyP(120),

        // ── Signal 5 ──
        h3("신호 5: 로켓군 부패 — 핵전력 신뢰성 위기"),
        new Table({ columnWidths: [2200, 6826], rows: [
          new TableRow({ children: [dataCell("분석 유형", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("일반 환경스캐닝 (미디어, 싱크탱크, 정책 소스)", 6826)] }),
          new TableRow({ children: [dataCell("도메인", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("정치(Political)", 6826)] }),
          new TableRow({ children: [dataCell("중요도", 2200, { fill: C.highBg, tOpts: { bold: true } }), dataCell([boldTxt("높음", { color: "D4AC0D" }), txt(" (신뢰도 87점)")], 6826, { fill: C.highBg })] }),
          new TableRow({ children: [dataCell("핵심 내용", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("핵미사일 연료 대신 물 충전, 사일로 건설 사기, 핵기밀 유출. 핵탄두 600발 이상 보유에도 실제 가동률 불확실", 6826)] }),
          new TableRow({ children: [dataCell("전략적 시사점", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("핵 억제력의 양적 확대와 질적 신뢰성 간 심각한 괴리", 6826)] }),
        ] }), emptyP(160),

        h2("1.2 주요 변화 요약"),
        bullet([boldTxt("일반 환경스캐닝: "), txt("10개 신호 수집 (미디어, 싱크탱크, 정책기관 등 20개 이상 소스)")]),
        bullet([boldTxt("학술 심층 분석: "), txt("5개 학술 프레임워크 분석 (15건 논문 및 연구 보고서)")]),
        bullet([boldTxt("통합 신호 풀: "), txt("15개 (신뢰도 통합 순위 기준 선정)")]),
        bullet([boldTxt("주요 영향 도메인: "), txt("정치(Political) 8건, 가치/이념(Spiritual) 4건, 경제(Economic) 2건, 기술(Technological) 1건")]),
        emptyP(100),

        h2("1.3 교차 검증 하이라이트"),
        p([txt("일반 환경스캐닝(미디어/싱크탱크)과 학술 심층 분석의 결과가 강력하게 수렴하는 지점이 확인되었다:")]),
        bullet([boldTxt("상호 강화: "), txt("'충성 vs 역량 딜레마'가 미디어 현장 관찰과 학술 실증 연구에서 독립적으로 확인")]),
        bullet([boldTxt("학술 선행: "), txt("'스탈린 논리' 프레임워크가 2026년 1월 사건 이전에 이미 이론화되어 있었으며, 현실이 이론을 추종")]),
        bullet([boldTxt("미디어 선행: "), txt("로켓군 부패의 구체적 사례(물 충전 미사일)는 미디어에서 먼저 보도, 학술 분석이 후속")]),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 2. 분석의 전제와 방법론
        // ══════════════════════════════
        h1("2. 분석의 전제와 방법론"),
        h2("2.1 분석의 전제"),
        calloutBox([
          p([txt('본 보고서는 "시진핑이 이기고 있는가, 지고 있는가?"라는 질문을 의도적으로 보류한다. 대신, ', { size: 22 }), boldTxt("어떤 시나리오에서든 발생하는 확실한 결과", { size: 22 }), txt("에 초점을 맞춘다. 이 접근은 불확실한 미래 예측보다 현재 관찰 가능한 사실에 기반한 분석을 제공한다.", { size: 22 })], { spacing: { before: 100, after: 100 } }),
        ]), emptyP(120),

        h2("2.2 방법론"),
        numbered([boldTxt("이중 워크플로우 스캐닝: "), txt("20개 이상의 미디어/싱크탱크/정책 소스와 15건의 학술 논문/연구 보고서를 독립적으로 분석한 후 통합")], "num-method"),
        numbered([boldTxt("다차원 분류 체계: "), txt("사회(Social), 기술(Technological), 경제(Economic), 환경(Environmental), 정치(Political), 가치/이념(Spiritual) 등 6개 도메인으로 신호를 분류")], "num-method"),
        numbered([boldTxt("다차원 신뢰도 평가: "), txt("출처 신뢰도(Source Reliability), 증거 강도(Evidence Strength), 분류 확신도(Classification Confidence), 시간적 확신도(Temporal Confidence), 독창성 확신도(Distinctiveness Confidence), 영향 확신도(Impact Confidence) 등 6개 차원으로 신호별 신뢰도를 점수화")], "num-method"),
        numbered([boldTxt("삼각검증(Triangulation): "), txt("동일 현상에 대해 복수의 독립 소스와 방법론(관찰, 이론, 실증, 역사적 유추)을 적용하여 결론의 견고성 확보")], "num-method"),
        numbered([boldTxt("반론 검토: "), txt("각 핵심 결론에 대해 체계적으로 반론을 검토하고 재반박")], "num-method"),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 3. 확실한 결과 1
        // ══════════════════════════════
        h1("3. 확실한 결과 1: 중국 군대의 전력 약화"),

        h2("3.1 논증 구조"),
        new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: cb, width: { size: TW, type: WidthType.DXA }, shading: { fill: C.lightGray, type: ShadingType.CLEAR }, children: [
          p([boldTxt("대전제: "), txt("대규모 군부 숙청은 군사적 역량을 구조적으로 약화시킨다 (역사적 귀납 + 이론적 연역 + 실증 데이터)")], { spacing: { before: 80, after: 60 } }),
          p([boldTxt("소전제: "), txt("시진핑은 중국 역사상 문화대혁명 이후 최대 규모의 군부 숙청을 진행 중이다 (관찰적 사실)")], { spacing: { after: 60 } }),
          p([boldTxt("결  론: "), boldTxt("중국 인민해방군(People's Liberation Army)의 전력은 구조적으로 약화되고 있다 (논리적 필연)", { color: C.red })], { spacing: { after: 80 } }),
        ] })] })] }), emptyP(120),

        h2("3.2 근거 A: 지휘구조의 물리적 와해 (관찰적 사실)"),
        p([boldTxt("표: 중국 인민해방군 고위직 숙청 현황")], { spacing: { after: 80 } }),
        new Table({ columnWidths: [2200, 1600, 1600, 3626], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("직위", 2200), headerCell("숙청자", 1600), headerCell("시기", 1600), headerCell("결과", 3626)] }),
          new TableRow({ children: [dataCell("중앙군사위 부주석", 2200), dataCell("허웨이둥", 1600), dataCell("2025.10", 1600), dataCell("공석 후 장유샤가 유일 부주석", 3626)] }),
          new TableRow({ children: [dataCell("중앙군사위 부주석", 2200, { fill: C.lightGray }), dataCell("장유샤", 1600, { fill: C.lightGray }), dataCell("2026.01", 1600, { fill: C.lightGray }), dataCell("공석 (장성민만 잔류)", 3626, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("합참참모장", 2200), dataCell("류전리", 1600), dataCell("2026.01", 1600), dataCell("공석", 3626)] }),
          new TableRow({ children: [dataCell("국방부장", 2200, { fill: C.lightGray }), dataCell("리상푸", 1600, { fill: C.lightGray }), dataCell("2023", 1600, { fill: C.lightGray }), dataCell("교체됨", 3626, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("정치공작부장", 2200), dataCell("먀오화", 1600), dataCell("2024", 1600), dataCell("교체됨", 3626)] }),
          new TableRow({ children: [dataCell("동부전구사령관", 2200, { fill: C.lightGray }), dataCell("린샹양", 1600, { fill: C.lightGray }), dataCell("2026.01", 1600, { fill: C.lightGray }), dataCell("공석 (대만 작전 담당)", 3626, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("로켓군 사령관", 2200), dataCell("왕허우빈", 1600), dataCell("2026.01", 1600), dataCell("공석 (핵전력 담당)", 3626)] }),
          new TableRow({ children: [dataCell("무장경찰 사령관", 2200, { fill: C.lightGray }), dataCell("왕춘닝", 1600, { fill: C.lightGray }), dataCell("2026.01", 1600, { fill: C.lightGray }), dataCell("공석", 3626, { fill: C.lightGray })] }),
        ] }), emptyP(80),
        p([boldTxt("결과: "), txt("2022년 제20차 당대회에서 구성된 중앙군사위원회 7인 중 5인(71.4%)이 낙마했다. 이는 인민해방군 역사상 문화대혁명 시기를 제외하면 전례 없는 수준이다.")]), emptyP(100),

        h2("3.3 근거 B: 역량-충성 트레이드오프의 실증적 증거 (학술적 사실)"),
        p([txt("사이언스다이렉트(ScienceDirect) 게재 논문(1994-2017년 데이터)에 따르면:")]),
        bullet([txt("독재자가 내부 서클에 충성스러운 자를 배치하면 효율성 손실(efficiency loss)이 발생한다")]),
        bullet([txt("효율성 손실은 충성 중시 정도에 비례적으로 증가한다")]),
        bullet([txt("이 손실은 하위 관료층으로 확산될수록 가속된다")]),
        p([boldTxt("적용: "), txt("장유샤(실전 경험, 능력 기반 승진)에서 장성민(정치위원 출신, 실전 경험 없음)으로의 전환은 역량-충성 트레이드오프의 극단적 사례이다.")]), emptyP(100),

        h2("3.4 근거 C: 주인-대리인 문제(Principal-Agent Problem)의 악화 (이론적 근거)"),
        p([txt("케임브리지 대학 출판부(Cambridge Core) 논문(Kou Chien-wen)에 따르면:")]),
        bullet([txt('중앙군사위원회 주석 책임제는 "모든 정보가 1인에게 집중"되는 구조이다')]),
        bullet([txt("정보 과부하와 아첨 인센티브가 결합되면 정보 왜곡의 제도화가 발생한다")]),
        quoteBox('"시진핑이 \'인민해방군이 대만 해방 준비가 되었나?\'라고 묻는다면, 이제 어떤 장군도 감히 신중론을 제기하지 못할 것"'), emptyP(100),

        h2("3.5 근거 D: 역사적 선례 (귀납적 근거)"),
        p([boldTxt("표: 군부 숙청의 역사적 선례와 결과")], { spacing: { after: 80 } }),
        new Table({ columnWidths: [2600, 2000, 2200, 2226], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("사례", 2600), headerCell("숙청 규모", 2000), headerCell("군사적 결과", 2200), headerCell("회복 기간", 2226)] }),
          new TableRow({ children: [dataCell("스탈린 대숙청 (1936-38)", 2600), dataCell("장교단 2/3 제거", 2000), dataCell("독소전쟁 초기 대패", 2200), dataCell("5년 이상", 2226)] }),
          new TableRow({ children: [dataCell("마오쩌둥 문화대혁명 (1966-76)", 2600, { fill: C.lightGray }), dataCell("고위직 60%+ 숙청", 2000, { fill: C.lightGray }), dataCell("10년간 군 마비", 2200, { fill: C.lightGray }), dataCell("10년 이상", 2226, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("사담 후세인 (1979-2003)", 2600), dataCell("지속적 장교 숙청", 2000), dataCell("이라크전 참패", 2200), dataCell("회복 불가", 2226)] }),
          new TableRow({ children: [dataCell("시진핑 (2022-2026)", 2600, { fill: C.critBg }), dataCell("중앙군사위 71.4%", 2000, { fill: C.critBg }), dataCell("진행 중", 2200, { fill: C.critBg }), dataCell("최소 5년(추정)", 2226, { fill: C.critBg })] }),
        ] }), emptyP(100),

        h2("3.6 근거 E: 방위산업 연쇄 타격 (경제적 사실)"),
        bullet([boldTxt("중국북방공업집단(NORINCO, China North Industries Group): "), txt("매출 31% 감소")]),
        bullet([boldTxt("중국항공공업집단(AVIC, Aviation Industry Corporation of China): "), txt("군용기 납품 지연")]),
        bullet([boldTxt("중국항천과기집단(CASC, China Aerospace Science and Technology): "), txt("미사일 생산 차질")]),
        bullet([boldTxt("중국핵공업집단(CNNC, China National Nuclear Corporation): "), txt("수장 활동 중단 (2025년 1월부터)")]),
        bullet([boldTxt("핵미사일 연료 대신 물 충전 사건 적발")]), emptyP(100),

        h2("3.7 반론 검토 및 재반박"),
        p([boldTxt('반론 1: "숙청으로 부패를 척결하면 장기적으로 군이 더 강해진다"'), txt(" (미국 국방부(Pentagon) 2025 보고서 일부)")]),
        p([boldTxt("재반박: ", { color: C.accent }), txt('이론적으로 가능하나, 역사적 사례에서 "숙청 후 장기적 강화"가 실현된 사례는 극히 드물다. 스탈린의 숙청은 결국 소련군을 약화시켰으며, 강화는 숙청된 장교들의 복권과 새로운 지도부 양성을 통해서만 가능했다. 시진핑은 복권 의사를 보이지 않고 있다.')]), emptyP(60),
        p([boldTxt('반론 2: "인민해방군의 중간 지휘관 이하 전력은 숙청의 영향을 받지 않는다"'), txt(" (아시아소사이어티 정책연구소(Asia Society Policy Institute)의 Neil Thomas)")]),
        p([boldTxt("재반박: ", { color: C.accent }), txt("부분적으로 타당하나, 합동작전은 전략적 지휘부의 조율 능력에 절대적으로 의존한다. 대만 침공과 같은 복합 작전에서 중간 지휘관의 역량은 전략적 지휘부 없이는 발휘될 수 없다.")]), emptyP(60),
        p([boldTxt('반론 3: "핵전력은 양적으로 계속 확대 중이므로 약화가 아니다"')]),
        p([boldTxt("재반박: ", { color: C.accent }), txt('양적 확대와 질적 신뢰성은 별개의 차원이다. 미사일 연료 대신 물을 채운 사례가 상징하듯, 양적 규모가 전투력을 보장하지 않는다. 미국 국방부 보고서 자체가 "지도부의 자국 핵전력에 대한 신뢰 저하"를 언급했다.')]), emptyP(100),

        h2("3.8 소결"),
        calloutBox([
          p([boldTxt("중국 군대의 전력 약화는 다음에 의해 다각적으로 확인된다:")], { spacing: { before: 100, after: 60 } }),
          bullet([boldTxt("관찰적 사실: "), txt("중앙군사위원회 와해, 핵심 직위 공석")]),
          bullet([boldTxt("이론적 필연: "), txt("역량-충성 트레이드오프, 주인-대리인 문제")]),
          bullet([boldTxt("역사적 귀납: "), txt("스탈린, 마오쩌둥, 사담 후세인의 선례")]),
          bullet([boldTxt("경제적 증거: "), txt("방위산업 실적 급락")]),
          p([boldTxt("시진핑이 승리하면 충성스럽지만 무능한 군이 되고, 실패하면 분열된 군이 된다. 어느 경우에도 군사적 역량은 약화된다.", { color: C.red })], { spacing: { before: 80, after: 100 } }),
        ], C.navy),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 4. 확실한 결과 2
        // ══════════════════════════════
        h1("4. 확실한 결과 2: 중국 공산당 내 신뢰 및 충성심 약화"),

        h2("4.1 논증 구조"),
        new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: cb, width: { size: TW, type: WidthType.DXA }, shading: { fill: C.lightGray, type: ShadingType.CLEAR }, children: [
          p([boldTxt("대전제: "), txt("엘리트의 안전 보장 없이는 진정한 충성이 불가능하며, 두려움에 기반한 복종은 충성의 대체재가 아니다 (정치학적 명제 + 심리학적 명제)")], { spacing: { before: 80, after: 60 } }),
          p([boldTxt("소전제: "), txt('시진핑은 자신의 최측근(태자당 동지, 직접 발탁 장성)까지 숙청하여 당 내 "안전지대 없음"을 입증했다 (관찰적 사실)')], { spacing: { after: 60 } }),
          p([boldTxt("결  론: "), boldTxt("중국 공산당(Chinese Communist Party) 내부의 진정한 충성심과 제도적 신뢰가 구조적으로 약화되고 있다 (논리적 필연)", { color: C.red })], { spacing: { after: 80 } }),
        ] })] })] }), emptyP(120),

        h2('4.2 근거 A: "안전지대 없음"의 실증 (관찰적 사실)'),
        p([txt("장유샤는 시진핑에게 있어 "), boldTxt("가장 신뢰할 수 있는 인물"), txt("이었다:")]),
        bullet([txt("두 사람의 아버지는 혁명 동지 (1세대 유대)")]),
        bullet([txt("어린 시절부터 함께 성장 (개인적 유대)")]),
        bullet([txt("시진핑이 2022년 정년을 넘겨서까지 유임시킨 유일한 장성 (정치적 유대)")]),
        bullet([txt("중앙군사위원회에서 시진핑 다음 서열 2위 (제도적 유대)")]),
        p([txt("이러한 인물마저 숙청되었다는 사실은, 브루킹스 연구소(Brookings Institution) 전문가의 말대로, "), boldTxt('"당 내에 안전지대는 없다(there is no safe zone)"', { color: C.red }), txt("는 것을 모든 엘리트에게 증명했다.")]), emptyP(100),

        h2("4.3 근거 B: 스탈린 논리의 자기강화적 순환 (이론적 근거)"),
        p([txt("아시아소사이어티 정책연구소(Asia Society Policy Institute) 분석에 따른 순환 구조:")]),
        numbered([txt("지도자가 배신을 의심한다")], "num-stalin"),
        numbered([txt("일부를 숙청한다")], "num-stalin"),
        numbered([txt('"이들이 배신했다면 나머지는 어떻게 믿을 수 있나?"')], "num-stalin"),
        numbered([txt("더 많은 사람을 숙청한다")], "num-stalin"),
        numbered([boldTxt("3단계로 돌아간다 (무한 순환)")], "num-stalin"),
        p([txt("이 순환은 "), boldTxt("논리적으로 멈출 수 없다"), txt(". 숙청이 더 많은 의심을 낳고, 의심이 더 많은 숙청을 낳기 때문이다. 시진핑이 이 순환에 진입한 것은 2023년(리상푸 숙청)으로 볼 수 있으며, 2026년 장유샤 숙청은 순환이 가속화되고 있음을 보여준다.")]), emptyP(100),

        h2("4.4 근거 C: 엘리트 결속의 제도적 기반 파괴 (학술적 근거)"),
        p([txt("캘리포니아 대학교 샌디에이고(UC San Diego) 연구에 따르면:")]),
        bullet([txt('권위주의 체제에서 "패배자의 복지를 보장하는 신뢰할 수 있는 제도"가 내부 갈등을 줄이는 핵심이다')]),
        bullet([txt("시진핑은 이러한 제도적 안전망을 완전히 해체했다: 숙청된 엘리트는 투옥, 재산 몰수, 사회적 파멸에 직면한다")]),
        bullet([txt('제도적 보장 없이 "상호 필요"만으로는 안정 유지가 가능하나, 그것도 독재자가 부하의 "고유한 기술(unique skills)"을 필요로 할 때만 해당한다')]),
        p([boldTxt("적용: "), txt('시진핑이 장유샤의 "고유한 기술"(실전 경험, 군사적 전문성)을 필요로 하지 않는다고 판단한 것은, 역량보다 충성을 절대적으로 우선한다는 의미이다. 이는 다른 모든 엘리트에게 "당신의 능력은 당신을 보호하지 않는다"는 메시지를 전달한다.')]), emptyP(100),

        h2("4.5 근거 D: 두려움의 역설 — 복종은 충성이 아니다 (심리학적 근거)"),
        p([boldTxt("핵심 구분:")]),
        bullet([boldTxt("복종(obedience): "), txt("외부 강제에 의한 행동 순응. 감시가 사라지면 행동이 변한다")]),
        bullet([boldTxt("충성(loyalty): "), txt("내면화된 헌신. 감시 없이도 행동이 일관된다")]),
        p([txt("숙청에 의해 생산되는 것은 "), boldTxt("복종"), txt("이지 "), boldTxt("충성"), txt("이 아니다.")]),
        bullet([txt("복종하는 관료는 위험 회피(risk aversion), 책임 전가(buck-passing), 소극적 저항(passive resistance)을 통해 체제의 효율성을 저하시킨다")]),
        bullet([txt('"관료적 수동성(bureaucratic passivity)"은 권위주의 체제에서 숙청의 가장 보편적인 부작용이다')]), emptyP(100),

        h2('4.6 근거 E: "집단지도체제" 회귀 징후 (관찰적 사실)'),
        p([txt("비전타임스(Vision Times) 보도에 따르면:")]),
        bullet([txt('인민해방군 기관지(PLA Daily)에 "집단지도(collective leadership)"와 "민주집중제(democratic centralism)"를 강조하는 기사가 게재되었다')]),
        bullet([txt("이는 시진핑의 1인 통제와 직접적으로 모순된다")]),
        bullet([txt("2025년 6월 30일, 정치국 산하 소조/위원회의 결정을 중앙위원회에 제출하도록 하는 규정이 도입되었다")]),
        p([txt('이러한 제도적 움직임은 당 내부에서 "1인 체제에 대한 조용한 저항"이 존재함을 시사한다.')]), emptyP(100),

        h2("4.7 근거 F: 역사적 선례 (귀납적 근거)"),
        p([boldTxt("표: 정치적 숙청이 당내 신뢰에 미친 역사적 영향")], { spacing: { after: 80 } }),
        new Table({ columnWidths: [2000, 2200, 2200, 2626], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("사례", 2000), headerCell("숙청 대상", 2200), headerCell("신뢰 영향", 2200), headerCell("장기적 결과", 2626)] }),
          new TableRow({ children: [dataCell("스탈린 대숙청", 2000), dataCell("혁명 동지, 군 원수", 2200), dataCell("전면적 불신", 2200), dataCell("당의 도구화, 소련 장기 경직화", 2626)] }),
          new TableRow({ children: [dataCell("마오 문화대혁명", 2000, { fill: C.lightGray }), dataCell("류사오치, 덩샤오핑", 2200, { fill: C.lightGray }), dataCell("당 기능 마비", 2200, { fill: C.lightGray }), dataCell("마오 사후 즉시 노선 전환", 2626, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("린뱌오 사건", 2000), dataCell("후계자 + 군 수천명", 2200), dataCell("군-당 관계 근본적 훼손", 2200), dataCell("덩샤오핑에 의한 군 재건 필요", 2626)] }),
          new TableRow({ children: [dataCell("천안문 1989", 2000, { fill: C.lightGray }), dataCell("자오쯔양 + 개혁파", 2200, { fill: C.lightGray }), dataCell("당내 자유화 세력 소멸", 2200, { fill: C.lightGray }), dataCell("30년간 정치 개혁 봉쇄", 2626, { fill: C.lightGray })] }),
        ] }), emptyP(100),

        h2("4.8 반론 검토 및 재반박"),
        p([boldTxt('반론 1: "트럼프도 시진핑이 \'중국의 보스이며 존경받고 있다\'고 인정했다"')]),
        p([boldTxt("재반박: ", { color: C.accent }), txt('외부 관찰자(특히 외국 정상)의 인정은 내부 충성심의 지표가 아니다. 스탈린도 외부에서는 "강력한 지도자"로 인식되었으나, 내부적으로는 편집증적 불신에 시달렸다. 외부의 인정은 오히려 독재자의 환상을 강화할 수 있다.')]), emptyP(60),
        p([boldTxt('반론 2: "인민해방군에서 숙청에 대한 공식적 저항이 전혀 없으므로 통제가 유효하다"')]),
        p([boldTxt("재반박: ", { color: C.accent }), txt("저항의 부재는 충성의 증거가 아니라 두려움의 증거일 수 있다. 1989년 천안문 사건에서 쉬친셴을 아무도 지지하지 않은 것은 충성 때문이 아니라 보복에 대한 두려움 때문이었다. 진정한 충성은 위기 시에만 검증되며, 평시의 복종은 충성의 대리 지표(proxy)가 될 수 없다.")]), emptyP(60),
        p([boldTxt('반론 3: "반부패 캠페인은 당의 정당성을 강화한다"')]),
        p([boldTxt("재반박: ", { color: C.accent }), txt('일반 대중 수준에서는 일부 타당하나, 엘리트 수준에서는 반대 효과가 있다. "누구든 숙청될 수 있다"는 인식은 엘리트의 체제 이탈 동기를 장기적으로 강화한다. 소련 말기 엘리트 이탈이 체제 붕괴의 핵심 메커니즘이었음을 상기해야 한다.')]), emptyP(100),

        h2("4.9 소결"),
        calloutBox([
          p([boldTxt("중국 공산당 내 신뢰 및 충성심의 약화는 다음에 의해 다각적으로 확인된다:")], { spacing: { before: 100, after: 60 } }),
          bullet([boldTxt("관찰적 사실: "), txt('최측근 숙청, "안전지대 없음" 입증')]),
          bullet([boldTxt("이론적 필연: "), txt("스탈린 논리의 자기강화적 순환")]),
          bullet([boldTxt("심리학적 명제: "), txt("두려움에 기반한 복종은 충성이 아님")]),
          bullet([boldTxt("역사적 귀납: "), txt("대숙청은 예외 없이 내부 신뢰를 파괴")]),
          bullet([boldTxt("제도적 증거: "), txt('"집단지도체제" 회귀 징후')]),
          p([boldTxt('시진핑이 승리하면 "진정한 충성 없는 절대 권력"이 되고, 실패하면 분열된 당이 된다. 어느 경우에도 제도적 신뢰는 약화된다.', { color: C.red })], { spacing: { before: 80, after: 100 } }),
        ], C.navy),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 5. 기존 신호 업데이트
        // ══════════════════════════════
        h1("5. 기존 신호 업데이트"),
        h2("5.1 강화 추세"),
        bullet([boldTxt("미중 전략적 경쟁 구조화: "), txt('군부 숙청이 미중 관계에 새로운 불확실성 변수를 추가했다. 미국 국방부(Pentagon) 2025 보고서는 "조직적 혼란(organizational churn)"이 인민해방군 현대화 모멘텀을 가리지 않아야 한다고 경고하면서도, 단기 전투준비태세 비용을 인정했다')]),
        bullet([boldTxt("글로벌 권위주의의 내적 취약성: "), txt("민주주의 다양성 연구소(Varieties of Democracy Institute, V-Dem) 2025 보고서에 따르면 세계적 자유민주주의 수준이 1985년 수준으로 회귀했다. 그러나 중국의 사례는 권위주의 체제의 강화가 동시에 취약화를 수반함을 보여준다")]),
        bullet([boldTxt("핵 불확실성 증대: "), txt("중국의 핵전력 양적 확대(600발 이상)와 질적 불확실성(부패, 지휘부 공백)의 동시 진행은 글로벌 핵 안정성에 새로운 변수이다")]), emptyP(100),

        h2("5.2 약화 추세"),
        bullet([boldTxt("중국 군사 현대화 2027 목표: "), txt("미국 국방부조차 인정하는 단기 전투준비태세 비용. 합동작전 모델 미완성, 지휘부 전면 교체. 2027년 목표 사실상 불가능")]),
        bullet([boldTxt("대만 조기 무력통일 가능성: "), txt('단기적으로 크게 약화. "의도적 전쟁 가능성 감소" — 그러나 "우발적 충돌 가능성 증가"라는 역설적 상황')]),
        bullet([boldTxt("중국 공산당의 제도적 거버넌스 역량: "), txt('1인 체제 심화로 제도적 의사결정 품질 저하. "집단지도체제"의 형식적 회귀 시도가 있으나 실효성 불분명')]), emptyP(100),

        h2("5.3 신호 상태 요약"),
        new Table({ columnWidths: [2200, 1800, 2800, 2226], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("신호", 2200), headerCell("이전 상태", 1800), headerCell("현재 상태", 2800), headerCell("변화 방향", 2226)] }),
          new TableRow({ children: [dataCell("중국 군사 현대화", 2200), dataCell("가속", 1800), dataCell("교란/지연", 2800), dataCell("약화", 2226, { tOpts: { color: C.red } })] }),
          new TableRow({ children: [dataCell("대만해협 긴장", 2200, { fill: C.lightGray }), dataCell("고조", 1800, { fill: C.lightGray }), dataCell("복합적(의도 감소, 우발 증가)", 2800, { fill: C.lightGray }), dataCell("질적 변화", 2226, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("시진핑 1인 체제", 2200), dataCell("공고화", 1800), dataCell("공고화+취약화 동시", 2800), dataCell("역설적", 2226)] }),
          new TableRow({ children: [dataCell("중국 경제", 2200, { fill: C.lightGray }), dataCell("둔화", 1800, { fill: C.lightGray }), dataCell("복합 불안(경제+정치 동시)", 2800, { fill: C.lightGray }), dataCell("악화", 2226, { fill: C.lightGray, tOpts: { color: C.red } })] }),
          new TableRow({ children: [dataCell("핵전력 확대", 2200), dataCell("가속", 1800), dataCell("양적 확대+질적 불확실", 2800), dataCell("이중적", 2226)] }),
          new TableRow({ children: [dataCell("미중 경쟁", 2200, { fill: C.lightGray }), dataCell("구조화", 1800, { fill: C.lightGray }), dataCell("군사 차원 불확실성 추가", 2800, { fill: C.lightGray }), dataCell("복잡화", 2226, { fill: C.lightGray })] }),
        ] }),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 6. 패턴 및 연결고리
        // ══════════════════════════════
        h1("6. 패턴 및 연결고리"),
        h2("6.1 신호 간 교차 영향"),
        p([boldTxt("인과관계 구조:")]),
        new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: cb, width: { size: TW, type: WidthType.DXA }, shading: { fill: C.lightGray, type: ShadingType.CLEAR }, children: [
          p([txt("중앙군사위 와해  →  인민해방군 전투력 약화  →  대만 침공 시한 지연 + 합동작전 능력 약화", { font: "Courier New", size: 20 })], { spacing: { before: 80, after: 40 } }),
          p([txt("중앙군사위 와해  →  당내 신뢰 약화  →  관료적 수동성 + 정보 왜곡 제도화  →  우발적 충돌 위험", { font: "Courier New", size: 20 })], { spacing: { after: 40 } }),
          p([txt("중앙군사위 와해  →  방위산업 타격  →  군사 현대화 지연", { font: "Courier New", size: 20 })], { spacing: { after: 40 } }),
          p([txt("경제 복합 불안  →  체제 불안정성  →  대외 모험주의 유발 가능", { font: "Courier New", size: 20 })], { spacing: { after: 80 } }),
        ] })] })] }), emptyP(120),

        h2("6.2 떠오르는 테마"),
        h3('테마 1: "강해질수록 약해지는" 역설 (Paradox of Strengthening)'),
        p([txt("시진핑의 권력이 공고해질수록 체제의 실질적 역량은 약화된다. 이는 권력 집중의 구조적 역설이며, 역사적으로 스탈린, 마오쩌둥, 사담 후세인 모두 이 역설에 빠졌다.")]),
        h3('테마 2: "단기 안정, 중기 위험" (Short-Term Stability, Medium-Term Risk)'),
        p([txt("대규모 군사작전(대만 침공) 가능성은 단기적으로 감소하나, 구조적 불확실성은 증가한다. 이는 전통적 억제 전략의 유효성에 의문을 제기하며, 새로운 안보 패러다임의 필요성을 시사한다.")]),
        h3('테마 3: "복종의 함정" (Obedience Trap)'),
        p([txt('두려움에 기반한 복종은 충성의 대체재가 아니며, 오히려 정보 왜곡, 위험 회피, 혁신 저해를 통해 체제를 장기적으로 약화시킨다. 이것이 "독재자의 딜레마"의 핵심이다.')]), emptyP(100),

        h2("6.3 교차 검증 분석"),
        h3("상호 강화 신호"),
        new Table({ columnWidths: [3200, 3826, 2000], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("일반 스캐닝 관찰", 3200), headerCell("학술 심층 분석 이론", 3826), headerCell("수렴도", 2000)] }),
          new TableRow({ children: [dataCell("중앙군사위 71.4% 숙청", 3200), dataCell("스탈린 논리의 자기강화적 순환", 3826), dataCell([boldTxt("강력", { color: "27AE60" })], 2000)] }),
          new TableRow({ children: [dataCell("충성 우선 인사 (영국 왕립합동군사연구소 분석)", 3200, { fill: C.lightGray }), dataCell("역량-충성 트레이드오프 실증 (사이언스다이렉트)", 3826, { fill: C.lightGray }), dataCell([boldTxt("강력", { color: "27AE60" })], 2000, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("장유샤(최측근) 숙청", 3200), dataCell("엘리트 숙청 비용-편익 이론 (영국정치학저널)", 3826), dataCell([boldTxt("강력", { color: "27AE60" })], 2000)] }),
          new TableRow({ children: [dataCell('"안전지대 없음" 메시지', 3200, { fill: C.lightGray }), dataCell("엘리트 결속 이론 (캘리포니아대 샌디에이고)", 3826, { fill: C.lightGray }), dataCell([boldTxt("강력", { color: "27AE60" })], 2000, { fill: C.lightGray })] }),
        ] }), emptyP(100),

        h3("학술 선행 신호"),
        bullet([boldTxt("역량-충성 트레이드오프: "), txt("2022년 사이언스다이렉트(ScienceDirect) 논문에서 이미 이론화. 2026년 현실이 이론을 추종")]),
        bullet([boldTxt("주인-대리인 문제: "), txt("2017년 차이나 쿼털리(The China Quarterly) 논문의 예측이 현재 정확하게 실현")]),
        bullet([boldTxt("엘리트 숙청 패턴: "), txt('영국정치학저널(British Journal of Political Science) 논문의 "1세대 동지 우선 숙청" 예측이 장유샤 사례에서 확인')]), emptyP(80),

        h3("미디어 선행 신호"),
        bullet([boldTxt("로켓군 구체적 부패 사례: "), txt("CNN, Technology.org에서 먼저 보도 (물 충전 미사일, 사일로 사기)")]),
        bullet([boldTxt("방위산업 실적 하락: "), txt("경제 전문지에서 먼저 보도, 학술 분석이 후속")]),
        bullet([boldTxt('"집단지도체제" 회귀 징후: '), txt("비전타임스(Vision Times), 인민해방군 기관지 분석에서 먼저 포착")]),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 7. 전략적 시사점
        // ══════════════════════════════
        h1("7. 전략적 시사점"),
        h2("7.1 즉시 조치 필요 (0-6개월)"),
        numbered([boldTxt("대만해협 우발적 충돌 대비 강화: "), txt("의도적 전쟁 가능성 감소와 무관하게, 중하급 장교의 충성 입증 행동에 의한 우발적 확전 위험 증가. 미중 군사 핫라인 가동 상태 확인 필수")], "num-imm"),
        numbered([boldTxt("중국 군부 인사 동향 실시간 모니터링: "), txt("중앙군사위원회 재충원 패턴, 신임 사령관 임명, 추가 숙청 여부가 향후 6개월간 핵심 지표")], "num-imm"),
        numbered([boldTxt("한국 안보 포스처 재검토: "), txt("중국 북부/동부전구 지휘부 공백 기간의 안보 환경 변화에 대한 대응 방안 수립")], "num-imm"),
        numbered([boldTxt("경제적 파급효과 대비: "), txt("중국 방위산업 혼란이 글로벌 공급망에 미치는 영향 평가, 한국 방산 수출 기회 포착")], "num-imm"), emptyP(100),

        h2("7.2 중기 모니터링 (6-18개월)"),
        numbered([boldTxt("2027년 목표의 현실적 재평가: "), txt('인민해방군의 "2027년 대만 침공 능력 확보" 목표가 사실상 불가능해진 상황에서, 시진핑이 새로운 시한을 설정하는지 주시')], "num-mid"),
        numbered([boldTxt("당내 권력 역학 변화: "), txt('2027년 제21차 당대회를 앞둔 후계 구도 변화, "집단지도체제" 복원 논의 심화 여부')], "num-mid"),
        numbered([boldTxt("핵전력 신뢰성 평가: "), txt("로켓군 재건 과정, 핵 경계태세 변화, 신형 미사일 시험 동향")], "num-mid"),
        numbered([boldTxt("경제-정치 복합 불안의 진화: "), txt("디플레이션, 부동산 위기, 인구감소가 정치적 불안정과 상호작용하는 패턴")], "num-mid"), emptyP(100),

        h2("7.3 모니터링 강화 필요 영역"),
        bullet([boldTxt("인민해방군 기관지 논조 변화: "), txt('"집단지도"와 "1인 통제" 사이의 미묘한 수사적 변화')]),
        bullet([boldTxt("중국 군 훈련 패턴: "), txt("대규모 합동훈련 감소/증가 여부")]),
        bullet([boldTxt("엘리트 해외 이탈 데이터: "), txt("고위급 관료/장교의 해외 이주 또는 자산 이전 동향")]),
        bullet([boldTxt("미중 군사 대화 채널: "), txt("군사 핫라인 가동 여부, 고위급 군사 대화 재개 여부")]),
        bullet([boldTxt("아시아 금융시장 반응: "), txt("중국 관련 정치적 리스크 프리미엄 변화")]),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 8. 시나리오
        // ══════════════════════════════
        h1("8. 전개 가능 시나리오"),
        h2('8.1 시나리오 A: "공고한 고립" (Entrenched Isolation) — 확률 45%'),
        calloutBox([p([txt('시진핑이 중앙군사위원회를 충성파로 재충원하고 단기적 안정을 회복하나, 체제의 실질적 역량은 계속 저하된다. "강력하지만 고립된" 시진핑이 정보 왜곡 속에서 점진적으로 전략적 오판 위험이 증가한다. 대만 침공은 2030년 이후로 연기되나, 국지적 군사 도발은 증가한다.')], { spacing: { before: 80, after: 80 } })]), emptyP(100),

        h2('8.2 시나리오 B: "조용한 재조정" (Silent Recalibration) — 확률 30%'),
        calloutBox([p([txt('당 내부의 "조용한 저항"이 점진적으로 집단지도체제 복원 방향으로 작용한다. 2027년 당대회를 앞두고 일정한 제도적 재조정이 이루어지며, 숙청의 속도가 감소한다. 군사적 역량은 5-7년에 걸쳐 점진적으로 회복된다.')], { spacing: { before: 80, after: 80 } })], "27AE60", "EAFAF1"), emptyP(100),

        h2('8.3 시나리오 C: "가속적 불안정" (Accelerating Instability) — 확률 20%'),
        calloutBox([p([txt('경제 위기와 정치적 숙청이 상호 강화하면서 체제 불안정이 가속화된다. 추가 고위급 숙청이 이어지고, 엘리트 이탈이 증가하며, 대외적으로 "전환 공격(diversionary war)" 유혹이 증가한다. '), boldTxt("가장 위험한 시나리오이다.", { color: C.red })], { spacing: { before: 80, after: 80 } })], C.red, C.critBg), emptyP(100),

        h2('8.4 시나리오 D: "전략적 전환" (Strategic Pivot) — 확률 5%'),
        calloutBox([p([txt("시진핑이 숙청의 한계를 인식하고 제도적 복원을 선택한다. 숙청된 일부 장교의 복권, 중앙군사위원회 제도적 재건, 집단지도 요소 부분 복원. 역사적으로 마오쩌둥이 문화대혁명 후 덩샤오핑을 복권시킨 사례가 있으나, 시진핑은 이 방향의 의사를 전혀 보이지 않고 있어 확률 극히 낮다.")], { spacing: { before: 80, after: 80 } })], C.gray, C.lightGray),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 9. 신뢰도 분석
        // ══════════════════════════════
        h1("9. 신뢰도 분석"),
        h2("9.1 신호 신뢰도 등급 분포"),
        new Table({ columnWidths: [3500, 2763, 2763], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("등급", 3500), headerCell("신호 수", 2763), headerCell("비율", 2763)] }),
          new TableRow({ children: [dataCell("A등급 (90점 이상)", 3500), dataCell("1", 2763, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("6.7%", 2763, { pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("B등급 (70-89점)", 3500, { fill: C.lightGray }), dataCell("13", 2763, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("86.7%", 2763, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("C등급 (50-69점)", 3500), dataCell("1", 2763, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("6.7%", 2763, { pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("D등급 (0-49점)", 3500, { fill: C.lightGray }), dataCell("0", 2763, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("0%", 2763, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } })] }),
        ] }), emptyP(120),

        h2("9.2 분석 유형별 신뢰도 비교"),
        new Table({ columnWidths: [2200, 2275, 2276, 2275], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("지표", 2200), headerCell("일반 스캐닝", 2275), headerCell("학술 심층 분석", 2276), headerCell("통합", 2275)] }),
          new TableRow({ children: [dataCell("평균 신뢰도", 2200, { tOpts: { bold: true } }), dataCell("83.6점", 2275, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("83.6점", 2276, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("83.6점", 2275, { pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("최고 신뢰도", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("92점", 2275, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("88점", 2276, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("92점", 2275, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("최저 신뢰도", 2200, { tOpts: { bold: true } }), dataCell("76점", 2275, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("80점", 2276, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("76점", 2275, { pOpts: { alignment: AlignmentType.CENTER } })] }),
        ] }), emptyP(120),

        h2("9.3 6개 차원별 평균 분석"),
        new Table({ columnWidths: [2800, 1000, 2613, 2613], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("평가 차원", 2800), headerCell("평균", 1000), headerCell("주요 강점", 2613), headerCell("주요 약점", 2613)] }),
          new TableRow({ children: [dataCell("출처 신뢰도(Source Reliability)", 2800), dataCell("82점", 1000, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("주요 싱크탱크 및 학술지", 2613), dataCell("중국 내부 소스 접근 제한", 2613)] }),
          new TableRow({ children: [dataCell("증거 강도(Evidence Strength)", 2800, { fill: C.lightGray }), dataCell("80점", 1000, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("정량 데이터 다수", 2613, { fill: C.lightGray }), dataCell("일부 정성적 판단 의존", 2613, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("분류 확신도(Classification Confidence)", 2800), dataCell("88점", 1000, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("정치 영역 분류 명확", 2613), dataCell("가치/이념 영역 경계 모호", 2613)] }),
          new TableRow({ children: [dataCell("시간적 확신도(Temporal Confidence)", 2800, { fill: C.lightGray }), dataCell("90점", 1000, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("2026년 1월 사건 기반", 2613, { fill: C.lightGray }), dataCell("장기 전망은 불확실", 2613, { fill: C.lightGray })] }),
          new TableRow({ children: [dataCell("독창성 확신도(Distinctiveness Confidence)", 2800), dataCell("78점", 1000, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("통합 분석의 독창성", 2613), dataCell("개별 사실은 기보도", 2613)] }),
          new TableRow({ children: [dataCell("영향 확신도(Impact Confidence)", 2800, { fill: C.lightGray }), dataCell("82점", 1000, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("교차 영향 분석", 2613, { fill: C.lightGray }), dataCell("장기 영향 추정치 변동성", 2613, { fill: C.lightGray })] }),
        ] }),

        new Paragraph({ children: [new PageBreak()] }),

        // ══════════════════════════════
        // 10. 부록
        // ══════════════════════════════
        h1("10. 부록"),
        h2("10.1 전체 신호 목록"),
        p([boldTxt("표: 통합 신호 목록 (신뢰도 순위)")], { spacing: { after: 80 } }),
        new Table({ columnWidths: [500, 1100, 5226, 700, 1500], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("#", 500), headerCell("분석 유형", 1100), headerCell("신호", 5226), headerCell("신뢰도", 700), headerCell("도메인", 1500)] }),
          ...[
            ["1", "일반", "중앙군사위원회 7인 체제 사실상 와해", "92", "정치"],
            ["2", "학술", "스탈린 논리의 제도화", "88", "가치/이념"],
            ["3", "일반", "인민해방군 전투준비태세 구조적 약화", "88", "정치"],
            ["4", "일반", "로켓군 부패 — 핵전력 신뢰성 위기", "87", "정치"],
            ["5", "일반", "공산당 내부 신뢰 체계 근본적 훼손", "85", "가치/이념"],
            ["6", "일반", "대만해협 단기 안정, 중기 불확실성", "85", "정치"],
            ["7", "학술", "공산당-인민해방군 주인-대리인 문제 심화", "85", "정치"],
            ["8", "일반", "역사적 전례 — 문화대혁명과의 유사성", "83", "정치"],
            ["9", "학술", "역량-충성 트레이드오프 실증", "83", "정치"],
            ["10", "일반", "방위산업 구조적 타격", "82", "경제"],
            ["11", "학술", "엘리트 숙청 비용-편익 분석", "82", "정치"],
            ["12", "일반", '"독재자의 딜레마" — 정보 왜곡 제도화', "80", "가치/이념"],
            ["13", "학술", "엘리트 결속과 권위주의 안정성", "80", "정치"],
            ["14", "일반", "중국 경제 복합 불안과 군부 숙청 동시 진행", "78", "경제"],
            ["15", "일반", "한반도 및 동아시아 안보 불확실성 증폭", "76", "정치"],
          ].map((r, i) => new TableRow({ children: [
            dataCell(r[0], 500, { pOpts: { alignment: AlignmentType.CENTER }, fill: i % 2 === 1 ? C.lightGray : undefined }),
            dataCell(r[1], 1100, { pOpts: { alignment: AlignmentType.CENTER }, fill: i % 2 === 1 ? C.lightGray : undefined }),
            dataCell(r[2], 5226, { fill: i % 2 === 1 ? C.lightGray : undefined }),
            dataCell(r[3], 700, { pOpts: { alignment: AlignmentType.CENTER }, fill: i % 2 === 1 ? C.lightGray : undefined, tOpts: { bold: true } }),
            dataCell(r[4], 1500, { pOpts: { alignment: AlignmentType.CENTER }, fill: i % 2 === 1 ? C.lightGray : undefined }),
          ] }))
        ] }), emptyP(120),

        h2("10.2 출처 목록"),
        h3("일반 환경스캐닝 주요 출처"),
        ...[ 'Foreign Affairs — "The Unsettling Implications of Xi\'s Military Purge"',
          'NBC News — "Purge of top Chinese general throws military into turmoil"',
          'The Diplomat — "The Purge of Zhang Youxia and Liu Zhenli"',
          'American Enterprise Institute — "Xi Jinping\'s Military Purges Leave Him Increasingly Powerful but Isolated"',
          'CBC News — "Xi Jinping\'s purge of China\'s top general spells uncertainty"',
          'Center for Naval Analyses — "Military Purges at China\'s Fourth Plenum Have Implications for Readiness"',
          'Bloomberg — "Xi\'s Military Purges Raise Questions Over China\'s PLA Readiness"',
          'GZERO Media (Ian Bremmer) — "What to know about China\'s military purges"',
          '미국 국방부(Pentagon) 2025 중국 군사력 보고서(China Military Power Report)',
          '미국 핵과학자 회보(Bulletin of the Atomic Scientists) — "Chinese nuclear weapons, 2025"',
          'CNN — 위성 분석 기반 미사일 생산 확대 보도',
          'War on the Rocks — "China\'s Military Advancing Amid Churn"',
          '미국 외교관계위원회(Council on Foreign Relations) — "Six Takeaways From the Pentagon\'s Report on China\'s Military"',
          '서울신문, 한국일보, 시사저널, 글로벌이코노믹, 아주경제',
        ].map(s => bullet([txt(s, { size: 20 })])), emptyP(80),

        h3("학술 심층 분석 주요 출처"),
        ...[ '아시아소사이어티 정책연구소(Asia Society Policy Institute) — Neil Thomas, "Xi Jinping\'s Purges Have Escalated"',
          '케임브리지 대학 출판부(Cambridge Core), 차이나 쿼털리(The China Quarterly) — Kou Chien-wen, "Xi Jinping in Command"',
          '영국정치학저널(British Journal of Political Science) — "To Purge or Not to Purge?"',
          '사이언스다이렉트(ScienceDirect), 비교경제학저널(Journal of Comparative Economics) — "The competence-loyalty tradeoff"',
          '캘리포니아대 샌디에이고(UC San Diego) — "Threats and Political Instability in Authoritarian Regimes"',
          '리서치게이트(ResearchGate) — "Elite Defection under Autocracy: Evidence from Russia"',
          'Semafor — "Xi is purging. Is this Stalinism?"',
          '엥겔스버그 아이디어(Engelsberg Ideas) — "China\'s century of purges"',
          '후버 연구소(Hoover Institution) — "The Lin Biao Incident and the PLA of Purges"',
          '허드슨 연구소(Hudson Institute) — "Why Communist Leaders Purge Their Generals"',
          '민주주의 다양성 연구소(V-Dem Institute), Democratization — "State of the world 2024"',
        ].map(s => bullet([txt(s, { size: 20 })])), emptyP(120),

        h2("10.3 분석 실행 요약"),
        new Table({ columnWidths: [2200, 2275, 2276, 2275], rows: [
          new TableRow({ tableHeader: true, children: [headerCell("항목", 2200), headerCell("일반 스캐닝", 2275), headerCell("학술 심층 분석", 2276), headerCell("통합", 2275)] }),
          new TableRow({ children: [dataCell("소스 수", 2200, { tOpts: { bold: true } }), dataCell("20개 이상", 2275, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("15건 논문/보고서", 2276, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("35개 이상", 2275, { pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("수집 신호", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("10", 2275, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("5", 2276, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("15", 2275, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("상위 신호", 2200, { tOpts: { bold: true } }), dataCell("10개", 2275, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("5개", 2276, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("15개", 2275, { pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("평균 신뢰도", 2200, { fill: C.lightGray, tOpts: { bold: true } }), dataCell("83.6점", 2275, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("83.6점", 2276, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } }), dataCell("83.6점", 2275, { fill: C.lightGray, pOpts: { alignment: AlignmentType.CENTER } })] }),
          new TableRow({ children: [dataCell("생성일", 2200, { tOpts: { bold: true } }), dataCell("2026-02-04", 2275, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("2026-02-04", 2276, { pOpts: { alignment: AlignmentType.CENTER } }), dataCell("2026-02-04", 2275, { pOpts: { alignment: AlignmentType.CENTER } })] }),
        ] }), emptyP(200),

        new Table({ columnWidths: [TW], rows: [new TableRow({ children: [new TableCell({ borders: { top: { style: BorderStyle.SINGLE, size: 2, color: C.navy }, bottom: noBorder, left: noBorder, right: noBorder }, width: { size: TW, type: WidthType.DXA }, children: [emptyP(20)] })] })] }),
        p([txt("보고서 생성일: 2026년 2월 4일", { size: 18, color: C.gray })], { alignment: AlignmentType.CENTER }),
        p([txt("분석 방법: 이중 워크플로우 통합 스캐닝 (일반 환경스캐닝 + 학술 심층 분석)", { size: 18, color: C.gray })], { alignment: AlignmentType.CENTER }),
        p([boldTxt("상태: 최종 승인 완료", { size: 18, color: "27AE60" })], { alignment: AlignmentType.CENTER }),
      ]
    }
  ]
});

const OUT = "/Users/cys/Desktop/AIagentsAutomation/EnvironmentScan-system-main-v1/env-scanning/integrated/reports/daily/중국_군부숙청_분석보고서_2026-02-04.docx";
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log("DONE:", OUT); });
