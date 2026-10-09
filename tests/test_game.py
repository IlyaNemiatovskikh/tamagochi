"""Монеты, инвентарь и границы игрового хода."""

from unittest.mock import Mock

import pytest

from game.clicker import SimpleRandomClicker
from game.exceptions import (
    InvalidItemError,
    ItemNotFoundError,
    NotEnoughMoney,
    TamagochiIsGone,
)
from game.game import SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi


def test_purchase_spends_exact_price(game: SimpleGame, food: Food) -> None:
    assert game.work() == 20
    game.buy_food()
    assert game.food == [food]
    assert game.get_status()['coins'] == 10
    assert game.get_status()['hunger'] == 30


def test_purchase_with_exact_balance(game: SimpleGame) -> None:
    game.work()
    game.buy_food()
    game.buy_food()
    assert game.get_status()['coins'] == 0
    assert len(game.food) == 2


def test_selected_food_is_purchased_and_consumed(game: SimpleGame) -> None:
    game.work()
    game.select_item(1)
    game.buy_food()
    assert game.food == [game.all_food[1]]
    assert game.get_status()['coins'] == 15
    game.select_item(0)
    game.feed_tamagochi()
    assert game.food == []
    assert game.get_status()['hunger'] == 25


@pytest.mark.parametrize('action', ['buy_food', 'buy_medicine'])
def test_insufficient_funds_do_not_spend_turn(
    game: SimpleGame, action: str,
) -> None:
    status = game.get_status()
    with pytest.raises(NotEnoughMoney):
        getattr(game, action)()
    assert game.get_status() == status
    assert game.food == game.medicine == []


@pytest.mark.parametrize('action', ['feed_tamagochi', 'heal_tamagochi'])
def test_missing_item_does_not_spend_turn(
    game: SimpleGame, action: str,
) -> None:
    status = game.get_status()
    with pytest.raises(ItemNotFoundError):
        getattr(game, action)()
    assert game.get_status() == status


@pytest.mark.parametrize('action', ['buy_food', 'buy_medicine'])
def test_empty_catalog(
    food: Food, medicine: Medicine, action: str,
) -> None:
    game = SimpleGame(
        SimpleTamagochi(), SimpleRandomClicker(),
        [] if action == 'buy_food' else [food],
        [] if action == 'buy_medicine' else [medicine],
    )
    with pytest.raises(ItemNotFoundError):
        getattr(game, action)()


def test_invalid_selection_has_no_effect(game: SimpleGame) -> None:
    game.work()
    status = game.get_status()
    with pytest.raises(InvalidItemError):
        game.select_item(-1)
    game.select_item(99)
    with pytest.raises(InvalidItemError):
        game.buy_food()
    assert game.get_status() == status
    assert game.food == []


def test_medicine_purchases_are_independent(
    game: SimpleGame, medicine: Medicine,
) -> None:
    game.work()
    game.work()
    game.buy_medicine()
    game.buy_medicine()
    first, second = game.medicine
    assert first is not second and first is not medicine
    game.heal_tamagochi()
    assert first.uses == 1
    assert second.uses == medicine.uses == 0
    assert game.get_status()['coins'] == 10
    game.heal_tamagochi()
    assert first.uses == first.number_of_uses == 2
    assert game.medicine == [second]


def test_inventory_lists_are_copies(game: SimpleGame) -> None:
    game.work()
    game.buy_food()
    game.work()
    game.buy_medicine()
    game.food.clear()
    game.medicine.clear()
    assert len(game.food) == len(game.medicine) == 1


@pytest.mark.parametrize(
    'action',
    ['work', 'buy_food', 'buy_medicine', 'feed_tamagochi',
     'heal_tamagochi', 'play_with_tamagochi', 'rest_tamagochi'],
)
def test_each_action_updates_once(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch, action: str,
) -> None:
    game.work()
    game.work()
    game.work()
    game.buy_food()
    game.buy_medicine()
    update = Mock(wraps=game.tamagochi.update)
    monkeypatch.setattr(game.tamagochi, 'update', update)
    getattr(game, action)()
    update.assert_called_once_with()


def test_reading_and_selection_do_not_update(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch,
) -> None:
    update = Mock(wraps=game.tamagochi.update)
    monkeypatch.setattr(game.tamagochi, 'update', update)
    game.get_status()
    game.food
    game.medicine
    game.select_item(1)
    update.assert_not_called()


def test_terminal_turn_commits_income(food: Food, medicine: Medicine) -> None:
    game = SimpleGame(
        SimpleTamagochi(hp=5, hunger=75), SimpleRandomClicker(20, 20),
        [food], [medicine],
    )
    game.work()
    assert game.get_status()['hp'] == 0
    with pytest.raises(TamagochiIsGone):
        game.work()
    assert game.get_status()['hp'] < 0
    assert game.get_status()['coins'] == 40
    with pytest.raises(TamagochiIsGone):
        game.work()
    assert game.get_status()['coins'] == 40


@pytest.mark.parametrize(
    'action',
    ['work', 'buy_food', 'buy_medicine', 'feed_tamagochi',
     'heal_tamagochi', 'play_with_tamagochi', 'rest_tamagochi'],
)
def test_dead_pet_blocks_all_game_actions(
    food: Food, medicine: Medicine, action: str,
) -> None:
    game = SimpleGame(
        SimpleTamagochi(hp=-1), SimpleRandomClicker(), [food], [medicine],
    )
    with pytest.raises(TamagochiIsGone):
        getattr(game, action)()
    assert game.get_status()['coins'] == 0


def test_game_handles_a_pet_that_does_not_raise_on_death(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        game.tamagochi, 'is_alive', Mock(side_effect=[True, False]),
    )
    monkeypatch.setattr(game.tamagochi, 'update', Mock())
    with pytest.raises(TamagochiIsGone):
        game.work()
