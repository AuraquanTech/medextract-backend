from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=0.2, min=0.5, max=8),
       retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)))
async def resilient_get(client: httpx.AsyncClient, url: str, **kw):
    r = await client.get(url, **kw)
    r.raise_for_status()
    return r
