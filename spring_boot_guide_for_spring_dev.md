# Spring Boot 핵심 개념 가이드 (for Spring 유경험자)

주니어 시절 Spring 프레임워크(Legacy)로 MVC 패턴(Controller, Service, Repository)을 경험해 보셨다면, 이미 가장 중요한 뼈대는 알고 계신 것입니다. 

Spring Boot는 기존 Spring의 **"귀찮고 복잡한 설정"을 자동화**하여 핵심 비즈니스 로직(Controller, Service) 개발에만 집중할 수 있게 만든 **강화판**입니다.

---

## 1. Spring과 Spring Boot의 가장 큰 차이점 3가지

### 1) 자동 설정 (Auto-Configuration)
- **과거 (Spring):** DB 연결, JSON 변환, 트랜잭션 등 기술 하나를 추가할 때마다 `XML`이나 `Java Config` 파일에 수많은 설정 코드를 작성해야 했습니다.
- **현재 (Spring Boot):** `@SpringBootApplication` 어노테이션 하나로 자주 쓰이는 설정들을 프로젝트 환경에 맞게 자동으로 세팅해 줍니다. 

### 2) 내장형 WAS (웹 애플리케이션 서버)
- **과거:** Tomcat이나 WebLogic 같은 WAS를 별도로 설치하고, `.war` 파일로 빌드해서 WAS에 배포(Deploy)해야 했습니다.
- **현재:** **Tomcat이 내장**되어 있어 `.jar` 파일 하나로 빌드하고 `java -jar app.jar` 명령어로 언제 어디서든 즉시 실행할 수 있습니다. (FastAPI의 `uvicorn` 실행과 똑같습니다.)

### 3) 의존성 관리 (Starter 패키지)
- **과거:** 호환되는 라이브러리 버전들을 일일이 찾아 `pom.xml`에 넣느라 버전 충돌(Jar Hell)이 빈번했습니다.
- **현재:** `spring-boot-starter-web`, `spring-boot-starter-data-jpa` 처럼 목적에 맞는 **스타터 패키지 하나만 선언**하면, 호환이 검증된 라이브러리 조합을 한 번에 다 가져옵니다.

---

## 2. 프로젝트 구조 (현재 FastAPI 프로젝트와 비교)

현재 작성하신 Python(FastAPI) 구조와 Spring Boot 구조는 놀랍도록 비슷합니다.

```text
[파이썬 FastAPI 기반 프로젝트]          |   [자바 Spring Boot 프로젝트]
                                   |
backend/                           |   src/main/java/com/example/vehiclebot/
├── app/                           |   ├── VehicleBotApplication.java (실행부)
│   ├── api/endpoints/             |   ├── controller/
│   │   └── manual.py  (라우터)      |   │   └── ManualController.java
│   │                              |   │
│   ├── services/                  |   ├── service/
│   │   └── manual_service.py      |   │   └── ManualService.java
│   │                              |   │
│   ├── repositories/              |   ├── repository/
│   │   └── manual_repository.py   |   │   └── ManualRepository.java
│   │                              |   │
│   ├── schemas/ (Pydantic 모델)   |   ├── dto/
│   │                              |   │   ├── ManualRequest.java
│   │                              |   │   └── ManualResponse.java
│   │                              |   │
│   └── core/ (설정 및 예외처리)      |   ├── config/ (설정 파일들)
│                                  |   └── exception/ (전역 예외 처리기)
│                                  |
└── .env (환경 변수)                 |   src/main/resources/
                                   |   └── application.yml (환경 변수 및 설정)
```

---

## 3. 엔터프라이즈 코드 디자인 패턴 및 구조화 원칙

금융권 등 시스템 안정성을 중요시하는 곳에서는 아래의 원칙들을 엄격히 지킵니다.

### ① 단일 책임 원칙 (SRP)과 의존성 주입 (DI)
`Controller`는 요청 객체(HTTP/DTO) 검증과 응답만 처리해야 합니다.
`Service`는 비즈니스 로직(AI 호출, 데이터 검증)만 수행하며, `Repository`는 DB와 통신만 합니다.
이 계층 간에는 **생성자 주입(Constructor Injection)**을 통해 서로 연결합니다.

### ② ControllerAdvice를 이용한 전역 예외 처리
**에러 처리 원칙:** 사용자에게 Raw Exception(`NullPointerException`, `IndexOutOfBoundsException` 등)을 그대로 노출하면 보안과 UX 모두 최악입니다.
`@RestControllerAdvice`를 사용해 스프링 부트 전체에서 발생하는 예외를 낚아채서, 정형화된 JSON 형태(에러 코드, 정제된 메시지)로 변환해 프론트엔드로 전달합니다. 

