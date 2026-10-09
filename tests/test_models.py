"""Параметры порций и упаковок, остаток доз и формат отображения."""

from dataclasses import FrozenInstanceError

import pytest

from game.models import Food, Medicine


@pytest.mark.parametrize('uses, empty', [(0, False), (1, False), (2, True)])
def test_medicine_remaining_uses(uses: int, empty: bool) -> None:
    medicine = Medicine('Лекарство', 15, 20, 2, uses=uses)
    assert medicine.is_empty() is empty


@pytest.mark.parametrize('uses', [-1, 3])
def test_medicine_rejects_invalid_uses(uses: int) -> None:
    with pytest.raises(ValueError):
        Medicine('Лекарство', 15, 20, 2, uses=uses)


@pytest.mark.parametrize(
    'price, healing, doses', [(-1, 20, 2), (15, -1, 2), (15, 20, 0)],
)
def test_invalid_medicine_parameters(
    price: int, healing: int, doses: int,
) -> None:
    with pytest.raises(ValueError):
        Medicine('Лекарство', price, healing, doses)


@pytest.mark.parametrize('satiety, price', [(0, 10), (-1, 10), (20, -1)])
def test_invalid_food_parameters(satiety: int, price: int) -> None:
    with pytest.raises(ValueError):
        Food('Корм', satiety, price)


def test_food_is_immutable(food: Food) -> None:
    with pytest.raises(FrozenInstanceError):
        food.price = 100


def test_item_descriptions(food: Food, medicine: Medicine) -> None:
    assert repr(food) == 'Корм стоимость: 10, утоляет голод на 20 единиц'
    assert repr(medicine) == (
        'Лекарство стоимость: 15, лечит на 20 HP, использований: 2/2'
    )
