# 🚀 로드맵 0단계 (1): 고급 어플리케이션 아키텍처 - 추상화(Abstraction)와 다형성

안녕하세요! 이번 학습 노트에서는 프로젝트의 **AS-IS 백엔드 구조를 분석**하고, 어떻게 **결합도 0%의 견고한 아키텍처(TO-BE)**로 발전시켰는지, 그리고 적용 과정에서 겪었던 **엔터프라이즈 실무의 진짜 고민들(폴더 구조, 의존성 주입 등)**을 정리합니다.

---

## 1. 🔍 AS-IS 구조 파악: 우리는 무엇이 문제였을까요?

기존 백엔드의 비즈니스 로직(`app/services/manual_service.py`)을 살펴보면 다음과 같았습니다.

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
* **만약 데이터베이스를 Supabase에서 Elasticsearch로 바꾼다면?**
  서비스 코드를 모두 열어서 임포트문부터 교체해야 하며, 핵심 비즈니스 로직이 망가질 위험성이 생깁니다.
* **테스트를 하고 싶다면?**
  Service를 테스트하려면 항상 실제 DB(Supabase)가 연결되어 있어야 합니다. (순수 비즈니스 로직만 테스트하기 어렵습니다.)

이것이 바로 **강한 결합**입니다. 단일 책임 원칙(SRP) 관점에서도 `ManualService`는 '비즈니스 로직'만 책임져야 하는데, '어떤 DB 구현체를 쓸 것인가'까지 알아야 하는 부담을 안고 있습니다.
  무조건 진짜 Supabase DB에 네트워크 접속을 해야만 테스트가 가능합니다. 네트워크가 끊기면 내 코드는 정상이어도 빌드가 실패합니다.

---

## 2. 🛡️ TO-BE 설계: 의존성 역전 원칙 (DIP)과 Duck Typing

이 문제를 해결하기 위해 **의존성 역전 원칙(Dependency Inversion Principle)**을 도입합니다.
Service가 **"어떤 DB를 쓸지는 모르겠고, 껍데기(인터페이스)에 적힌 약속만 지키면 난 그 DB를 쓸게!"** 라고 선언하는 것입니다.

### 🆚 `abc.ABC` vs `typing.Protocol` 차이점 한눈에 보기

| 특징 | `abc.ABC` (추상 클래스) | `typing.Protocol` (덕 타이핑) |
|---|---|---|
| **역할** | 명시적으로 상속을 받아야 하는 '청사진' | 특정 메서드만 구현하면 인정해주는 '자격증' |
| **코드 관계** | `class MyRepo(ABCRepo):` **(강제 상속)** | 상속 불필요. 우는 소리만 내면 오리로 인정!(Duck Typing) |
| **엔터프라이즈 선호도** | 전통적인 객체지향 (Java 스타일) | **최근 파이썬 트렌드 (느슨한 결합 극대화)** |

### 🦆 파이썬의 `typing.Protocol` 과 덕 타이핑(Duck Typing)
> *"오리처럼 걷고 오리처럼 소리 낸다면, 나는 그것을 오리라고 부르겠다."*

**Protocol의 압도적 장점:**
실제 구현체인 `ManualSupabaseRepository`는 자기가 `Protocol`을 상속받는다는 사실조차 코드에 적을(Import) 필요가 없습니다. 단지 Protocol이 요구하는 동일한 이름의 메서드를 똑같이 가지고 있기만 하면 파이썬이 알아서 형태를 인정해 줍니다. 

---

## 3. 🛠️ 어떻게 코드를 수정해야 할까요? (핵심 TO-BE 샘플 코드)

기존 코드를 훼손하지 않으면서 아키텍처를 진화시키는 2단계 방법입니다.

### 단계 1: 인터페이스(Protocol) 선언하기
Repository가 어떤 메서드들을 가지고 있어야 하는지 약속(형태)만 정의하는 프로토콜을 선언합니다.

```python
# TO-BE 제안: app/repositories/manual/protocol.py
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

### 단계 2: Service가 Protocol에 의존하도록 변경
`ManualService`가 더 이상 구체적인 기능을 가진 `Repository`를 가져오지 않고, 방금 만든 껍데기(Protocol)를 바라보게 합니다.

```python
# TO-BE 제안: app/services/manual_service.py
from app.repositories.manual.protocol import ManualRepositoryProtocol

