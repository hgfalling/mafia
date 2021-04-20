from fractions import Fraction

import pytest

import mafia
from main import new_game, get_all_incomplete_gs
from strategies import original_strat, incomplete_detective, proper_detective


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


def test_incomplete_detective_original_strat_same():
    pl, gs, games = new_game(2, 19, 0, 0)
    weight_dict_original = mafia.eval_strat_rc(games, original_strat)
    weight_dict_simple = mafia.eval_strat_rc(games, incomplete_detective)
    assert weight_dict_original == weight_dict_simple


def test_can_play_detective():
    pl, gs, games = new_game(2, 18, 1, 0)
    weight_dict = mafia.eval_strat_rc(games, incomplete_detective)
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
    mgs_outcomes = incomplete_detective(mgs)
    cgs_outcomes = incomplete_detective(cgs)
    dgs_outcomes = incomplete_detective(dgs)
    assert sum(mgs_outcomes.values()) == 1
    assert sum(cgs_outcomes.values()) == 1
    assert sum(dgs_outcomes.values()) == 1


def test_incomplete_detective_same_as_no_detective():
    _, _, games = new_game(2, 19, 0, 0)
    gwd = mafia.eval_strat_rc(games, original_strat)
    _, _, dgames = new_game(2, 18, 1, 0)
    dwd = mafia.eval_strat_rc(dgames, incomplete_detective)
    assert mafia.winner_probabilities(games, gwd) == mafia.winner_probabilities(
        dgames, dwd
    )


def test_can_play_proper_detective():
    pl, gs, games = new_game(2, 18, 1, 0)
    weight_dict = mafia.eval_strat_rc(games, proper_detective)
    mafia_win, citizen_win = mafia.winner_probabilities(games, weight_dict)
    assert mafia_win + citizen_win == 1


def test_proper_detective_beats_incomplete_detective():
    _, _, games = new_game(2, 18, 1, 0)
    idwd = mafia.eval_strat_rc(games, incomplete_detective)
    pdwd = mafia.eval_strat_rc(games, proper_detective)
    imw, icw = mafia.winner_probabilities(games, idwd)
    pmw, pcw = mafia.winner_probabilities(games, pdwd)
    # proper detective wins more often
    assert pcw > icw


def test_all_peeks_verified_after_detective_out():
    dpl, dgs, dgame = new_game(2, 5, 1, 0)
    igs = get_all_incomplete_gs(dgame)
    bad_states = []
    for i in igs:
        if (
            i.players[mafia.PType.PeekedMafia] > 0
            or i.players[mafia.PType.PeekedCitizen] > 0
        ) and i.players[mafia.PType.VerifiedDetective] > 0:
            bad_states.append(i)
    assert len(bad_states) == 0
