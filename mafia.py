import treelib
import typing
import enum
import collections
from fractions import Fraction


class PType(enum.IntEnum):
    Mafia = 0
    VerifiedMafia = 1
    PeekedMafia = 2
    Citizen = 3
    VerifiedCitizen = 4
    PeekedCitizen = 5
    Detective = 6
    VerifiedDetective = 7
    CitizenDetective = 8
    Bodyguard = 9
    VerifiedBodyguard = 10
    PeekedBodyguard = 11


peek_dict = {
    PType.Mafia: PType.PeekedMafia,
    PType.Bodyguard: PType.PeekedBodyguard,
    PType.Citizen: PType.PeekedCitizen,
}

unpeek_dict = {
    PType.PeekedMafia: PType.Mafia,
    PType.PeekedBodyguard: PType.Bodyguard,
    PType.PeekedCitizen: PType.Citizen,
}

verified_dict = {
    PType.Mafia: PType.VerifiedMafia,
    PType.Bodyguard: PType.VerifiedBodyguard,
    PType.Citizen: PType.VerifiedCitizen,
    PType.Detective: PType.VerifiedDetective,
    PType.PeekedMafia: PType.VerifiedMafia,
    PType.PeekedBodyguard: PType.VerifiedBodyguard,
    PType.PeekedCitizen: PType.VerifiedCitizen,
}


def is_citizen(x: PType) -> bool:
    return x.value >= 3


def is_mafia(x: PType) -> bool:
    return x.value <= 2


def is_bodyguard(x: PType) -> bool:
    return x >= 9 and x <= 11


def is_detective(x: PType) -> bool:
    return x >= 6 and x <= 8


def is_verified(x: PType) -> bool:
    return x in [1, 4, 7, 10]


def is_peeked(x: PType) -> bool:
    return x in [2, 5, 11]


def peekable_types() -> typing.Tuple[PType, PType, PType]:
    return (PType.Mafia, PType.Bodyguard, PType.Citizen)


def peeked_types() -> typing.Tuple[PType, PType, PType]:
    return PType.PeekedMafia, PType.PeekedBodyguard, PType.PeekedCitizen


def peeked_version(x: PType) -> PType:
    if x in peek_dict:
        return peek_dict[x]
    else:
        return None


def unpeeked_version(x: PType) -> PType:
    if x in unpeek_dict:
        return unpeek_dict[x]
    else:
        return None


def verified_version(x: PType) -> PType:
    if x in verified_dict:
        return verified_dict[x]
    else:
        return None


def to_string(x: PType) -> str:
    if x is None:
        return "XX"
    abbrevs = ["MM", "MV", "PM", "CC", "CV", "CP", "DD", "DV", "DC", "BB", "BV", "BP"]
    return abbrevs[x]


class Players(typing.NamedTuple):
    mafia: int
    verified_mafia: int
    peeked_mafia: int
    citizen: int
    verified_citizen: int
    peeked_citizen: int
    detective: int
    verified_detective: int
    citizen_detective: int
    bodyguard: int
    verified_bodyguard: int
    peeked_bodyguard: int

    def __add__(self, other):
        new_vals = tuple([x + y for x, y in zip(list(self), list(other))])
        return Players(*new_vals)

    def __repr__(self):
        rlist = []
        for i in range(0, len(self), 3):
            rlist.append("".join([str(x) for x in self[i : i + 3]]))
        return "/".join(rlist)


class Gamestate(typing.NamedTuple):
    day: int
    time: int  # 0=day,1=night
    last_protected: object
    players: Players


def total_remaining(x: Gamestate) -> int:
    return mafia_remaining(x) + citizens_remaining(x)


def mafia_remaining(x: Gamestate) -> int:
    return sum(x.players[PType.Mafia : PType.Citizen])


def citizens_remaining(x: Gamestate) -> int:
    return sum(x.players[PType.Citizen :])


def bodyguard_alive(x: Gamestate) -> bool:
    return sum(x.players[PType.Bodyguard :]) > 0


def detective_alive(x: Gamestate) -> bool:
    return sum(x.players[PType.Detective : PType.Bodyguard]) > 0


