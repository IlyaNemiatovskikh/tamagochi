"""Проверка имён классов, методов, аргументов и декораторов."""

import ast
from pathlib import Path

import pytest

CONTRACTS = {
    'clicker': (
        'AbstractClicker',
        {
            '__init__': (('self',), ('abstractmethod',)),
            'click': (('self',), ('abstractmethod',)),
            'income_per_click': (('self',), ('property', 'abstractmethod')),
        },
    ),
    'game': (
        'AbstractGame',
        {
            '__init__': (
                ('self', 'tamagochi', 'clicker', 'all_food', 'all_medicine'),
                ('abstractmethod',),
            ),
            'work': (('self',), ('abstractmethod',)),
            'buy_food': (('self',), ('abstractmethod',)),
            'buy_medicine': (('self',), ('abstractmethod',)),
            'feed_tamagochi': (('self',), ('abstractmethod',)),
            'heal_tamagochi': (('self',), ('abstractmethod',)),
            'rest_tamagochi': (('self',), ('abstractmethod',)),
            'play_with_tamagochi': (('self',), ('abstractmethod',)),
            'get_status': (('self',), ('abstractmethod',)),
            'food': (('self',), ('property', 'abstractmethod')),
            'medicine': (('self',), ('property', 'abstractmethod')),
        },
    ),
    'tamagochi': (
        'AbstractTamagochi',
        {
            'feed': (('self', 'food'), ('abstractmethod',)),
            'play': (('self',), ('abstractmethod',)),
            'rest': (('self',), ('abstractmethod',)),
            'heal': (('self', 'medicine'), ('abstractmethod',)),
            'status': (('self',), ('property', 'abstractmethod')),
            'is_alive': (('self',), ('abstractmethod',)),
            'is_sick': (('self',), ('abstractmethod',)),
            'update': (('self',), ('abstractmethod',)),
        },
    ),
}


@pytest.mark.parametrize('module', CONTRACTS)
def test_abstract_contract(module: str) -> None:
    root = Path(__file__).resolve().parents[1]
    current = ast.parse((root / 'game' / f'{module}.py').read_text())
    class_name, expected_methods = CONTRACTS[module]
    current_class = next(
        node for node in current.body if isinstance(node, ast.ClassDef)
    )
    assert current_class.name == class_name
    methods = {
        node.name: node
        for node in current_class.body
        if isinstance(node, ast.FunctionDef)
    }
    for name, (arguments, decorators) in expected_methods.items():
        method = methods[name]
        assert (
            tuple(argument.arg for argument in method.args.args) == arguments
        )
        assert (
            tuple(
                ast.unparse(decorator) for decorator in method.decorator_list
            )
            == decorators
        )
