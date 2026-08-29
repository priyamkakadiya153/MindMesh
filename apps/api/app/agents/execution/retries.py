import asyncio
import random
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class RetryPolicy:
    @staticmethod
    async def execute_with_retry(
        func: Callable[..., Any],
        *args,
        retries: int = 3,
        initial_delay: float = 0.05,
        backoff_factor: float = 2.0,
        **kwargs
    ) -> Any:
        """Executes a function with exponential backoff and jitter retry policy."""
        delay = initial_delay
        last_exception = None

        for attempt in range(retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == retries:
                    break

                # Apply jitter to delay
                jitter = random.uniform(0, 0.1 * delay)
                sleep_time = delay + jitter
                logger.warning(
                    f"RetryPolicy: Attempt {attempt + 1} failed with error: {str(e)}. "
                    f"Retrying in {sleep_time:.3f} seconds..."
                )
                await asyncio.sleep(sleep_time)
                delay *= backoff_factor

        raise last_exception
