"""Ходы игры, монеты, каталог и инвентарь."""

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any

from .clicker import AbstractClicker
from .exceptions import (
    InvalidItemError,
    ItemNotFoundError,
    MedicineIsEmptyError,
    NotEnoughMoney,
    TamagochiIsGone,
)
from .models import Food, Medicine
from .tamagochi import AbstractTamagochi


class AbstractGame(ABC):
    """Контракт игры с выбором предмета перед действием.

    Доступны каталоги all_food, all_medicine и питомец tamagochi.
    select_item расширяет шаблон для выбора через консольный интерфейс.
    Индекс начинается с нуля; по умолчанию выбран первый предмет.
    """

    tamagochi: AbstractTamagochi
    all_food: list[Food]
    all_medicine: list[Medicine]
    _selected_index: int = 0

    @abstractmethod
    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine],
    ) -> None:
        """Создать игру с питомцем, кликером и каталогами."""
        raise NotImplementedError

    def select_item(self, index: int) -> None:
        """Сохранить индекс для покупки или использования предмета.

        Индекс действует до следующего успешного выбора; покупка
        и использование предмета его не сбрасывают.

        Args:
            index: индекс в каталоге или инвентаре, начиная с 0.

        Raises:
            InvalidItemError: индекс отрицателен; верхнюю границу
                проверяет действие по соответствующему списку.
        """
        if index < 0:
            raise InvalidItemError(
                'Номер предмета не может быть отрицательным.',
            )
        self._selected_index = index

    @abstractmethod
    def work(self) -> int:
        """Выполнить рабочий ход и вернуть доход."""
        raise NotImplementedError

    @abstractmethod
    def buy_food(self) -> None:
        """Купить выбранную порцию еды."""
        raise NotImplementedError

    @abstractmethod
    def buy_medicine(self) -> None:
        """Купить выбранную упаковку лекарства."""
        raise NotImplementedError

    @abstractmethod
    def feed_tamagochi(self) -> None:
        """Скормить выбранную порцию."""
        raise NotImplementedError

    @abstractmethod
    def heal_tamagochi(self) -> None:
        """Применить выбранное лекарство."""
        raise NotImplementedError

    @abstractmethod
    def rest_tamagochi(self) -> None:
        """Дать питомцу отдохнуть."""
        raise NotImplementedError

    @abstractmethod
    def play_with_tamagochi(self) -> None:
        """Поиграть с питомцем."""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Показатели питомца и монеты словарём."""
        raise NotImplementedError

    @property
    @abstractmethod
    def food(self) -> list[Food]:
        """Купленные порции."""
        raise NotImplementedError

    @property
    @abstractmethod
    def medicine(self) -> list[Medicine]:
        """Купленные упаковки."""
        raise NotImplementedError


class SimpleGame(AbstractGame):
    """Игра завершает действие одним вызовом обновления у питомца.

    Выбор предмета и чтение состояния не расходуют ход. Отказ из-за
    неверного индекса, отсутствия предмета или нехватки монет
    сохраняет ресурсы и состояние питомца. Если питомец погибает
    при обновлении, уже выполненное действие не отменяется.
    """

    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine],
    ) -> None:
        """Создать игру с нулевым балансом и пустым инвентарём.

        Args:
            tamagochi: питомец с собственными правилами состояния.
            clicker: кликер для расчёта дохода.
            all_food: каталог еды; копируется только список.
            all_medicine: образцы упаковок для продажи; копируется
                только список. При покупке создаётся полная упаковка.
        """
        self.tamagochi = tamagochi
        self._clicker = clicker
        self.all_food = all_food.copy()
        self.all_medicine = all_medicine.copy()
        self._coins = 0
        self._food: list[Food] = []
        self._medicine: list[Medicine] = []
        self._selected_index = 0

    def work(self) -> int:
        """Получить доход кликера и завершить ход.

        Возвращает число заработанных монет.

        Raises:
            TamagochiIsGone: питомец погиб до или во время хода.
        """
        self._require_alive()
        self._clicker.click()
        income = self._clicker.income_per_click
        self._coins += income
        self._finish_turn()
        return income

    def buy_food(self) -> None:
        """Купить выбранную порцию за её цену и завершить ход.

        Raises:
            TamagochiIsGone: питомец погиб до или во время хода.
            ItemNotFoundError: каталог еды пуст.
            InvalidItemError: выбранного номера нет в каталоге.
            NotEnoughMoney: монет не хватает.
        """
        self._require_alive()
        self._check_selection(self.all_food)
        food = self.all_food[self._selected_index]
        if self._coins < food.price:
            raise NotEnoughMoney('Не хватает монет на эту еду.')
        self._coins -= food.price
        # Поля Food неизменяемы, поэтому образец можно не копировать.
        self._food.append(food)
        self._finish_turn()

    def buy_medicine(self) -> None:
        """Купить полную упаковку выбранного лекарства и завершить ход.

        Покупка создаёт копию образца с uses = 0.

        Raises:
            TamagochiIsGone: питомец погиб до или во время хода.
            ItemNotFoundError: каталог лекарств пуст.
            InvalidItemError: выбранного номера нет в каталоге.
            NotEnoughMoney: монет не хватает.
            ValueError: цена или эффект образца стали отрицательными
                либо число доз стало неположительным. При создании
                упаковки эти поля проверяются повторно.
        """
        self._require_alive()
        self._check_selection(self.all_medicine)
        medicine = self.all_medicine[self._selected_index]
        if self._coins < medicine.price:
            raise NotEnoughMoney('Не хватает монет на это лекарство.')
        # У каждой покупки свой счётчик доз, даже при общем образце.
        purchased = replace(medicine, uses=0)
        self._coins -= medicine.price
        self._medicine.append(purchased)
        self._finish_turn()

    def feed_tamagochi(self) -> None:
        """Накормить питомца выбранной порцией и завершить ход.

        Съеденная порция удаляется из сумки.

        Raises:
            TamagochiIsGone: питомец погиб до или во время хода.
            ItemNotFoundError: еды в сумке нет.
            InvalidItemError: выбранного номера нет в сумке.
        """
        self._require_alive()
        self._check_selection(self._food)
        self.tamagochi.feed(self._food[self._selected_index])
        self._food.pop(self._selected_index)
        self._finish_turn()

    def heal_tamagochi(self) -> None:
        """Применить выбранное лекарство и завершить ход.

        После последней дозы упаковка удаляется из сумки.
        При отказе из-за пустой упаковки ход не расходуется.

        Raises:
            TamagochiIsGone: питомец погиб до или во время хода.
            ItemNotFoundError: лекарств в сумке нет.
            InvalidItemError: выбранного номера нет в сумке.
            MedicineIsEmptyError: у выбранной упаковки нет доз.
        """
        self._require_alive()
        self._check_selection(self._medicine)
        medicine = self._medicine[self._selected_index]
        if medicine.is_empty():
            raise MedicineIsEmptyError('В этой упаковке закончились дозы.')
        self.tamagochi.heal(medicine)
        if medicine.is_empty():
            self._medicine.pop(self._selected_index)
        self._finish_turn()

    def rest_tamagochi(self) -> None:
        """Дать питомцу отдохнуть и завершить ход.

        Raises:
            TamagochiIsGone: питомец погиб до или во время хода.
        """
        self._require_alive()
        self.tamagochi.rest()
        self._finish_turn()

    def play_with_tamagochi(self) -> None:
        """Поиграть с питомцем и завершить ход.

        Raises:
            TamagochiIsGone: питомец погиб до или во время хода.
        """
        self._require_alive()
        self.tamagochi.play()
        self._finish_turn()

    def get_status(self) -> dict[str, Any]:
        """Показатели питомца и баланс монет.

        Чтение не расходует ход и доступно после смерти питомца.
        """
        return {**self.tamagochi.status, 'coins': self._coins}

    @property
    def food(self) -> list[Food]:
        """Копия списка еды; ход не расходуется."""
        return self._food.copy()

    @property
    def medicine(self) -> list[Medicine]:
        """Копия списка упаковок; сами упаковки не копируются."""
        return self._medicine.copy()

    def _check_selection(self, items: list[Food] | list[Medicine]) -> None:
        """Проверить выбранный индекс по списку items.

        Raises:
            ItemNotFoundError: список пуст.
            InvalidItemError: выбранного индекса нет в списке.
        """
        if not items:
            raise ItemNotFoundError('В этом списке пока нет предметов.')
        if not 0 <= self._selected_index < len(items):
            raise InvalidItemError('Предмета с таким номером нет.')

    def _require_alive(self) -> None:
        """Проверить возможность хода.

        Raises:
            TamagochiIsGone: питомец уже погиб.
        """
        if not self.tamagochi.is_alive():
            raise TamagochiIsGone('Питомец погиб. Игра окончена.')

    def _finish_turn(self) -> None:
        """Обновить питомца один раз и проверить конец игры.

        Изменения действия сохраняются, даже если обновление
        завершает игру.

        Raises:
            TamagochiIsGone: питомец погиб до или во время обновления.
        """
        self.tamagochi.update()
        self._require_alive()
