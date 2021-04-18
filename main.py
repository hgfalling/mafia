import mafia
import collections


def simple_strat(gs):
    # no detectives
    if gs.time == 0:
        choices = [x for x in mafia.day_outcomes(gs).keys()]
        tr = mafia.total_remaining(gs)
        action = dict([(x, gs.players[x[0]] / tr) for x in choices])
        return action
    if gs.time == 1:
        choices = [x for x in mafia.night_outcomes(gs).keys()]
        tr = mafia.citizens_remaining(gs)
        action = dict([(x, gs.players[x[0]] / tr) for x in choices])
        return action


pl = mafia.Players(2, 0, 0, 19, 0, 0, 0, 0, 0, 0, 0, 0)
gs = mafia.Gamestate(1, 0, None, pl)
games = mafia.make_game(pl, gs)

weight_dict = mafia.eval_strat_rc(games, simple_strat)
mafia_win, citizen_win = mafia.winner_probabilities(games, weight_dict)
print(mafia_win, citizen_win)
