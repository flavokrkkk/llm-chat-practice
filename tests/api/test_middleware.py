import re

import pytest

pytestmark = pytest.mark.api

GENERATED_ID_RE = re.compile(r"[0-9a-f]{32}")


async def test_response_has_generated_request_id(client):
    r = await client.get("/health")

    assert r.status_code == 200, r.text
    assert GENERATED_ID_RE.fullmatch(r.headers["x-request-id"])


@pytest.mark.parametrize(
    "client_id",
    [
        pytest.param("test-abc-123", id="simple"),
        pytest.param("A_b-9", id="mixed_case_and_underscore"),
        pytest.param("f47ac10b-58cc-4372-a567-0e02b2c3d479", id="uuid_with_dashes"),
        pytest.param("a" * 64, id="max_length_64"),
    ],
)
async def test_valid_client_request_id_is_kept(client, client_id):
    r = await client.get("/health", headers={"X-Request-ID": client_id})

    assert r.status_code == 200, r.text
    assert r.headers["x-request-id"] == client_id


@pytest.mark.parametrize(
    "client_id",
    [
        pytest.param("a" * 65, id="too_long_65"),
        pytest.param("has space", id="space"),
        pytest.param("<script>", id="html"),
        pytest.param("dots.not.allowed", id="dot"),
        pytest.param("../../etc/passwd", id="path"),
        pytest.param("", id="empty"),
    ],
)
async def test_invalid_client_request_id_is_replaced(client, client_id):
    r = await client.get("/health", headers={"X-Request-ID": client_id})

    assert r.status_code == 200, r.text
    assert GENERATED_ID_RE.fullmatch(r.headers["x-request-id"])
