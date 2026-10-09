"""Консольный интерфейс игры."""

from game.clicker import SimpleRandomClicker
from game.exceptions import (
    InvalidItemError,
    ItemNotFoundError,
    MedicineIsEmptyError,
    NotEnoughMoney,
    TamagochiIsGone,
)
from game.game import AbstractGame, SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi


def choose_item(
    game: AbstractGame, items: list[Food] | list[Medicine],
) -> bool:
    """Показать предметы и сохранить выбранный индекс.

    Пользователь вводит номер с единицы, 0 отменяет выбор.
    Покупку или применение предмета выполняет вызывающий код.

    Args:
        game: игра, принимающая выбор через select_item.
        items: каталог или раздел инвентаря.

    Returns:
        True, если индекс сохранён; False при пустом списке,
        отмене или ошибке ввода. При False прежний выбор сохраняется.
    """
    if not items:
        print('В этом списке пока нет предметов.')
        return False
    for number, item in enumerate(items, start=1):
        print(f'{number}. {item}')
    try:
        number = int(input('Номер предмета (0: отмена): '))
    except ValueError:
        print('Введите целое число.')
        return False
    if number == 0:
        return False
    if not 1 <= number <= len(items):
        print('Предмета с таким номером нет.')
        return False
    game.select_item(number - 1)
    return True


def show_status(game: AbstractGame) -> None:
    """Вывести статус питомца и содержимое сумок."""
    status = game.get_status()
    print(
        f'\nГолод: {status["hunger"]}, усталость: {status["fatigue"]}, '
        f'здоровье: {status["hp"]}, энергия: {status["energy"]}, '
        f'монеты: {status["coins"]}'
    )
    print(f'Сумка с едой: {game.food}')
    print(f'Сумка с лекарствами: {game.medicine}')
    if game.tamagochi.is_sick():
        print('Питомец болеет. Отдых восстанавливает меньше сил.')


def run_game(game: AbstractGame) -> None:
    """Обработать команды до выхода или смерти питомца.

    EOF и Ctrl+C завершают цикл. Нехватка монет, пустой список,
    неверный индекс и исчерпание доз выводятся в консоль и позволяют
    продолжить игру. После смерти выводится итоговый статус.
    """
    print('Добро пожаловать в Тамагочи-кликер! Ваш питомец: кот Мурчик.')
    try:
        while game.tamagochi.is_alive():
            show_status(game)
            print(
                '\n1. Пойти на работу\n2. Купить еду\n'
                '3. Купить лекарство\n4. Покормить\n5. Вылечить\n'
                '6. Играть\n7. Отдых\n8. Статус\n0. Выход'
            )
            command = input('Выберите действие: ').strip()
            try:
                match command:
                    case '1':
                        print(f'Вы заработали {game.work()} монет.')
                    case '2':
                        if choose_item(game, game.all_food):
                            game.buy_food()
                            print('Еда куплена.')
                    case '3':
                        if choose_item(game, game.all_medicine):
                            game.buy_medicine()
                            print('Лекарство куплено.')
                    case '4':
                        if choose_item(game, game.food):
                            game.feed_tamagochi()
                            print('Питомец поел.')
                    case '5':
                        if choose_item(game, game.medicine):
                            game.heal_tamagochi()
                            print('Питомец получил лекарство.')
                    case '6':
                        game.play_with_tamagochi()
                        print('Вы поиграли с питомцем.')
                    case '7':
                        game.rest_tamagochi()
                        print('Питомец отдохнул.')
                    case '8':
                        continue
                    case '0':
                        print('До встречи!')
                        return
                    case _:
                        print('Неверная команда.')
            except (InvalidItemError, ItemNotFoundError, MedicineIsEmptyError,
                    NotEnoughMoney) as error:
                print(error)
    except TamagochiIsGone as error:
        print(error)
    except (EOFError, KeyboardInterrupt):
        print('\nИгра остановлена.')
        return
    else:
        print('Питомец погиб. Игра окончена.')
    show_status(game)


def main() -> None:
    """Собрать игру с каталогами и запустить консольный цикл."""
    all_food = [
        Food(name='Бургер', satiety=20, price=40),
        Food(name='Салат', satiety=10, price=20),
        Food(name='Яблоко', satiety=10, price=15),
    ]
    all_medicine = [
        Medicine(name='Ибупрофен', price=30, heal_hp=20, number_of_uses=2),
    ]
    game = SimpleGame(
        SimpleTamagochi(), SimpleRandomClicker(10, 20),
        all_food=all_food, all_medicine=all_medicine,
    )
    run_game(game)


if __name__ == '__main__':
    main()