def detective_is_already_out(gs: Gamestate) -> bool:
    return gs.players[PType.VerifiedDetective] > 0


def winner(gs: Gamestate) -> int:
    """1 = town, 0 = not over, -1 = mafia"""
    mr = mafia_remaining(gs)
    if mr == 0:
        return 1
    if mr >= citizens_remaining(gs):
        return -1
    else:
        return 0


def kill_change(ptype: PType) -> Players:
    """
    produces a Players 'delta' vector that can be added to another
    Players vector to kill one player of the provided type
    """
    ch = [0] * len(PType)
    ch[ptype] = -1
    return Players(*tuple(ch))


def peek_change(ptype: PType) -> Players:
    """
    produces a Players 'delta' vector that can be added to another
    Players vector to peek one player of the provided type
    """
    ch = [0] * len(PType)
    ch[ptype] = -1
    ch[peeked_version(ptype)] = 1
    return Players(*tuple(ch))


def verified_change(ptype: PType) -> Players:
    """
    produces a Players 'delta' vector that can be added to another
    Players vector to verify one player of the provided type
    """
    ch = [0] * len(PType)
    ch[ptype] = -1
    ch[verified_version(ptype)] = 1
    return Players(*tuple(ch))


def gs_choices(gs: Gamestate) -> list:
    """
    Returns a list of the allowable choices from gamestate gs.
    """
    if gs.time == 0:  # daytime
        choices = []
        if gs.players[PType.Detective] + gs.players[PType.CitizenDetective] > 0:
            choices.append("Detective Out")
        for ptype in PType:
            if gs.players[ptype] >= 1:
                choices.append(ptype)
        return choices

    if gs.time == 1:  # night.
        if detective_alive(gs):
            dchoices = []
            for ptype in peekable_types():
                if gs.players[ptype] >= 1:
                    dchoices.append(ptype)
        else:
            dchoices = [None]

        if not dchoices:
            # if the detective is alive, but there are no peekable types left
            # then dchoices is an empty list, and this causes a problem later
            dchoices = [None]

        if bodyguard_alive(gs):
            bchoices = []
            for ptype in PType:
                if gs.players[ptype] > 1 or ptype != gs.last_protected:
                    bchoices.append(ptype)
        else:
            bchoices = [None]

        return dchoices, bchoices


def detective_comes_out(gs: Gamestate):
    """
    Returns the gamestate resulting from the detective coming out in gamestate gs.
    """
    if not detective_alive(gs):
        return gs
    gsp = list(gs.players)
    for ptype in PType:
        if is_peeked(ptype):
            gsp[verified_version(ptype)] += gsp[ptype]
            gsp[ptype] = 0
    gsp[PType.VerifiedDetective] = 1
    gsp[PType.Detective] = 0

    if is_peeked(gs.last_protected):
        last_protected = verified_version(gs.last_protected)
    else:
        last_protected = gs.last_protected

    new_players = Players(*tuple(gsp))
    new_gs = Gamestate(gs.day, gs.time, last_protected, new_players)
    return new_gs


def day_outcomes(gs: Gamestate):
    """
    Returns a dictionary with keys: the possible choices that can be taken
    (annotated with possible hidden combinations) and values: the resulting
    gamestates from those choices.
    This is for daytime outcomes.
    """
    assert gs.time == 0
    outcomes = {}
    choices = gs_choices(gs)
    for choice in choices:
        if choice == "Detective Out":
            outcomes[choice] = detective_comes_out(gs)
        else:
            change = [0] * len(PType)
            change[choice] = -1
            new_players = gs.players + Players(*tuple(change))
            new_gs = Gamestate(gs.day, 1, gs.last_protected, new_players)
            outcomes[(choice, None, None)] = new_gs
    return outcomes


