from src.service.security import SlidingWindowRateLimiter, is_api_key_valid


def test_api_key_validation() -> None:
    assert is_api_key_valid("abc", "abc") is True
    assert is_api_key_valid("abc", "xyz") is False
    assert is_api_key_valid(None, "xyz") is False


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = SlidingWindowRateLimiter(limit_per_minute=2)
    assert limiter.allow("client-1")[0] is True
    assert limiter.allow("client-1")[0] is True
    allowed, retry_after = limiter.allow("client-1")
    assert allowed is False
    assert retry_after >= 1
