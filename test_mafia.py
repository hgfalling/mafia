import mafia
from main import simple_strat


def original_game():
    pl = mafia.Players(2, 0, 0, 19, 0, 0, 0, 0, 0, 0, 0, 0)
    gs = mafia.Gamestate(1, 0, None, pl)
    games = mafia.make_game(pl, gs)
    weight_dict = mafia.eval_strat_rc(games, simple_strat)
    return pl, gs, games, weight_dict


def test_nothing():
    assert 1 == 1


def test_original_game():
    pl, gs, games, weight_dict = original_game()
    cleaves = []
    mleaves = []
    for g in games:
        cleaves.extend(
            [x.identifier for x in g.leaves() if mafia.winner(x.data[1]) == 1]
        )
        mleaves.extend(
            [x.identifier for x in g.leaves() if mafia.winner(x.data[1]) == -1]
        )

    mafia_win = sum([weight_dict[x] for x in mleaves])
    citizen_win = sum([weight_dict[x] for x in cleaves])
    assert mafia_win == 0.49290131952670657
    assert citizen_win == 0.5070986804732934
