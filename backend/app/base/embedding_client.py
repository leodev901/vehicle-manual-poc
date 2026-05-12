import httpx

from app.base.http_client import get_httpx_client
from app.base.logger import logger
from app.core.config import settings
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.retry import retry_async


class EmbeddingClient:
    """
    HuggingFace Inference API 또는 로컬 임베딩 서버와 통신하는 클라이언트입니다.
    """

    def __init__(self):
        self.url = settings.HF_INFERENCE_URL
        self.token = settings.HF_TOKEN

        # CircuitBreaker는 실패 횟수를 누적해 사용해야 하므로 객체에 선언
        self.breaker = CircuitBreaker(
            name="hf_embedding",
            failure_threshold=5,
            recovery_timeout_seconds=30.0,
        )



    async def get_embedding(self, text: str) -> list[float]:
        """서킷 브레이커 call"""
        return await self.breaker.call(
            lambda: retry_async(
                "hf_embedding",
                lambda: self._request_embedding(text),
                max_attempts=3,
                base_delay_seconds=0.5
            )
        )

    async def _request_embedding(self, text: str) -> list[float]:
        """
        텍스트를 벡터로 변환합니다.
        """
        
        client = await get_httpx_client()
        
        payload = {
            "text": text,
        }
        
        try:
            response = await client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.token}"
                },
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            query_vector = result.get("embedding")
            
            if not query_vector:
                logger.error(f"Embedding failed: No vector in response. {result}")
                raise ValueError("임베딩 서버에서 벡터를 생성하지 못했습니다.")
                
            return query_vector

        except httpx.HTTPStatusError as exc:
            # 4xx/5xx 응답은 여기로 들어옵니다.
            # 로그에는 상태 코드를 남겨야 장애 원인을 구분할 수 있습니다.
            logger.error(f"Embedding Server API error: {exc.response.status_code} - {exc.response.text}")
            raise
        except httpx.HTTPError as exc:
            # timeout, connect error 등 네트워크 계열 오류입니다.
            logger.error(f"Embedding server request failed: {type(exc).__name__}")
            raise ValueError("임베딩 서버에 연결할 수 없습니다.") from exc

        except Exception as e:
            logger.error(f"Unexpected error during embedding: {str(e)}")
            raise

# module-level singleton
# 같은 프로세스 안에서는 이 객체 하나를 계속 재사용합니다.
embedding_client = EmbeddingClient()