import pytest

from app.agent.tools.recipient import mask_name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        pytest.param("Иван Петров", "Иван П.", id="first_and_last"),
        pytest.param("Иван", "Иван", id="single_word"),
        pytest.param("Иван Петрович Сидоров", "Иван С.", id="with_patronymic"),
        pytest.param(" Иван Петров ", "Иван П.", id="extra_spaces"),
        pytest.param("", "клиент банка", id="empty"),
    ],
)
def test_mask_name(name, expected):
    assert mask_name(name) == expected
