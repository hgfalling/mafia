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
    """
    This detective is incomplete in several ways... its purpose was that it should
    not crash with a detective in the game, and should have
    the same strategy results as original_strat with the same number of citizens+detectives
    1. All "Detective Out" branches are ignored
    2. The case where mafia kill and detective peek the same type
       we ignore one case (assign it probability zero)
    3. (As a consequence above) neither Mafia or Citizen do anything different
       because the detective is in the game

    """
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


def is_time_to_come_out(gs):
    """
    If Detective is alive and there is a PeekedMafia
    come out 100% of the time. Otherwise, don't come out
    """
    has_detective = mafia.detective_alive(gs)
    has_peeks = gs.players[mafia.PType.PeekedMafia] > 0
    is_day = gs.time == 0
    return all([has_detective, has_peeks, is_day])


def proper_detective(gs):
    """
    1. If there's a PeekedMafia, always come out
    2. If there's a VerifiedMafia, citizens will always kill
    3. If there's a VerifiedCitizen, citizens will never kill
    4. If there's a VerifiedDetective, citizens will never kill
    5. If there's a VerifiedDetective, mafia will always assasinate (todo)
    6. If there's a VerifiedCitizen, and no VerifiedDetective, mafia will always assasinate (todo)
    7. Correctly assign random chances to the case when mafia assasinate and detective peek the same type (todo)
    """
    if gs.time == 0:
        choices = [x for x in mafia.day_outcomes(gs).keys()]
        action = {}
        if is_time_to_come_out(gs):
            assert "Detective Out" in choices
            for c in choices:
                if c == "Detective Out":
                    action[c] = Fraction(1, 1)
                else:
                    action[c] = Fraction(0, 1)
        else:
            # if there's a verifiedmafia, kill them first!
            if gs.players[mafia.PType.VerifiedMafia] > 0:
                for c in choices:
                    if c == "Detective Out":
                        action[c] = Fraction()
                    else:
                        if c[0] == mafia.PType.VerifiedMafia:
                            action[c] = Fraction(1, 1)
                        else:
                            action[c] = Fraction(0, 1)
            else:
                # Get the total remaining, excluding those who are verified safe
                sr = mafia.suspicious_remaining(gs)
                for x in choices:
                    if x == "Detective Out":
                        # Never come out
                        action[x] = Fraction()
                    else:
                        if not mafia.is_suspicious(x[0]):
                            # Never kill someone who is verified safe
                            action[x] = Fraction()
                        else:
                            # For everyone else, choose randomly with an equal chance
                            action[x] = Fraction(gs.players[x[0]], sr)
        assert sum(action.values()) == 1
        return action
    if gs.time == 1:
        # get all the choices for this round
        choices = list(mafia.night_outcomes(gs).keys())

        # from these choices, specifically get all the different kills
        kill_choices = set([c[0] for c in choices])
        # and get the total number of possible kills
        total_killable = mafia.citizens_remaining(gs)

        # go for verified detective
        # if there isnt one, go for verifieddetective
        # if there isnt one, then get probability for each kill choice by how common
        kill_chances = {}
        # if there is a verifieddetective, kill it 100% of the time
        if mafia.PType.VerifiedDetective in kill_choices:
            for kc in kill_choices:
                if kc == mafia.PType.VerifiedDetective:
                    kill_chances[kc] = Fraction(1, 1)
                else:
                    kill_chances[kc] = Fraction(0, 1)
        elif mafia.PType.VerifiedCitizen in kill_choices:
            for kc in kill_choices:
                if kc == mafia.PType.VerifiedCitizen:
                    kill_chances[kc] = Fraction(1, 1)
                else:
                    kill_chances[kc] = Fraction(0, 1)
        else:
            # get the probability each unique kill choice will be chosen
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
                # c[3] == 0 means that the peeked player was killed
                # c[3] == 1 means that they hit two different ones
                case_idx = c[3]
                assert case_idx in (0, 1)
                assert killed == peeked  # i think this is always true
                assert (
                    gs.players[killed] == gs.players[peeked]
                )  # so this is always true
                chance_it_is_the_same_player = Fraction(1, gs.players[killed])
                chance_it_isnt = 1 - chance_it_is_the_same_player
                case_chances = {0: chance_it_is_the_same_player, 1: chance_it_isnt}
                action[c] = (
                    kill_chances[killed] * peek_chances[peeked] * case_chances[case_idx]
                )
            else:
                # the probability of this action is the probability this type will be killed
                # multiplied by the probability this type will be peeked
                action[c] = kill_chances[killed] * peek_chances[peeked]
        assert sum(action.values()) == 1
        return action
