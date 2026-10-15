from types import SimpleNamespace

import pytest

from app.mesh import MeshGatewayError, MeshLLM, normalize_mesh_error


class ChangingProviderError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


@pytest.mark.parametrize(
    ('status', 'message', 'code', 'http_status', 'retryable'),
    [
        (401, 'old auth wording', 'mesh_authentication_failed', 401, False),
        (402, 'balance text version A', 'mesh_payment_required', 402, False),
        (429, 'completely different rate-limit body', 'mesh_rate_limited', 429, True),
        (503, '<html>upstream outage</html>', 'mesh_unavailable', 503, True),
    ],
)
def test_mesh_errors_use_status_not_provider_wording(status, message, code, http_status, retryable):
    error = normalize_mesh_error(ChangingProviderError(status, message))
    assert error.code == code
    assert error.status_code == http_status
    assert error.retryable is retryable
    assert message not in error.message


def test_mesh_invalid_json_has_stable_error():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='not json'))]
    )
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_kwargs: response)
        )
    )

    with pytest.raises(MeshGatewayError) as caught:
        MeshLLM(client=client).json('role', 'instruction', {})

    assert caught.value.code == 'mesh_invalid_response'
    assert caught.value.status_code == 502
    assert caught.value.retryable is True
