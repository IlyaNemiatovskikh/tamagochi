"""Консольные команды, ошибки ввода и штатный выход."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from game.clicker import SimpleRandomClicker
from game.game import SimpleGame
from game.tamagochi import SimpleTamagochi
from main import run_game


def test_console_all_actions(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = iter([
        '1', '1', '2', '1', '4', '1', '3', '1', '5', '1',
        '5', '1', '6', '7', '8', '0',
    ])
    monkeypatch.setattr('builtins.input', lambda prompt: next(commands))
    run_game(game)
    output = capsys.readouterr().out
    for message in (
        'Еда куплена.', 'Питомец поел.', 'Лекарство куплено.',
        'Питомец получил лекарство.', 'Вы поиграли с питомцем.',
        'Питомец отдохнул.', 'До встречи!',
    ):
        assert message in output
    assert game.food == game.medicine == []
    assert game.get_status()['coins'] == 15
    assert game.get_status()['hunger'] == 50


def test_bad_input_cancellation_and_missing_items_do_not_spend_turn(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = iter(['?', '2', 'abc', '2', '-1', '2', '99', '2', '0',
                     '4', '5', '8', '0'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(commands))
    status = game.get_status()
    run_game(game)
    output = capsys.readouterr().out
    assert 'Неверная команда.' in output
    assert 'Введите целое число.' in output
    assert 'Предмета с таким номером нет.' in output
    assert 'В этом списке пока нет предметов.' in output
    assert game.get_status() == status


def test_console_recovers_from_insufficient_money(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = iter(['2', '1', '1', '0'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(commands))
    run_game(game)
    assert 'Не хватает монет' in capsys.readouterr().out
    assert game.get_status()['coins'] == 20
    assert game.get_status()['hunger'] == 25


@pytest.mark.parametrize('interruption', [EOFError, KeyboardInterrupt])
def test_console_input_interruption(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], interruption: type[BaseException],
) -> None:
    monkeypatch.setattr('builtins.input', Mock(side_effect=interruption))
    run_game(game)
    assert 'Игра остановлена.' in capsys.readouterr().out


def test_console_stops_on_death(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    game = SimpleGame(
        SimpleTamagochi(hp=0, hunger=75), SimpleRandomClicker(20, 20), [], [],
    )
    monkeypatch.setattr('builtins.input', lambda prompt: '1')
    run_game(game)
    assert 'Игра окончена.' in capsys.readouterr().out
    assert not game.tamagochi.is_alive()


def test_console_does_not_hide_programming_errors(
    game: SimpleGame, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr('builtins.input', lambda prompt: '1')
    monkeypatch.setattr(game, 'work', Mock(side_effect=RuntimeError('bug')))
    with pytest.raises(RuntimeError, match='bug'):
        run_game(game)


def test_launch_without_site_packages() -> None:
    root = Path(__file__).resolve().parents[1]
    process = subprocess.run(
        [sys.executable, '-S', 'main.py'], input='1\n8\n0\n',
        text=True, capture_output=True, cwd=root, timeout=10, check=True,
    )
    assert 'Вы заработали' in process.stdout
    assert 'До встречи!' in process.stdout
    assert process.stderr == ''
