from prometheus_client import Counter, Histogram, Gauge
REQUESTS = Counter("http_requests_total", "HTTP requests", ["path","method","status"])
LATENCY = Histogram("http_request_seconds","Latency",["path","method"])
CACHE_HITS = Counter("cache_hits_total","Cache hits",["key"])
CIRCUIT_OPEN = Gauge("circuit_open", "Open circuit flag", ["name"])
