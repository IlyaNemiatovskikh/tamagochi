"""Независимые начальные состояния для проверок игры."""

import pytest

from game.clicker import SimpleRandomClicker
from game.game import SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi


@pytest.fixture(autouse=True)
def prevent_random_sickness(monkeypatch: pytest.MonkeyPatch) -> None:
    # Болезнь наступает при random() < 0.1; 0.99 её исключает.
    monkeypatch.setattr('game.tamagochi.random.random', lambda: 0.99)


@pytest.fixture
def food() -> Food:
    return Food('Корм', satiety=20, price=10)


@pytest.fixture
def medicine() -> Medicine:
    return Medicine('Лекарство', price=15, heal_hp=20, number_of_uses=2)


@pytest.fixture
def tamagochi() -> SimpleTamagochi:
    return SimpleTamagochi()


@pytest.fixture
def game(
    tamagochi: SimpleTamagochi, food: Food, medicine: Medicine,
) -> SimpleGame:
    """Игра с фиксированным доходом 20 монет за ход."""
    return SimpleGame(
        tamagochi, SimpleRandomClicker(20, 20),
        [food, Food('Малый корм', satiety=10, price=5)], [medicine],
    )
