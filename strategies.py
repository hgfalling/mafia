from fractions import Fraction

import mafia


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


def incomplete_detective(gs):
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
