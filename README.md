# garak_ko

*Generative AI Red-teaming & Assessment Kit (Korean-focused workspace)*

> 원본 문서: [docs.garak.ai](https://docs.garak.ai/) | 원본 저장소: [NVIDIA/garak](https://github.com/NVIDIA/garak)

---

### 1. 레포지토리 설명

연관 프로젝트: 
담당자: 노은솔
작성일: 2026-03-16

`garak_ko`는 NVIDIA의 오픈소스 LLM 취약점 점검 프레임워크인 `garak`를 기반으로,
**한국어 LLM 평가에 특화된 워크스페이스**입니다.

한국어(`target_lang=ko`) 평가를 빠르게 실행할 수 있도록 seed group, 실행 설정, 튜토리얼을 정리해 두었습니다.

주요 특징:
- 한국어 실행 패키지 제공: `garak/configs/korean_specialization.yaml`
- 짧은 실행용 cap 설정 제공: `run-soft.yaml`
- 노트북 튜토리얼 제공: `tutorials/`
- 함수형 실행 래퍼 제공: `main.py`
- 지원 대상(target): OpenAI API, Hugging Face, AWS Bedrock, Replicate, LiteLLM, REST endpoint

---

### 2. 데이터셋

garak 내장 데이터셋(`garak/data/`)을 기반으로 사용하며, 한국어 특화 seed는 `garak/seeds/` 내에 직접 구현되어 있습니다. 외부 데이터셋 의존성 없음.

---

### 3. 구체적인 설명

garak는 **seed → attacker → target → judge → evaluator** 파이프라인 구조로 동작합니다.

방법 1. **seed group 기반 실행** — `korean_specialization.yaml`에 정의된 seed group을 지정해 한국어 평가 패키지 단위로 실행
방법 2. **단일 seed 실행** — `--seeds` 옵션으로 특정 seed를 지정해 개별 취약점 점검
방법 3. **`main.py` 래퍼 사용** — `garak.cli.main()`을 내부적으로 호출하는 간단한 실행 래퍼

한국어 평가 시, 기본 설정에 `en↔ko` 번역용 langprovider가 포함되어 있어 영어 seed를 한국어로 자동 변환하여 평가합니다.

---

### 4. 파이프라인 설명 및 실행
**0. 환경 설치 관련 **

**1. 파이프라인 설명**

```
seed group 지정
    → garak CLI 실행
    → langprovider(en→ko) 번역
    → target 모델 호출
    → judge 평가
    → JSONL/HTML 리포트 생성
```

실행 결과로 아래 파일이 생성됩니다:
- `garak.<uuid>.report.jsonl`: 시도/평가 상세 로그
- `garak.<uuid>.report.html`: 요약 리포트
- `garak.<uuid>.hitlog.jsonl`: 취약점 hit만 추린 로그

**2. 파이프라인 실행**

```bash
# seed group 목록 확인
python -m garak --list_seed_groups --seed_groups_file garak/configs/korean_specialization.yaml

# 한국어 우선순위 패키지 실행
python -m garak \
  --target_type openai \
  --target_name gpt-4o-mini \
  --seed_groups_file garak/configs/korean_specialization.yaml \
  --seed_group priority_ko_soft_20m \
  --config run-soft.yaml

# 단일 seed 실행
python -m garak \
  --target_type openai \
  --target_name gpt-4o-mini \
  --target_lang ko \
  --seeds grandma.Win10 \
  --generations 1 \
  --config run-soft.yaml
```

변경 인자 설명:
- `--target_type`: 대상 모델 타입 (openai, huggingface, bedrock 등)
- `--target_name`: 대상 모델명
- `--seed_group`: 실행할 seed group 이름
- `--seeds`: 실행할 단일 seed (`.`으로 구분된 클래스명)
- `--target_lang`: 언어 코드 (ko, en 등)
- `--generations`: 시도 횟수
- `--config`: 실행 설정 파일

---

### 5. 이슈

<!-- 진행하면서 발생한 이슈사항 -->

---

### 6. Requirements

Python `>=3.10`

핵심 라이브러리:

```
transformers>=4.51.3,<4.57.0
datasets>=3.0.0,<4.0
torch>=2.6.0
openai>=1.45.0,<2
litellm>=1.68.1
langchain>=0.3.25,<1.0.0
huggingface_hub>=0.21.0
tiktoken>=0.7.0
langdetect==1.0.9
deepl==1.17.0
google-cloud-translate>=2.0.4
boto3>=1.28.0
```

전체 의존성은 `pyproject.toml` 및 `requirements.txt` 참고.

설치:
```bash
python -m pip install -e .
```

테스트 의존성 추가 설치:
```bash
python -m pip install -e ".[tests]"
```

---

### 7. 폴더 구조

```
garak_ko/
├── garak/                          # 코어 패키지 (NVIDIA/garak 기반)
│   ├── configs/                    # 실행 프로필 및 한국어 specialization 설정
│   ├── seeds/                      # 취약점 seed 구현체
│   ├── judges/                     # 판정 모듈
│   ├── targets/                    # 대상 모델 어댑터
│   ├── langproviders/              # 언어 변환 모듈 (en↔ko)
│   ├── attackers/                  # 공격 전략 모듈
│   ├── evaluators/                 # 평가 모듈
│   ├── harnesses/                  # 실행 하네스
│   └── data/                       # 내장 데이터셋
├── tests/                          # 단위 테스트 (pytest)
│   ├── seeds/
│   ├── judges/
│   └── ...
├── tutorials/                      # 실행 튜토리얼 노트북
│   ├── tutorial.ipynb
│   ├── tutorial_korean_specialization_priority.ipynb
│   └── ...
├── tools/                          # 유틸리티 스크립트
├── docs/                           # 문서
├── main.py                         # 함수형 실행 래퍼
├── run-soft.yaml                   # prompt cap 중심 실행 설정
└── pyproject.toml
```
