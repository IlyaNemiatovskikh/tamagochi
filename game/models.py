"""Еда и лекарства с ценой и эффектом применения."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Food:
    """Порция еды: название, насыщение и цена в монетах.

    Поля порции нельзя менять после создания. Несколько покупок
    могут ссылаться на один образец из каталога.
    """

    name: str
    satiety: int
    price: int

    def __post_init__(self) -> None:
        """Проверить значения полей.

        Raises:
            ValueError: насыщение неположительно или цена отрицательна.
        """
        if self.satiety <= 0 or self.price < 0:
            raise ValueError('Насыщение должно быть > 0, а цена >= 0.')

    def __repr__(self) -> str:
        """Вернуть название, цену и насыщение порции."""
        return (
            f'{self.name} стоимость: {self.price}, '
            f'утоляет голод на {self.satiety} единиц'
        )


@dataclass
class Medicine:
    """Упаковка лекарства с ограниченным числом доз.

    number_of_uses хранит число доз в полной упаковке, uses считает
    потраченные дозы. heal_hp задаёт прибавку к здоровью за одну дозу,
    ограниченную максимальным здоровьем питомца. Поля проверяются
    при создании; последующее присваивание не проверяет их границы.
    """

    name: str
    price: int
    heal_hp: int
    number_of_uses: int
    uses: int = 0

    def __post_init__(self) -> None:
        """Проверить значения полей.

        Raises:
            ValueError: цена или эффект отрицательны, доз нет либо
                uses выходит за пределы 0..number_of_uses.
        """
        if self.price < 0 or self.heal_hp < 0 or self.number_of_uses <= 0:
            raise ValueError('Цена и лечение >= 0, количество доз > 0.')
        if not 0 <= self.uses <= self.number_of_uses:
            raise ValueError('Число использованных доз вне границ упаковки.')

    def is_empty(self) -> bool:
        """Все дозы потрачены."""
        return self.uses >= self.number_of_uses

    def __repr__(self) -> str:
        """Вернуть название, цену, лечение и остаток доз."""
        return (
            f'{self.name} стоимость: {self.price}, '
            f'лечит на {self.heal_hp} HP, '
            f'использований: '
            f'{self.number_of_uses - self.uses}/{self.number_of_uses}'
        )
