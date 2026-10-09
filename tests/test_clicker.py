"""Доход рассчитывается при клике, а чтение его не меняет."""

import pytest

from game.clicker import AbstractClicker, SimpleRandomClicker


@pytest.mark.parametrize('income', [0, 10, 20])
def test_fixed_income(income: int) -> None:
    clicker = SimpleRandomClicker(income, income)
    assert isinstance(clicker, AbstractClicker)
    assert clicker.income_per_click == 0
    assert clicker.click() is None
    assert clicker.income_per_click == income
    assert clicker.income_per_click == income


def test_random_income_is_sampled_on_click(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    earnings = iter([10, 20])
    monkeypatch.setattr(
        'game.clicker.random.randint', lambda lower, upper: next(earnings),
    )
    clicker = SimpleRandomClicker()
    clicker.click()
    assert clicker.income_per_click == 10
    assert clicker.income_per_click == 10
    clicker.click()
    assert clicker.income_per_click == 20


@pytest.mark.parametrize('lower, upper', [(-1, 10), (20, 10)])
def test_invalid_income_bounds(lower: int, upper: int) -> None:
    with pytest.raises(ValueError):
        SimpleRandomClicker(lower, upper)
