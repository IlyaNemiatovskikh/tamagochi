"""Состояние питомца и эффекты ухода за ним."""

import random
from abc import ABC, abstractmethod

from .exceptions import MedicineIsEmptyError, TamagochiIsGone
from .models import Food, Medicine


class AbstractTamagochi(ABC):
    """Контракт питомца; действия и обновление хода разделены."""

    @abstractmethod
    def feed(self, food: Food) -> None:
        """Накормить питомца."""
        raise NotImplementedError

    @abstractmethod
    def play(self) -> None:
        """Поиграть с питомцем."""
        raise NotImplementedError

    @abstractmethod
    def rest(self) -> None:
        """Дать питомцу отдохнуть."""
        raise NotImplementedError

    @abstractmethod
    def heal(self, medicine: Medicine) -> None:
        """Применить лекарство."""
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> dict[str, int]:
        """Показатели питомца словарём."""
        raise NotImplementedError

    @abstractmethod
    def is_alive(self) -> bool:
        """Проверить, жив ли питомец."""
        raise NotImplementedError

    @abstractmethod
    def is_sick(self) -> bool:
        """Проверить, болен ли питомец."""
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        """Обновить состояние за ход; вызывается игрой после действия."""
        raise NotImplementedError


class SimpleTamagochi(AbstractTamagochi):
    """Питомец с голодом, усталостью, энергией и риском болезни.

    Голод, усталость и энергия ограничены шкалой 0..100.
    Здоровье не превышает 100; значение ниже нуля означает смерть.
    Эффекты ухода и обновление хода применяются отдельно.
    """

    def __init__(
        self,
        hp: int = 100,
        hunger: int = 20,
        fatigue: int = 0,
        energy: int = 100,
        sick: bool = False,
    ) -> None:
        """Задать начальное состояние питомца.

        Args:
            hp: здоровье не выше 100; при нуле питомец жив,
                отрицательное значение означает смерть.
            hunger: голод в пределах 0..100.
            fatigue: усталость в пределах 0..100.
            energy: энергия в пределах 0..100.
            sick: болен ли питомец.

        Raises:
            ValueError: hp выше 100 либо hunger, fatigue или energy
                выходит за пределы 0..100.
        """
        if hp > 100 or any(
            not 0 <= value <= 100 for value in (hunger, fatigue, energy)
        ):
            raise ValueError('Показатели должны быть в пределах шкалы.')
        self._hp = hp
        self._hunger = hunger
        self._fatigue = fatigue
        self._energy = energy
        self._sick = sick

    def feed(self, food: Food) -> None:
        """Снизить голод на насыщение порции и потратить до 2 энергии.

        Голод и энергия не опускаются ниже 0.

        Args:
            food: съедаемая порция; списанием управляет игра.

        Raises:
            TamagochiIsGone: питомец уже погиб.
        """
        self._require_alive()
        self._hunger = max(0, self._hunger - food.satiety)
        self._energy = max(0, self._energy - 2)

    def play(self) -> None:
        """Применить эффект игры с питомцем в пределах шкал.

        Энергия падает на 15, усталость растёт на 10, голод на 5,
        здоровье на 3. Обновление хода здесь не выполняется.

        Raises:
            TamagochiIsGone: питомец уже погиб.
        """
        self._require_alive()
        self._energy = max(0, self._energy - 15)
        self._fatigue = min(100, self._fatigue + 10)
        self._hunger = min(100, self._hunger + 5)
        self._hp = min(100, self._hp + 3)

    def rest(self) -> None:
        """Восстановить энергию и снизить усталость с учётом болезни.

        Здоровый питомец получает до 25 энергии и до 5 HP,
        усталость снижается на 25, минимум до 0. Больной питомец
        получает до 12 энергии, усталость снижается на 12,
        минимум до 0. Здоровье больного не восстанавливается.

        Raises:
            TamagochiIsGone: питомец уже погиб.
        """
        self._require_alive()
        recovery = 12 if self._sick else 25
        self._energy = min(100, self._energy + recovery)
        self._fatigue = max(0, self._fatigue - recovery)
        if not self._sick:
            self._hp = min(100, self._hp + 5)

    def heal(self, medicine: Medicine) -> None:
        """Восстановить здоровье, снять болезнь и потратить одну дозу.

        Здоровье увеличивается на heal_hp, максимум до 100.
        Доза расходуется и при полном здоровье здорового питомца.
        Удалением пустой упаковки из инвентаря управляет игра.

        Args:
            medicine: упаковка с хотя бы одной оставшейся дозой.

        Raises:
            TamagochiIsGone: питомец уже погиб.
            MedicineIsEmptyError: в упаковке закончились дозы.
        """
        self._require_alive()
        if medicine.is_empty():
            raise MedicineIsEmptyError('В этой упаковке закончились дозы.')
        self._hp = min(100, self._hp + medicine.heal_hp)
        self._sick = False
        medicine.uses += 1

    @property
    def status(self) -> dict[str, int]:
        """Копия показателей, включая болезнь (0 или 1)."""
        return {
            'hp': self._hp,
            'hunger': self._hunger,
            'fatigue': self._fatigue,
            'energy': self._energy,
            'sick': int(self._sick),
        }

    def is_alive(self) -> bool:
        """Вернуть True при hp >= 0, иначе False."""
        return self._hp >= 0

    def is_sick(self) -> bool:
        """Вернуть True при болезни, иначе False."""
        return self._sick

    def update(self) -> None:
        """Применить расход за ход, риск болезни и урон от запущенности.

        Голод, усталость и энергия остаются в пределах 0..100,
        здоровье может стать отрицательным.

        Raises:
            TamagochiIsGone: питомец погиб до или во время обновления.
        """
        self._require_alive()
        self._hunger = min(100, self._hunger + 5)
        self._fatigue = min(100, self._fatigue + 3)
        self._energy = max(0, self._energy - 3)
        if not self._sick and (
            self._hunger >= 70 or self._fatigue >= 70
        ):
            self._sick = random.random() < 0.1
        if self._sick:
            self._hp -= 5
            self._fatigue = min(100, self._fatigue + 2)
        if self._hunger >= 80:
            self._hp -= 5
        if self._fatigue >= 80:
            self._hp -= 3
        if self._energy == 0:
            self._hp -= 3
        self._require_alive()

    def _require_alive(self) -> None:
        """Проверить возможность действия.

        Raises:
            TamagochiIsGone: здоровье ниже нуля.
        """
        if not self.is_alive():
            raise TamagochiIsGone('Питомец погиб. Игра окончена.')
