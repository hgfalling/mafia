from fractions import Fraction

import pytest

import mafia
from main import new_game, simple_strat


def original_strat(gs):
    # no detectives
    if gs.time == 0:
        choices = [x for x in mafia.day_outcomes(gs).keys()]
        tr = mafia.total_remaining(gs)
        action = dict([(x, Fraction(gs.players[x[0]], tr)) for x in choices])
        return action
    if gs.time == 1:
        choices = [x for x in mafia.night_outcomes(gs).keys()]
        tr = mafia.citizens_remaining(gs)
        action = dict([(x, Fraction(gs.players[x[0]], tr)) for x in choices])
        return action


def original_game():
    pl, gs, games = new_game(2, 19, 0, 0)
    weight_dict = mafia.eval_strat_rc(games, original_strat)
    return pl, gs, games, weight_dict


def test_nothing():
    assert 1 == 1


def test_winner_probabilities():
    pl, gs, games, weight_dict = original_game()
    mafia_win, citizen_win = mafia.winner_probabilities(games, weight_dict)
    assert mafia_win == Fraction(478099, 969969)
    assert citizen_win == Fraction(491870, 969969)


def test_simple_strat_original_strat_same():
    pl, gs, games = new_game(2, 19, 0, 0)
    weight_dict_original = mafia.eval_strat_rc(games, original_strat)
    weight_dict_simple = mafia.eval_strat_rc(games, simple_strat)
    assert weight_dict_original == weight_dict_simple


def test_can_play_detective():
    pl, gs, games = new_game(2, 18, 1, 0)
    weight_dict = mafia.eval_strat_rc(games, simple_strat)
    mafia_win, citizen_win = mafia.winner_probabilities(games, weight_dict)
    assert mafia_win + citizen_win == 1


def test_leaves_match_children():
    """
    All leaves that aren't game ending should have a corresponding starter node
    in the next days' game tree. This isn't checked right now until a strategy
    is evaluated.
    """
    pl, gs, games = new_game(2, 18, 1, 0)
    for idx, t in enumerate(games):
        for node in t.leaves():
            if mafia.winner(node.data[1]) != 0:
                continue
            else:
                targets = []
                for x in games[idx + 1].children(games[idx + 1].root):
                    if x.data[1] == node.data[1]:
                        targets.append(x.identifier)
                assert len(targets) == 1


def test_strategy_with_detective_sum_is_one():
    pl, gs, games = new_game(2, 4, 1, 0)
    mgs, cgs, dgs = [
        x.data[1]
        for x in games[0].children(games[0].root)
        if x.data[0] != "Detective Out"
    ]
    mgs_outcomes = simple_strat(mgs)
    cgs_outcomes = simple_strat(cgs)
    dgs_outcomes = simple_strat(dgs)
    assert sum(mgs_outcomes.values()) == 1
    assert sum(cgs_outcomes.values()) == 1
    assert sum(dgs_outcomes.values()) == 1


def test_useless_detective_same_as_no_detective():
    _, _, games = new_game(2, 19, 0, 0)
    gwd = mafia.eval_strat_rc(games, original_strat)
    _, _, dgames = new_game(2, 18, 1, 0)
    dwd = mafia.eval_strat_rc(dgames, simple_strat)
    assert mafia.winner_probabilities(games, gwd) == mafia.winner_probabilities(
        dgames, dwd
    )
