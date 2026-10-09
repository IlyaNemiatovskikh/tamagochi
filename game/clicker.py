"""Расчёт дохода за один рабочий ход."""

import random
from abc import ABC, abstractmethod


class AbstractClicker(ABC):
    """Контракт кликера: выполнить клик и прочитать его доход."""

    @abstractmethod
    def __init__(self) -> None:
        """Подготовить кликер."""
        raise NotImplementedError

    @abstractmethod
    def click(self) -> None:
        """Рассчитать доход клика."""
        raise NotImplementedError

    @property
    @abstractmethod
    def income_per_click(self) -> int:
        """Доход последнего клика."""
        raise NotImplementedError


class SimpleRandomClicker(AbstractClicker):
    """Кликер со случайным доходом в заданных границах."""

    def __init__(
        self, min_income: int = 10, max_income: int = 20,
    ) -> None:
        """Задать границы случайного дохода.

        Args:
            min_income: нижняя граница дохода, включительно.
            max_income: верхняя граница дохода, включительно.

        Raises:
            ValueError: границы отрицательны или перепутаны.
        """
        if not 0 <= min_income <= max_income:
            raise ValueError('Нужны границы 0 <= min_income <= max_income.')
        self._min_income = min_income
        self._max_income = max_income
        self._income_per_click = 0

    def click(self) -> None:
        """Рассчитать и сохранить доход клика в заданных границах."""
        self._income_per_click = random.randint(
            self._min_income, self._max_income,
        )

    @property
    def income_per_click(self) -> int:
        """Доход последнего клика; до первого клика — 0."""
        return self._income_per_click
