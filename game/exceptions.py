"""Ожидаемые ошибки игровых действий."""


class TamagochiIsGone(Exception):
    """Здоровье питомца упало ниже нуля; игра завершена."""


class NotEnoughMoney(Exception):
    """Монет недостаточно для выбранной покупки."""


class ItemNotFoundError(Exception):
    """Каталог или нужный раздел инвентаря пуст."""


class InvalidItemError(ValueError):
    """Номер предмета выходит за границы списка."""


class MedicineIsEmptyError(Exception):
    """Все дозы лекарства уже использованы."""