### ③ 계층별 DTO 분리
엔티티(DB 모델)나 도메인 객체를 절대로 Controller 밖으로 노출하지 않습니다. 오직 **DTO(Data Transfer Object)** 로 변환해서 주고받아야 합니다.

---

## 4. 실전 샘플 코드 (기존 메뉴얼 조회 RAG 서비스 대비)

### 1) Controller (FastAPI의 api/endpoints)
```java
package com.example.vehiclebot.controller;

import com.example.vehiclebot.dto.ManualRequest;
import com.example.vehiclebot.dto.ManualResponse;
import com.example.vehiclebot.service.ManualService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController // @Controller + @ResponseBody: JSON 형태로 결과를 반환하는 REST API용 컨트롤러임을 선언
@RequestMapping("/api/v1/manuals") // 해당 컨트롤러의 모든 API가 가질 공통 경로 접두사 지정
@RequiredArgsConstructor // Lombok: final이 붙은 필드를 인자로 받는 생성자를 자동으로 생성 (생성자 주입 방식의 DI에 활용)
public class ManualController {

    private final ManualService manualService;

    // @PostMapping: HTTP POST 요청을 처리하도록 매핑. FastAPI의 @router.post("/")와 동일
    @PostMapping("/search")
    public ResponseEntity<ManualResponse> searchManual(
            @RequestBody ManualRequest request) { // @RequestBody: HTTP 요청 본문(JSON)을 자바 객체로 역직렬화
        
        ManualResponse response = manualService.answerQuestion(request);
        return ResponseEntity.ok(response); // 성공 시 HTTP 200 OK와 함께 응답 객체 반환
    }
}
```

### 2) Service (비즈니스 로직, FastAPI의 services)
```java
package com.example.vehiclebot.service;

import com.example.vehiclebot.dto.ManualRequest;
import com.example.vehiclebot.dto.ManualResponse;
import com.example.vehiclebot.repository.ManualRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j // Lombok: 로깅 객체(log)를 자동으로 생성해줌
@Service // 해당 클래스가 비즈니스 로직을 수행하는 서비스 계층임을 선언 (Spring Bean으로 등록됨)
@RequiredArgsConstructor // final 필드에 대한 생성자 주입 자동화
public class ManualService {

    private final ManualRepository manualRepository;
    private final AiClient aiClient;

    public ManualResponse answerQuestion(ManualRequest request) {
        try {
            // 1. Vector DB에서 관련 문서 조회
            String context = manualRepository.findRelevantDocs(request.getQuery());

            // 2. LLM 질의 (외부 API 연동)
            String answer = aiClient.generateAnswer(request.getQuery(), context);

            // 3. 응답 DTO 반환
            return new ManualResponse(answer);

        } catch (Exception e) {
            // 에러 처리 원칙: 내부 로깅은 상세히(log.error), 사용자 응답은 정제해서 송출
            log.error("Failed to generate answer for query: {}", request.getQuery(), e);
            throw new CustomAiProcessingException("답변 생성 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.");
        }
    }
}
```

### 3) Request/Response DTO (FastAPI의 Pydantic 모델)
```java
package com.example.vehiclebot.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * 질문 요청 DTO
 */
@Getter // Lombok: 모든 필드에 대해 Getter 메서드(getQuery, getUserId) 자동 생성
@NoArgsConstructor // Lombok: 인자가 없는 기본 생성자 자동 생성 (JSON 역직렬화 시 필수)
@AllArgsConstructor // Lombok: 모든 필드를 인자로 받는 생성자 자동 생성
public class ManualRequest {
    private String query;
    private String userId;
}

/**
 * 답변 응답 DTO
 */
@Getter // Getter 메서드 자동 생성
@AllArgsConstructor // 모든 필드 인자 생성자 자동 생성
public class ManualResponse {
    private String answer;
    private List<String> sourceDocuments;
}
```

