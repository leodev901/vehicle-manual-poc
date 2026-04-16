# 🚀 로드맵 0단계 (1): 고급 어플리케이션 아키텍처 - 추상화(Abstraction)와 다형성

안녕하세요! 이번 학습 노트에서는 현재 우리 프로젝트의 **AS-IS 백엔드 구조를 분석**하고, 앞으로 어떻게 **결합도 0%의 견고한 아키텍처(TO-BE)**로 발전시킬 수 있는지 신입 개발자분들도 이해하기 쉽게 단계별로 설명해 드리겠습니다.

---

## 1. 🔍 AS-IS 구조 파악: 우리는 무엇이 문제일까요?

우선 현재 백엔드의 비즈니스 로직을 담당하는 `app/services/manual_service.py`를 살펴보겠습니다.

```python
# app/services/manual_service.py (AS-IS)
from fastapi import Depends
from app.repositories.manual_repository import ManualRepository

class ManualService:
    def __init__(
        self,
        # 🚨 여기서 문제 발생! Service가 특정 데이터베이스(ManualRepository)를 '직접' 가리키고 있습니다.
        manual_repository: ManualRepository = Depends(ManualRepository),
    ):
        self.manual_repository = manual_repository

    async def list_brands(self):
        # 🚨 Service 내부에서 구체적인 클래스의 메서드를 강하게 의존하고 있습니다.
        result = await self.manual_repository.list_brands()
        ...
```

### 💡 무엇이 강한 결합(Tight Coupling)인가요?
현재 `ManualService`는 `ManualRepository`라는 **실제 구현체(Concrete Class)**에 직접적으로 의존하고 있습니다.
* **만약 데이터베이스를 Supabase에서 MongoDB로 바꾼다면?**
  `MongoManualRepository`를 새로 만들고, `ManualService`의 코드도 전부 수정해야 합니다. 
* **테스트를 하고 싶다면?**
  Service를 테스트하려면 항상 실제 DB(Supabase)가 연결되어 있어야 합니다. (순수 비즈니스 로직만 테스트하기 어렵습니다.)

이것이 바로 **강한 결합**입니다. 단일 책임 원칙(SRP) 관점에서도 `ManualService`는 '비즈니스 로직'만 책임져야 하는데, '어떤 DB 구현체를 쓸 것인가'까지 알아야 하는 부담을 안고 있습니다.

---

## 2. 🛡️ TO-BE 설계: 의존성 역전 원칙 (DIP)

이 문제를 해결하기 위해 도입하는 것이 객체지향의 꽃이라 불리는 **의존성 역전 원칙(Dependency Inversion Principle)**입니다.
쉽게 말해, Service가 **"어떤 DB를 쓸지는 모르겠고, 껍데기(인터페이스)에 적힌 약속만 지키면 난 그 DB를 쓸게!"** 라고 선언하는 것입니다.

이 **껍데기**를 파이썬에서 만드는 두 가지 주요 방식이 바로 `abc.ABC`와 `typing.Protocol`입니다.

### 🆚 `abc.ABC` vs `typing.Protocol` 차이점 한눈에 보기

| 특징 | `abc.ABC` (추상 클래스) | `typing.Protocol` (덕 타이핑) |
|---|---|---|
| **역할** | 명시적으로 상속을 받아야 하는 '청사진' | 특정 메서드만 구현하면 인정해주는 '자격증' |
| **코드 관계** | `class MyRepo(ABCRepo):` **(강제 상속)** | 상속 불필요. 우는 소리만 내면 오리로 인정!(Duck Typing) |
| **엔터프라이즈 선호도** | 전통적인 객체지향 (Java 스타일) | **최근 파이썬 트렌드 (느슨한 결합 극대화)** |

파이썬에서는 상속의 강제성마저 제거하여 결합도를 궁극적으로 낮출 수 있는 **`Protocol` (덕 타이핑)** 방식을 많이 추천합니다.

---

