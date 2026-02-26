# garak_ko

*Generative AI Red-teaming & Assessment Kit (Korean-focused workspace)*

`garak_ko`는 `garak` 기반의 LLM 취약점 점검 워크스페이스입니다.  
한국어(`target_lang=ko`) 평가를 빠르게 실행할 수 있도록 seed group, 실행 설정, 튜토리얼을 정리해 둔 레포입니다.

---

## 시작하기
### > 원본 문서: [docs.garak.ai](https://docs.garak.ai/)
### > 프로젝트: [garak.ai](https://garak.ai/)
### > 원본 저장소: [NVIDIA/garak](https://github.com/NVIDIA/garak)

---

## garak_ko의 특징

- 한국어 실행 패키지 제공: `garak/configs/korean_specialization.yaml`
- 짧은 실행용 cap 설정 제공: `run-soft.yaml`
- 노트북 튜토리얼 제공: `tutorials/`
- 함수형 실행 래퍼 제공: `main.py`
- seed/judge/target 기반 구조는 원본 `garak`와 동일

---

## 지원 대상 모델

원본 `garak`의 대상(target) 플러그인을 그대로 사용합니다.

- OpenAI API
- Hugging Face
- AWS Bedrock
- Replicate
- LiteLLM
- REST endpoint
- 그 외 `garak --list_targets`로 확인 가능한 대상

---

## 설치

### 1) 소스 기준 설치 (권장)

```bash
python -m pip install -e .
```

### 2) PyPI 설치

```bash
python -m pip install -U garak
```

Python 버전은 `>=3.10`을 권장합니다.

---

## 빠른 시작

### 1) 사용 가능한 seed group 확인

```bash
python -m garak --list_seed_groups --seed_groups_file garak/configs/korean_specialization.yaml
```

### 2) 한국어 우선순위 패키지 실행

```bash
python -m garak \
  --target_type openai \
  --target_name gpt-4o-mini \
  --seed_groups_file garak/configs/korean_specialization.yaml \
  --seed_group priority_ko_soft_20m \
  --config run-soft.yaml
```

### 3) 한국어 스모크 패키지 실행

```bash
python -m garak \
  --target_type openai \
  --target_name gpt-4o-mini \
  --seed_groups_file garak/configs/korean_specialization.yaml \
  --seed_group quick_variety_smoke_ko \
  --config run-soft.yaml
```

### 4) 단일 seed 실행 예시

```bash
python -m garak \
  --target_type openai \
  --target_name gpt-4o-mini \
  --target_lang ko \
  --seeds grandma.Win10 \
  --generations 1 \
  --config run-soft.yaml
```

---

## `main.py` 래퍼 사용

`main.py`는 내부적으로 `garak.cli.main()`을 호출하는 간단한 실행 래퍼입니다.

```bash
python main.py \
  --target_type openai \
  --target_name gpt-4o-mini \
  --target_lang ko \
  --seeds grandma.Win10 \
  --generations 1 \
  --config run-soft.yaml
```

---

## 입력 명세 (요약)

- 필수에 가까운 인자:
  - `--target_type`
  - `--target_name` (대부분의 target에서 필요)
- 실행 범위 제어:
  - `--seeds` 또는 `--seed_group`
  - `--config`
- 런타임 제어:
  - `--target_lang`
  - `--generations`
  - `--eval_threshold`
  - `--parallel_attempts`

상세 스키마는 다음 문서를 참고하세요.

- `docs/source/cliref.rst`
- `docs/source/configurable.rst`
- `garak/cli.py`

---

## 결과 파일

실행이 끝나면 기본적으로 아래 파일이 생성됩니다.

- `garak.<uuid>.report.jsonl`: 시도/평가 상세 로그
- `garak.<uuid>.report.html`: 요약 리포트
- `garak.<uuid>.hitlog.jsonl`: 취약점 hit만 추린 로그

기본 저장 위치는 `reporting.report_dir` 설정을 따릅니다.  
코어 기본값은 `garak_runs`이며, 일반적으로 XDG 데이터 경로 아래에 저장됩니다.

---

## 한국어 실행 시 참고사항

- 기본 코어 설정에 언어 변환(`en<->ko`)용 langprovider가 포함되어 있습니다.
- 오프라인/망차단 환경에서는 번역 모델 다운로드가 실패할 수 있습니다.
- 이런 환경에서는 `run.langproviders`를 비우거나, 사전 캐시된 모델을 사용하세요.

---

## 레포 구조 (핵심)

- `garak/`: 코어 패키지
- `garak/configs/`: 실행 프로필 및 한국어 specialization 설정
- `run-soft.yaml`: prompt cap 중심 실행 설정
- `tutorials/`: 실행 튜토리얼 노트북
- `tests/`: 단위 테스트
- `main.py`: 함수형 실행 래퍼

---

## 자주 쓰는 명령

```bash
# seed 목록
python -m garak --list_seeds

# judge 목록
python -m garak --list_judges

# target 목록
python -m garak --list_targets

# 현재 config 확인
python -m garak --list_config
```

---

## 라이선스

Apache-2.0 (원본 `garak`와 동일)

