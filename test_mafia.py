import mafia
from main import new_game, simple_strat


def original_game():
    pl, gs, games = new_game(2, 19, 0, 0)
    weight_dict = mafia.eval_strat_rc(games, simple_strat)
    return pl, gs, games, weight_dict


def test_nothing():
    assert 1 == 1


def test_winner_probabilities():
    pl, gs, games, weight_dict = original_game()
    mafia_win, citizen_win = mafia.winner_probabilities(games, weight_dict)
    assert mafia_win == 0.49290131952670657
    assert citizen_win == 0.5070986804732934
