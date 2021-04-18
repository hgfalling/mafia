import mafia
import collections
from fractions import Fraction


def simple_strat(gs):
    # no detectives
    if gs.time == 0:
        choices = [x for x in mafia.day_outcomes(gs).keys()]
        tr = mafia.total_remaining(gs)
        action = dict(
            [
                (x, Fraction(gs.players[x[0]], tr))
                for x in choices
                if x != "Detective Out"
            ]
        )
        return action
    if gs.time == 1:
        # get all the choices for this round
        choices = list(mafia.night_outcomes(gs).keys())

        # from these choices, specifically get all the different kills
        kill_choices = set([c[0] for c in choices])
        # and get the total number of possible kills
        total_killable = mafia.citizens_remaining(gs)
        # get the probability each unique kill choice will be chosen
        kill_chances = {}
        for kc in kill_choices:
            num_remaining = gs.players[kc]
            # kill_chances[kc] = num_remaining / total_killable
            kill_chances[kc] = Fraction(num_remaining, total_killable)
        # this should add up to 1
        assert sum(kill_chances.values()) == 1

        # now do the same for peeks
        peek_choices = set([c[1] for c in choices if c[1] is not None])
        if peek_choices:
            # total number of possible peeks
            total_unpeeked = (
                gs.players[mafia.PType.Citizen] + gs.players[mafia.PType.Mafia]
            )
            # get the probability of each unique peek choice
            peek_chances = {}
            for pc in peek_choices:
                num_remaining = gs.players[pc]
                peek_chances[pc] = Fraction(num_remaining) / Fraction(total_unpeeked)
            # this should add up to 1
            assert sum(peek_chances.values()) == 1
        else:
            # so if there are no peeks, make sure that all peek lookups are 1
            peek_chances = {None: Fraction(1, 1)}

        action = {}
        for c in choices:
            killed = c[0]
            peeked = c[1]
            if len(c) == 4:
                # this means this choice has an additional index
                # i.e. sometimes detective peeks same person mafia kills, etc.
                # as to keep probabilities right, only take the first option
                if c[3] != 0:
                    action[c] = 0
                    continue
            # the probability of this action is the probability this type will be killed
            # multiplied by the probability this type will be peeked
            action[c] = kill_chances[killed] * peek_chances[peeked]
        assert sum(action.values()) == 1
        return action


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
weight_dict = mafia.eval_strat_rc(games, simple_strat)
mafia_win, citizen_win = mafia.winner_probabilities(games, weight_dict)
print(mafia_win, citizen_win)

igs = get_all_incomplete_gs(dgame)
strat_out = [simple_strat(i) for i in igs]