class ManualService:
    def __init__(
        self,
        # 1. 타입 힌트로 Protocol을 지정합니다. 이제 구현체에 강하게 결합되지 않습니다!
        manual_repository: ManualRepositoryProtocol,
    ):
        self.manual_repository = manual_repository

    async def list_brands(self):
        # 2. 내부는 껍데기를 믿고 그대로 씁니다. 진짜 동작은 외부에서 꽂아준 놈이 처리합니다.
        result = await self.manual_repository.list_brands()
        ...
```

### 단계 3: FastAPI에서 의존성 주입 연결하기 (`dependencies.py`)
서비스가 껍데기만 바라보게 되었으므로, 런타임에 진짜 부품을 조립해주는 전용 함수를 만듭니다.


단순히 동작하는 코드를 넘어서, 엔터프라이즈 환경에서 왜 이렇게 인터페이스 계층을 하나 더 두는지 정리해보겠습니다.

1. **플러그인 교체하듯 쉬운 유지보수**: 추후 `MockManualRepository(Fake DB)`를 만들 때 프로토콜 규칙에 맞춰 `list_brands`, `list_lineups` 함수만 똑같이 만들어 끼워 넣으면 1초 만에 데이터베이스 없이도 테스트(Unit Test)를 돌릴 수 있게 됩니다!
2. **독립적인 개발 속도 향상**: 프론트엔드 팀과 작업할 때, 백엔드 DB 연동이 끝날 때까지 기다리지 않고 '가짜 응답을 반환하는 FakeRepository'를 주입시켜서 서버를 먼저 띄워줄 수 있습니다.
3. **단일 책임 원칙 (SRP) 준수**: 서비스 로직은 오로지 "가져온 데이터를 어떻게 가공하고 에러 처리를 할까?"라는 본연의 책임에만 집중할 수 있게 되었습니다.

다음 스텝은 이렇게 분리된 구조를 바탕으로 **FakeRepository를 만들고, 진짜 DB 연결 없이 유닛 테스트를 작성해 보는 실습**입니다!

```python
# TO-BE 제안: app/core/dependencies.py
from fastapi import Depends
from app.services.manual_service import ManualService
from app.repositories.manual import ManualRepositoryProtocol, ManualSupabaseRepository

async def get_manual_service(
    # 여기서 스위치를 켭니다. 교체가 필요하면 이 괄호 안의 이름 1개만 바꿉니다! (예: ManualMockRepository)
    repository: ManualRepositoryProtocol = Depends(ManualSupabaseRepository)
):
    # 파라미터로 받은 완성품을 그대로 서비스에 주입!
    return ManualService(repository)
```

---

## 4. 📂 디렉터리 아키텍처: 도메인 중심 설계 (DDD 관점)

인프라가 커지면 인터페이스와 구현체가 많아집니다. 파일과 폴더를 어떻게 나눌까요?

### ✅ 엔터프라이즈 모범 사례 (도메인/업무 중심 패키징)
```text
backend/app/repositories/
└── manual/                             # '차량 매뉴얼' 비즈니스 도메인 폴더
    ├── __init__.py                     # 모듈 인터페이스 (Facade)
    ├── protocol.py                     # [껍데기] ManualRepositoryProtocol
    ├── supabase_repository.py          # [구현체1] ManualSupabaseRepository
    ├── sqlalchemy_repository.py        # [구현체2] ManualSqlAlchemyRepository
    └── mock_repository.py              # [테스트용] ManualMockRepository
