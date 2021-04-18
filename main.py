import mafia
import collections
from fractions import Fraction

from strategies import incomplete_detective


def get_all_incomplete_gs(games):
    states = []
    for idx, t in enumerate(games):
        for node in t.expand_tree(mode=t.WIDTH):
            nid = t[node].identifier
            node = t[node]
            if node.is_leaf():
                continue
            elif node.identifier == ("root" + str(node.data[1].day - 1)):
                if idx > 0:
                    continue
            states.append(node.data[1])
    return states


def get_all_choices(games):
    choices = []
    for idx, t in enumerate(games):
        for node in t.expand_tree(mode=t.WIDTH):
            # this is weird because you are reassigning node because of
            # how you copy and pasted the function
            game, node, day = (games[idx], t[node], idx)
            nid = node.identifier
            if node.is_leaf():
                continue
            elif nid == ("root" + str(node.data[1].day - 1)):
                if day > 0:
                    continue
            if node.data[1].time == 0:
                for k, v in mafia.day_outcomes(node.data[1]).items():
                    choices.append({"before": node.data[1], "choice": k, "after": v})
            elif node.data[1].time == 1:
                for k, v in mafia.night_outcomes(node.data[1]).items():
                    choices.append({"before": node.data[1], "choice": k, "after": v})
            else:
                assert 1 == 0
    return choices


def query_choices(choices, choice, before_phase=(0, 1)):
    if isinstance(before_phase, int):
        before_phase = (before_phase,)
    return [
        c for c in choices if c["choice"] == choice and c["before"].time in before_phase
    ]


def unique_choices(choices, before_phase=(0, 1)):
    if isinstance(before_phase, int):
        before_phase = (before_phase,)
    uniqc = {}
    for c in choices:
        if c["before"].time in before_phase:
            if c["choice"] not in uniqc.keys():
                uniqc[c["choice"]] = []
            uniqc[c["choice"]].append(c["before"])
    return uniqc


def new_game(num_mafia, num_citizen, num_detective, num_bodyguard):
    pl = mafia.Players(
        num_mafia, 0, 0, num_citizen, 0, 0, num_detective, 0, 0, num_bodyguard, 0, 0
    )
    gs = mafia.Gamestate(1, 0, None, pl)
    games = mafia.make_game(pl, gs)
    return pl, gs, games


dpl, dgs, dgame = new_game(2, 5, 1, 0)
cs = get_all_choices(dgame)

pl, gs, games = new_game(2, 19, 0, 0)
weight_dict = mafia.eval_strat_rc(games, incomplete_detective)
mafia_win, citizen_win = mafia.winner_probabilities(games, weight_dict)
print(mafia_win, citizen_win)

igs = get_all_incomplete_gs(dgame)
strat_out = [incomplete_detective(i) for i in igs]
