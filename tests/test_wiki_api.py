import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _mock_response(data, status=200):
    resp = MagicMock()
    resp.getcode.return_value = status

    import json

    resp.read.return_value = json.dumps(data).encode()
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = None
    return resp


def _reload_module(monkeypatch):
    """Reload ``utils.wiki_api`` so env changes take effect."""

    import utils.wiki_api as wiki_api

    importlib.reload(wiki_api)
    return wiki_api


def test_get_mapping_uses_cache(monkeypatch):
    wiki_api = _reload_module(monkeypatch)
    mock_resp = _mock_response([{"id": 1, "name": "Item"}])
    with patch("utils.wiki_api.request.urlopen", return_value=mock_resp) as mock_get:
        data1 = wiki_api.get_mapping()
        data2 = wiki_api.get_mapping()
        assert mock_get.call_count == 1
        assert data1 == data2


def test_user_agent_from_env(monkeypatch):
    monkeypatch.setenv("USER_AGENT", "TEST-AGENT")
    wiki_api = _reload_module(monkeypatch)
    mock_resp = _mock_response({"data": {}})
    with patch("utils.wiki_api.request.urlopen", return_value=mock_resp) as mock_get:
        wiki_api.get_latest()
        req = mock_get.call_args.args[0]
        headers = {k.lower(): v for k, v in req.header_items()}
        assert headers["user-agent"] == "TEST-AGENT"


def test_get_timeseries_dataframe(monkeypatch):
    wiki_api = _reload_module(monkeypatch)
    mock_resp = _mock_response(
        {"data": [{"timestamp": 0, "avgHighPrice": 10, "avgLowPrice": 8}]}
    )
    with patch("utils.wiki_api.request.urlopen", return_value=mock_resp):
        data = wiki_api.get_timeseries(1, "1h")

    assert data == [
        {"timestamp": "1970-01-01 00:00:00", "avgHighPrice": 10, "avgLowPrice": 8}
    ]


def test_get_timeseries_bad_timestep(monkeypatch):
    wiki_api = _reload_module(monkeypatch)
    with pytest.raises(ValueError):
        wiki_api.get_timeseries(1, "bad")