```

#### 🎁 `__init__.py`를 활용한 임포트 다이어트 (Facade 패턴)
폴더 안의 모든 파일을 바깥에서 1줄에 가져올 수 있게 포장해 줍니다.
```python
# app/repositories/manual/__init__.py
from .protocol import ManualRepositoryProtocol
from .supabase_repository import ManualSupabaseRepository
from .mock_repository import ManualMockRepository
```
이제 밖(`dependencies.py`)에서는 아래처럼 단 한 줄로 모든 클래스를 꺼내 쓸 수 있습니다.
```python
from app.repositories.manual import (
    ManualRepositoryProtocol,
    ManualSupabaseRepository,
    ManualMockRepository
)
```

---

## 5. 🛠️ FastAPI 의존성 주입(DI)의 마법과 함정

가장 많이 혼란을 겪는 `dependencies.py` 조립 공장의 핵심 원리입니다.

### 🚨 함정: 함수 내부에서 재할당 금지
```python
# ❌ 최악의 작성법 (자주 하는 실수)
async def get_manual_service(
    repository: ManualRepositoryProtocol = Depends(ManualSupabaseRepository)
):
    # 위에서 FastAPI가 완벽히 조립(Supabase 커넥션까지)해서 줬는데,
    # 밑에서 빈 괄호로 다시 덮어씌워서 DB 커넥션이 증발해버리는 버그 발생!
    repository = ManualSupabaseRepository() 
    return ManualService(repository)
```

```python
# ✅ 정답: 라우터 파라미터에서 모든 것을 해결한다.
async def get_manual_service(
    # 👇 레포지토리 교체가 필요하면 이 괄호 안의 이름 1개만 바꿉니다! (예: ManualMockRepository)
    repository: ManualRepositoryProtocol = Depends(ManualSupabaseRepository)
):
    return ManualService(repository) # 파라미터로 받은 것을 그대로 주입!
```

### 🧠 FastAPI의 의존성 캐싱 (Client 중복 연결 문제)
Q. *"만약 Service에 수많은 종류의 Repository가 필요하다면? 모두 주입하면 `Depends(get_supabase_client)`가 여러 번 불려서 DB 커넥션이 폭발하는 것 아닐까?"*

**A. 절대 아닙니다! FastAPI는 `use_cache=True`가 기본값입니다.**
한 번의 통신(Request)이 일어날 때, `ManualRepository`를 만들며 `get_supabase_client`를 단 1번 호출합니다. 그 다음 `ChatRepository`를 만들 때는 똑같은 의존성을 파악하고, **방금 만들어둔 커넥션을 재사용**하여 꽂아줍니다! 즉, Service는 결합도를 끊어내면서 DB 연결 성능까지 100% 최적화됩니다.

---

## 6. 🗣️ Q&A : 아키텍처 토론 회고록

**Q1. 단위 테스트(Unit Test) 의미 있나? 당연히 진짜 DB를 붙여서 검증해야지!**
* **A.** 네, 실제 DB가 도는지 검증하는 '통합 테스트(Integration Test)'는 생명입니다. 하지만 우리가 Mock 객체를 만든 이유는 코어(Service)의 **'단위 테스트'**를 위해서입니다. "만약 DB가 갑자기 죽어버린다면, 내 서비스 코드가 에러를 잘 우회할까?"라는 악조건(Edge Case)은 실제 DB 환경에서는 억지로 재현하기 매우 어렵습니다. 그래서 Fake 객체를 통해 극한의 엣지 케이스들을 0.01초 만에 검증하는 것입니다.

**Q2. 인터페이스, 의존성 다 좋은데, 파일이 너무 많아지고 코드가 너무 복잡해집니다 (가독성 하락).**
* **A.** 완전히 공감합니다. 의존성을 쪼개면 타이핑할 파라미터가 늘어납니다. 만약 레포지토리 수십 개를 주입해야 해서 정말 가독성에 한계가 온다면, **UoW (Unit of Work) 또는 퍼사드(Facade) 패턴**을 씁니다. 
바구니(`AppRepositoryUnit`) 객체 1개에 모든 Repository를 묶어넣고 그것 1개만 주입받아서 `self.repo.manual...` 처럼 꺼내 쓰는 타협을 통해 높은 수준의 가독성과 의존성 분리를 둘 다 가져갈 수 있습니다.

**결론적으로, 무조건 쪼개는 것만이 정답은 아니지만, 이런 코어 도메인(설계/인프라 변동성이 큰 RAG 엔진 등)은 시간을 지불하더라도 완벽히 분리해 두는 것이 미래의 파멸을 막는 엔터프라이즈 환경 투자의 기본입니다.**