def night_outcomes(gs: Gamestate):
    """
    Returns a dictionary with keys: the possible choices that can be taken
    (annotated with possible hidden combinations) and values: the resulting
    gamestates from those choices.
    This is for nighttime outcomes. Only detective and bodyguard implemented
    here now.
    """
    assert gs.time == 1
    # mafia can kill any citizen.
    mafia_kills = []
    for ptype in PType:
        if is_citizen(ptype) and gs.players[ptype] > 0:
            mafia_kills.append(ptype)
    detective_peeks, bg_protects = gs_choices(gs)
    outcomes = {}
    for mafia_kill in mafia_kills:
        for detective_peek in detective_peeks:
            for bg_protect in bg_protects:
                if detective_peek is None and bg_protect is None:
                    new_players = gs.players + kill_change(mafia_kill)
                    outcomes[(mafia_kill, detective_peek, bg_protect)] = Gamestate(
                        gs.day + 1, 0, None, new_players
                    )
                elif bg_protect is None:
                    # then nobody is protected, figure out peek.
                    if detective_peek != mafia_kill:
                        # then everything is easy...
                        new_players = gs.players + kill_change(mafia_kill)
                        new_players = new_players + peek_change(detective_peek)
                        outcomes[(mafia_kill, detective_peek, bg_protect)] = Gamestate(
                            gs.day + 1, 0, None, new_players
                        )
                    else:
                        # we can always have the case where the peeked gets killed
                        new_players = gs.players + kill_change(mafia_kill)
                        outcomes[
                            (mafia_kill, detective_peek, bg_protect, 0)
                        ] = Gamestate(gs.day + 1, 0, None, new_players)
                        # if there are more than 1, they could miss each other:
                        if gs.players[mafia_kill] >= 2:
                            new_players = gs.players + kill_change(mafia_kill)
                            new_players = new_players + peek_change(detective_peek)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 1)
                            ] = Gamestate(gs.day + 1, 0, None, new_players)
                elif detective_peek is None:
                    # then there's no peek, just figure out BG.
                    if bg_protect != mafia_kill:
                        new_players = gs.players + kill_change(mafia_kill)
                        outcomes[(mafia_kill, detective_peek, bg_protect)] = Gamestate(
                            gs.day + 1, 0, bg_protect, new_players
                        )
                    else:
                        # bg could save:
                        new_players = gs.players + verified_change(mafia_kill)
                        outcomes[
                            (mafia_kill, detective_peek, bg_protect, 2)
                        ] = Gamestate(
                            gs.day + 1, 0, verified_version(bg_protect), new_players
                        )
                        if gs.players[mafia_kill] >= 2:
                            new_players = gs.players + kill_change(mafia_kill)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 2)
                            ] = Gamestate(gs.day + 1, 0, bg_protect, new_players)
                else:  # a kill,a peek,a protect.
                    if (
                        len(set[mafia_kill, detective_peek, bg_protect]) == 3
                    ):  # all different
                        new_players = gs.players + kill_change(mafia_kill)
                        new_players = new_players + peek_change(detective_peek)
                        outcomes[(mafia_kill, detective_peek, bg_protect)] = Gamestate(
                            gs.day + 1, 0, bg_protect, new_players
                        )
                    if (
                        len(set[mafia_kill, detective_peek, bg_protect]) == 2
                    ):  # one different, two the same
                        if mafia_kill == detective_peek:
                            new_players = gs.players + kill_change(mafia_kill)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 0)
                            ] = Gamestate(gs.day + 1, 0, bg_protect, new_players)
                            if gs.players[mafia_kill] >= 2:
                                new_players = gs.players + kill_change(mafia_kill)
                                new_players = new_players + peek_change(detective_peek)
                                outcomes[
                                    (mafia_kill, detective_peek, bg_protect, 1)
                                ] = Gamestate(gs.day + 1, 0, bg_protect, new_players)
                        if mafia_kill == bg_protect:
                            new_players = gs.players + verified_change(mafia_kill)
                            new_players = gs.players + peek_change(detective_peek)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 0)
                            ] = Gamestate(
                                gs.day + 1, 0, verified_version(bg_protect), new_players
                            )
                            if gs.players[mafia_kill] >= 2:
                                new_players = gs.players + kill_change(mafia_kill)
                                new_players = gs.players + peek_change(detective_peek)
                                outcomes[
                                    (mafia_kill, detective_peek, bg_protect, 1)
                                ] = Gamestate(gs.day + 1, 0, bg_protect, new_players)
                        if bg_protect == detective_peek:
                            new_players = gs.players + kill_change(mafia_kill)
                            new_players = gs.players + peek_change(detective_peek)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 0)
                            ] = Gamestate(gs.day + 1, 0, bg_protect, new_players)
                            if gs.players[bg_protect] >= 2:
                                new_players = gs.players + kill_change(mafia_kill)
                                new_players = gs.players + peek_change(detective_peek)
                                outcomes[
                                    (mafia_kill, detective_peek, bg_protect, 1)
                                ] = Gamestate(
                                    gs.day + 1,
                                    0,
                                    peeked_version(bg_protect),
                                    new_players,
                                )
                    if (
                        len(set[mafia_kill, detective_peek, bg_protect]) == 1
                    ):  # all the same
                        n = gs.players[mafia_kill]
                        if n >= 1:
                            # 0: 000 (bg saves, det peek does nothing)
                            new_players = gs.players + verified_change(mafia_kill)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 0)
                            ] = Gamestate(
                                gs.day + 1, 0, verified_version(bg_protect), new_players
                            )
                        if n >= 2:
                            # 1: 001 (so peek does nothing and bg whiffs)
                            new_players = gs.players + verified_change(mafia_kill)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 1)
                            ] = Gamestate(gs.day + 1, 0, bg_protect, new_players)
                            # 2: 010 (bg saves and detective peeks another)
                            new_players = gs.players + verified_change(mafia_kill)
                            new_players = gs.players + peek_change(detective_peek)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 2)
                            ] = Gamestate(
                                gs.day + 1, 0, verified_version(bg_protect), new_players
                            )
                            # 3: 011 (so bg protects peeked player and mafia kills.)
                            new_players = gs.players + verified_change(mafia_kill)
                            new_players = gs.players + peek_change(mafia_kill)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 3)
                            ] = Gamestate(
                                gs.day + 1, 0, peeked_version(bg_protect), new_players
                            )
                        if n >= 3:
                            # 4: 012 (so all 3 different)
                            new_players = gs.players + verified_change(mafia_kill)
                            new_players = gs.players + peek_change(mafia_kill)
                            outcomes[
                                (mafia_kill, detective_peek, bg_protect, 4)
                            ] = Gamestate(gs.day + 1, 0, bg_protect, new_players)

    for key, val in outcomes.items():
        # if the detective dies, undo all the peeks
        if not detective_alive(val):
            gsp = list(val.players)
            for ptype in peeked_types():
                gsp[unpeeked_version(ptype)] += gsp[ptype]
                gsp[ptype] = 0
            outcomes[key] = Gamestate(
                day=val.day,
                time=val.time,
                last_protected=val.last_protected,
                players=Players(*tuple(gsp)),
            )
        if detective_is_already_out(val):
            gsp = list(val.players)
            for ptype in peeked_types():
                gsp[verified_version(ptype)] += gsp[ptype]
                gsp[ptype] = 0
            outcomes[key] = Gamestate(
                day=val.day,
                time=val.time,
                last_protected=val.last_protected,
                players=Players(*tuple(gsp)),
            )

    return outcomes


