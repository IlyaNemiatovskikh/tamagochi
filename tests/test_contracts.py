"""Сверка имён классов, методов, аргументов и декораторов с шаблоном."""

import ast
from pathlib import Path

import pytest


@pytest.mark.parametrize('module', ['clicker', 'game', 'tamagochi'])
def test_abstract_contract_matches_official_template(module: str) -> None:
    root = Path(__file__).resolve().parents[1]
    original = ast.parse(
        (root / 'sources' / 'official-template' / 'game'
         / f'{module}.py').read_text(),
    )
    current = ast.parse((root / 'game' / f'{module}.py').read_text())
    original_class = next(
        node for node in original.body if isinstance(node, ast.ClassDef)
    )
    current_class = next(
        node for node in current.body if isinstance(node, ast.ClassDef)
    )
    assert original_class.name == current_class.name
    methods = {
        node.name: node for node in current_class.body
        if isinstance(node, ast.FunctionDef)
    }
    # Проверяем методы шаблона; дополнительные методы допустимы.
    for method in original_class.body:
        if not isinstance(method, ast.FunctionDef):
            continue
        replacement = methods[method.name]
        assert [argument.arg for argument in replacement.args.args] == [
            argument.arg for argument in method.args.args
        ]
        assert [ast.dump(decorator) for decorator
                in replacement.decorator_list] == [
            ast.dump(decorator) for decorator in method.decorator_list
        ]
