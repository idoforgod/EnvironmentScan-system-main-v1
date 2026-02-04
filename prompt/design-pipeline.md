다음 주의사항과 요구사항을 따르는 AI 에이전트 파이프라인을 기획하라.

작업을 시작하기전에 먼저 주의사항/요구사항을 완전히 이해하고, 제대로 이해한 것이 맞는지 방향성 등에 대해서 모호한 부분이 있다면 내게 최대 4개까지 질문하세요. 각 질문은 Recommend 옵션, 기타 옵션을 포함하여 3개 정도의 선택지를 제공하세요.

결과에는 다음 사항들이 반드시 포함되어야한다.

- step-by-step으로 필요한 정보들과, 해당 정보를 추출하기위한 데이터 pre-processing, post-processing

- agent들의 관계 및 역할

주의사항은 다음과 같다.

- 너무 큰 데이터를 AI에게 그대로 맡기면, context size를 과하게 소모해 큰 비용이 발생하고 정확도도 떨어질 수 있다. step-by-step으로 필요한 정보를 추출하되, 해당 정보를 추출하는데 필요하지 않은 데이터는 code-level에서 python script 등으로 적절히 제거한 뒤 전달하는 편이 좋다.

- 데이터의 연관관계도 code-level에서 compute할 수 있는 것들은 가능한 미리 처리해서 전달하는 편이 좋다.

- 이미지 리소스도 정확히 다운로드해야하며, placeholder도 모두 추출해야한다.

claude code를 사용할 것이다. master agent가 전체 작업흐름을 담당하고, context 소모가 큰 하위 작업을 sub agent에게 위임한다.

요구사항:
framer로 구현된 랜딩페이지를, react + tailwindcss + motion/react를 사용한 header/footer/섹션 컴포넌트들의 조합으로 정확히 클론코딩한다.