def expand_day_nodes(tree: treelib.Tree):
    """
    Expands day nodes by creating all the appropriate children nodes.
    """

    for node in tree.all_nodes():
        node_id = node.identifier
        path, gs, expanded = tree[node_id].data[0:3]
        if expanded or gs.time == 1:
            continue

        if winner(gs) != 0:
            tree[node_id].data = (path, gs, True)
            continue

        outcomes = day_outcomes(gs)

        for key, val in outcomes.items():
            if key == "Detective Out":
                tree.create_node(
                    f"DO {str(val)}",
                    node_id + "_" + "DO",
                    node_id,
                    data=(key, val, False),
                )
            else:
                s = "".join([to_string(x) for x in key[0:3]]) + (
                    str(key[-1]) if len(key) > 3 else ""
                )
                tree.create_node(
                    f"{s} {str(val)}",
                    node_id + "_" + s,
                    node_id,
                    data=(key, val, False),
                )

        tree[node_id].data = (path, gs, True)
    return


def expand_night_nodes(tree: treelib.Tree):
    """
    Expands night nodes by creating all the appropriate children nodes.
    """
    for node in tree.all_nodes():
        node_id = node.identifier

        path, gs, expanded = tree[node_id].data[0:3]
        if expanded or gs.time == 0:
            continue

        if winner(gs) != 0:
            tree[node_id].data = (path, gs, True)
            continue

        outcomes = night_outcomes(gs)

        for key, val in outcomes.items():
            s = "".join([to_string(x) for x in key[0:3]]) + (
                str(key[-1]) if len(key) > 3 else ""
            )
            tree.create_node(
                f"{s} {str(val)}",
                node_id + "_" + s,
                node_id,
                data=(key, val, False, 0.0),
            )

        tree[node_id].data = (path, gs, True)
    return