### 4) Repository (데이터 접근 계층, FastAPI의 repositories)
```java
package com.example.vehiclebot.repository;

import org.springframework.stereotype.Repository;

@Repository // 해당 클래스가 데이터 접근 계층(데이터베이스/외부저장소 통신)임을 선언
public interface ManualRepository {
    String findRelevantDocs(String query);
}

// ---------------------------------------------------------
// 실제 구현체
// ---------------------------------------------------------
@Repository // 구현 클래스에도 계층 어노테이션 지정
@RequiredArgsConstructor // 의존성 주입 자동 생성자
public class ManualRepositoryImpl implements ManualRepository {
    
    // private final VectorDbClient vectorDbClient;

    @Override // 부모 인터페이스의 메서드를 재정의함을 명시
    public String findRelevantDocs(String query) {
        return "조회된 메뉴얼 내용...";
    }
}
```

### 5) Global Exception Handler (FastAPI의 Exception Handler)
```java
package com.example.vehiclebot.exception;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice // @ControllerAdvice + @ResponseBody: 모든 컨트롤러에서 발생하는 예외를 한 곳에서 잡아 JSON으로 반환
public class GlobalExceptionHandler {

    // @ExceptionHandler: 특정 예외가 발생했을 때 이 메서드가 처리하도록 지정
    @ExceptionHandler(CustomAiProcessingException.class)
    public ResponseEntity<ErrorResponse> handleAiException(CustomAiProcessingException ex) {
        return ResponseEntity
                .status(503) // 503 Service Unavailable 응답 설정
                .body(new ErrorResponse("AI_ERROR_01", ex.getMessage()));
    }
}
```

---

## 요약

*   주니어 시절 작성하셨던 Controller-Service-Repository 뼈대는 **지금도 여전히 강력한 표준**입니다.
*   Spring Boot는 이 뼈대가 돌아가게 만들기 위해 필요했던 수많은 인프라 세팅(WAS 세팅, XML 설정)을 **삭제하고 자동화**한 도구입니다.
*   현재 만드신 **FastAPI RAG 프로젝트 경로 구조**는 Spring Boot 패키지 구조와 사상이 정확히 일치하므로, 언어의 문법(Python -> Java)만 바뀐다고 생각하시면 이해하기 매우 쉽습니다.
; // 필요시 사용자 식별 정보 추가
}

/**
 * 답변 응답 DTO
 */
 ```java
@Getter
@AllArgsConstructor
public class ManualResponse {
    private String answer;
    private List<String> sourceDocuments; // 참고한 문서 리스트 추가 가능
}
```

### 4) Repository (데이터 접근 계층, FastAPI의 repositories)
Spring Data JPA를 사용하면 인터페이스 선언만으로 기본적인 CRUD가 가능합니다. RAG의 경우 Vector DB 조회를 위한 커스텀 로직이 포함될 수 있습니다.

```java
package com.example.vehiclebot.repository;

import org.springframework.stereotype.Repository;

@Repository
public interface ManualRepository {
    /**
     * 질문과 관련된 문서를 Vector DB에서 검색합니다.
     */
    String findRelevantDocs(String query);
}

// ---------------------------------------------------------
// 실제 구현체 (예: ChromaDB나 Pinecone 연동 시)
// ---------------------------------------------------------
@Repository
@RequiredArgsConstructor
public class ManualRepositoryImpl implements ManualRepository {
    
    // private final VectorDbClient vectorDbClient;

    @Override
    public String findRelevantDocs(String query) {
        // 실제 Vector DB 검색 로직이 들어가는 자리
        return "조회된 메뉴얼 내용 컨텍스트...";
    }
}
```

### 5) Global Exception Handler (FastAPI의 Exception Handler)
이 부분이 Spring Boot를 매우 우아하게 만들어주는 기술입니다.
```java
package com.example.vehiclebot.exception;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(CustomAiProcessingException.class)
    public ResponseEntity<ErrorResponse> handleAiException(CustomAiProcessingException ex) {
        // HTTP 503 Service Unavailable 로 프론트엔드에 응답
        return ResponseEntity
                .status(503)
                .body(new ErrorResponse("AI_ERROR_01", ex.getMessage()));
    }
}
```


## 요약

*   주니어 시절 작성하셨던 Controller-Service-Repository 뼈대는 **지금도 여전히 강력한 표준**입니다.
*   Spring Boot는 이 뼈대가 돌아가게 만들기 위해 필요했던 수많은 인프라 세팅(WAS 세팅, XML 설정)을 **삭제하고 자동화**한 도구입니다.
*   현재 만드신 **FastAPI RAG 프로젝트 경로 구조**는 Spring Boot 패키지 구조와 사상이 정확히 일치하므로, 언어의 문법(Python -> Java)만 바뀐다고 생각하시면 이해하기 매우 쉽습니다.
