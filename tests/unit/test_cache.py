"""Unit tests for cache utilities"""
from unittest.mock import patch, MagicMock

import utils.cache as cache_mod


class TestCache:
    def setup_method(self):
        cache_mod._redis_client = None
        cache_mod._redis_checked = False

    def test_cache_disabled_returns_none(self):
        with patch.dict('os.environ', {'CACHE_ENABLED': 'false'}):
            cache_mod._redis_checked = False
            cache_mod._redis_client = None
            assert cache_mod.cache_get('key') is None
            assert cache_mod.cache_set('key', 'val') is False

    def test_cache_get_set_with_mock_redis(self):
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"a": 1}'
        mock_redis.setex.return_value = True
        with patch.dict('os.environ', {'CACHE_ENABLED': 'true'}):
            cache_mod._redis_checked = True
            cache_mod._redis_client = mock_redis
            assert cache_mod.cache_get('k') == '{"a": 1}'
            assert cache_mod.cache_get_json('k') == {'a': 1}
            assert cache_mod.cache_set_json('k', {'b': 2}, 60) is True

    def test_invalidate_user_cache(self):
        mock_redis = MagicMock()
        mock_redis.scan_iter.return_value = iter(['fh:1', 'sp:1:30'])
        with patch.dict('os.environ', {'CACHE_ENABLED': 'true'}):
            cache_mod._redis_checked = True
            cache_mod._redis_client = mock_redis
            cache_mod.invalidate_user_cache(1)
            assert mock_redis.delete.called

    def test_redis_unavailable_fallback(self):
        with patch.dict('os.environ', {'CACHE_ENABLED': 'true', 'REDIS_URL': 'redis://invalid:6379/0'}):
            cache_mod._redis_checked = False
            cache_mod._redis_client = None
            with patch('redis.from_url', side_effect=ConnectionError('fail')):
                assert cache_mod._get_redis() is None
                assert cache_mod.cache_get('x') is None