## 3. 🛠️ 어떻게 코드를 수정해야 할까요? (TO-BE 적용안)

코드 변경은 크게 세 가지 단계로 나뉩니다. 기존 코드를 훼손하지 않으면서 아키텍처를 진화시키는 방법입니다.

### 단계 1: 인터페이스(Protocol) 선언하기
Repository가 어떤 메서드들을 가지고 있어야 하는지 약속(형태)만 정의하는 프로토콜을 선언합니다.

```python
# TO-BE 제안: app/repositories/protocols.py (신규 파일 생성)
from typing import Protocol, List, Dict, Any

class ManualRepositoryProtocol(Protocol):
    """
    이 프로토콜을 만족하려면, 아래의 메서드들을 반드시 구현해야 합니다.
    설정값은 코드가 아닌 외부에서 주입받는 형태로 디자인됩니다.
    """
    async def list_brands(self) -> List[Dict[str, Any]]:
        ...
        
    async def list_lineups(self, brand_id: str) -> List[Dict[str, Any]]:
        ...
        
    async def list_models(self, lineup_id: str) -> List[Dict[str, Any]]:
        ...
```
*(참고: `...` 은 실제로 구현하지 않고 선언만 한다는 뜻입니다.)*

### 단계 2: Service가 Protocol에 의존하도록 변경
`ManualService`가 더 이상 구체적인 `ManualRepository`를 가져오지 않고, 방금 만든 Protocol을 바라보게 합니다.

```python
# TO-BE 제안: app/services/manual_service.py (수정안)
# 1. 구체적인 구현체 대신 프로토콜만 가져옵니다!
from app.repositories.protocols import ManualRepositoryProtocol

class ManualService:
    def __init__(
        self,
        # 2. 타입 힌트로 Protocol을 지정합니다. 이제 구현체에 강하게 결합되지 않습니다!
        manual_repository: ManualRepositoryProtocol,
    ):
        self.manual_repository = manual_repository

    async def list_brands(self):
        # 3. 내부 사용법은 동일하지만, 기반 DB 처리는 주입된 객체에 위임합니다.
        result = await self.manual_repository.list_brands()
        ...
```

### 단계 3: FastAPI에서 의존성 주입 연결하기 (생성 시점)
Service를 껍데기만 바라보게 만들었으므로, FastAPI 라우터에서 API를 호출할 때 "진짜 구현체"를 만들어서 밀어 넣어주어야 합니다 (Dependency Injection). FastAPI의 DI 시스템을 활용하여 라우터 단에서 이 퍼즐을 조립합니다.

---

## 🎓 요약: 왜 이렇게 쪼개야 하는가? (이유와 기대효과)

단순히 동작하는 코드를 넘어서, 엔터프라이즈 환경에서 왜 이렇게 인터페이스 계층을 하나 더 두는지 정리해보겠습니다.

1. **플러그인 교체하듯 쉬운 유지보수**: 추후 `MockManualRepository(Fake DB)`를 만들 때 프로토콜 규칙에 맞춰 `list_brands`, `list_lineups` 함수만 똑같이 만들어 끼워 넣으면 1초 만에 데이터베이스 없이도 테스트(Unit Test)를 돌릴 수 있게 됩니다!
2. **독립적인 개발 속도 향상**: 프론트엔드 팀과 작업할 때, 백엔드 DB 연동이 끝날 때까지 기다리지 않고 '가짜 응답을 반환하는 FakeRepository'를 주입시켜서 서버를 먼저 띄워줄 수 있습니다.
3. **단일 책임 원칙 (SRP) 준수**: 서비스 로직은 오로지 "가져온 데이터를 어떻게 가공하고 에러 처리를 할까?"라는 본연의 책임에만 집중할 수 있게 되었습니다.

다음 스텝은 이렇게 분리된 구조를 바탕으로 **FakeRepository를 만들고, 진짜 DB 연결 없이 유닛 테스트를 작성해 보는 실습**입니다!
