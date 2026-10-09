"""Границы состояния, болезнь, уход и смерть питомца."""

import pytest

from game.exceptions import MedicineIsEmptyError, TamagochiIsGone
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi


@pytest.mark.parametrize('hp, alive', [(-1, False), (0, True), (1, True)])
def test_health_boundary(hp: int, alive: bool) -> None:
    assert SimpleTamagochi(hp=hp).is_alive() is alive


def test_zero_health_can_recover() -> None:
    pet = SimpleTamagochi(hp=0)
    pet.rest()
    pet.update()
    assert pet.is_alive()
    assert pet.status['hp'] == 5


def test_health_reaches_zero_before_death() -> None:
    pet = SimpleTamagochi(hp=5, hunger=75)
    pet.update()
    assert pet.status['hp'] == 0
    assert pet.is_alive()
    with pytest.raises(TamagochiIsGone):
        pet.update()
    assert pet.status['hp'] == -5
    assert not pet.is_alive()


def test_feed_changes_only_its_effect(food: Food) -> None:
    pet = SimpleTamagochi(hunger=30)
    pet.feed(food)
    assert pet.status == {
        'hp': 100, 'hunger': 10, 'fatigue': 0, 'energy': 98, 'sick': 0,
    }


def test_play_spends_energy_and_increases_fatigue() -> None:
    pet = SimpleTamagochi(hp=80)
    pet.play()
    assert pet.status == {
        'hp': 83, 'hunger': 25, 'fatigue': 10, 'energy': 85, 'sick': 0,
    }


def test_sickness_reduces_rest_and_harms_health() -> None:
    healthy = SimpleTamagochi(hp=80, energy=40, fatigue=50)
    sick = SimpleTamagochi(hp=80, energy=40, fatigue=50, sick=True)
    for pet in (healthy, sick):
        pet.rest()
        pet.update()
    assert healthy.status['energy'] > sick.status['energy']
    assert healthy.status['fatigue'] < sick.status['fatigue']
    assert healthy.status['hp'] == 85
    assert sick.status['hp'] == 75


@pytest.mark.parametrize('roll, sick', [(0.0, True), (0.1, False)])
def test_sickness_at_high_hunger(
    monkeypatch: pytest.MonkeyPatch, roll: float, sick: bool,
) -> None:
    monkeypatch.setattr('game.tamagochi.random.random', lambda: roll)
    pet = SimpleTamagochi(hunger=65)
    pet.update()
    assert pet.is_sick() is sick


def test_sickness_at_high_fatigue(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('game.tamagochi.random.random', lambda: 0.0)
    pet = SimpleTamagochi(fatigue=67)
    pet.update()
    assert pet.is_sick()


def test_healthy_pet_has_no_sickness_roll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr('game.tamagochi.random.random', lambda: 0.0)
    pet = SimpleTamagochi()
    pet.update()
    assert not pet.is_sick()


def test_healing_cures_sickness_and_exhausts_pack(medicine: Medicine) -> None:
    pet = SimpleTamagochi(hp=50, sick=True)
    pet.heal(medicine)
    assert not pet.is_sick()
    assert pet.status['hp'] == 70
    pet.heal(medicine)
    assert medicine.uses == medicine.number_of_uses == 2
    assert medicine.is_empty()
    status = pet.status
    with pytest.raises(MedicineIsEmptyError):
        pet.heal(medicine)
    assert medicine.uses == 2
    assert pet.status == status


def test_scales_stay_in_bounds(food: Food, medicine: Medicine) -> None:
    pet = SimpleTamagochi(hunger=0, fatigue=0, energy=0)
    pet.feed(food)
    pet.play()
    pet.rest()
    pet.heal(medicine)
    pet.update()
    for indicator, value in pet.status.items():
        assert 0 <= value <= 100, indicator


def test_exhaustion_deals_health_damage() -> None:
    pet = SimpleTamagochi(hunger=100, fatigue=100, energy=0)
    pet.update()
    assert pet.status['hp'] == 89
    assert pet.status['hunger'] == pet.status['fatigue'] == 100
    assert pet.status['energy'] == 0


def test_status_is_a_copy(tamagochi: SimpleTamagochi) -> None:
    status = tamagochi.status
    status['hp'] = -100
    assert tamagochi.is_alive()


@pytest.mark.parametrize('action', ['feed', 'play', 'rest', 'heal', 'update'])
def test_dead_pet_cannot_act(
    action: str, food: Food, medicine: Medicine,
) -> None:
    pet = SimpleTamagochi(hp=-1)
    arguments = {'feed': (food,), 'heal': (medicine,)}
    with pytest.raises(TamagochiIsGone):
        getattr(pet, action)(*arguments.get(action, ()))
    assert pet.status['hp'] == -1
    assert medicine.uses == 0


@pytest.mark.parametrize(
    'indicator, value',
    [('hp', 101), ('hunger', -1), ('fatigue', 101), ('energy', -1)],
)
def test_invalid_initial_state(indicator: str, value: int) -> None:
    with pytest.raises(ValueError):
        SimpleTamagochi(**{indicator: value})