def unexpanded_nodes(game: treelib.Tree):
    return sum([int(not x.data[2]) for x in game.all_nodes()])


def unexpanded_day_nodes(game: treelib.Tree):
    return sum([int((not x.data[2]) and x.data[1].time == 0) for x in game.all_nodes()])


def unexpanded_night_nodes(game: treelib.Tree):
    return sum([int((not x.data[2]) and x.data[1].time == 1) for x in game.all_nodes()])


def level_size(tree: treelib.Tree, level=1):
    return len([x for x in tree.all_nodes() if tree.level(x.identifier) == level])


def make_game(pl: Players, gs: Gamestate):
    """
    makes the entire recombining game tree, which is a list of trees
    one for each day.
    """

    game = treelib.Tree()
    game.create_node(f"Root {str(gs)}", "root0", data=(None, gs, False))

    games = [game]
    g = games[-1]

    while unexpanded_nodes(g) > 0:
        while unexpanded_day_nodes(g) > 0:
            expand_day_nodes(g)
        while unexpanded_night_nodes(g) > 0:
            expand_night_nodes(g)
        gss = set([x.data[1] for x in g.leaves() if not x.data[2]])
        if len(gss) > 0:
            root_gs = g[g.root].data[1]
            new_gs = Gamestate(root_gs.day + 1, 0, None, pl)
            new_game = treelib.Tree()
            new_game.create_node(
                f"Day {new_gs.day}",
                "root" + str(new_gs.day - 1),
                data=(None, new_gs, True, 1.0),
            )
            for idx, ugss in enumerate(gss):
                new_game.create_node(
                    f"{str(ugss)}",
                    "root" + str(new_gs.day - 1) + "_n" + str(idx),
                    parent=new_game.root,
                    data=(None, ugss, False, 0.0),
                )
            games.append(new_game)
            g = new_game
    return games


def apply_strat(game, node, day, fstrat, weight_dict):
    nid = node.identifier
    if node.is_leaf():
        return
    elif nid == ("root" + str(node.data[1].day - 1)):
        weight_dict["root" + str(day)] = Fraction(1, 1)
        if day > 0:
            return
    outcomes = fstrat(node.data[1])
    # print(outcomes)
    for key, val in outcomes.items():
        node_ids = [x.identifier for x in game.children(nid) if x.data[0] == key]
        weight_dict[node_ids[0]] += val * weight_dict[nid]
    return


def eval_strat_rc(games, fstrat):
    weight_dict = collections.defaultdict(Fraction)
    for idx, t in enumerate(games):
        for node in t.expand_tree(mode=t.WIDTH):
            apply_strat(games[idx], t[node], idx, fstrat, weight_dict)
        for node in t.leaves():
            if winner(node.data[1]) != 0:
                continue
            else:
                target = [
                    x.identifier
                    for x in games[idx + 1].children(games[idx + 1].root)
                    if x.data[1] == node.data[1]
                ][0]
                weight_dict[target] += weight_dict[node.identifier]
    return weight_dict


def winner_probabilities(games, weight_dict):
    cleaves = []
    mleaves = []
    for g in games:
        cleaves.extend([x.identifier for x in g.leaves() if winner(x.data[1]) == 1])
        mleaves.extend([x.identifier for x in g.leaves() if winner(x.data[1]) == -1])

    mafia_win = sum([weight_dict[x] for x in mleaves])
    citizen_win = sum([weight_dict[x] for x in cleaves])
    return mafia_win, citizen_win
