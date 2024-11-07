from collections import Counter
import copy
import numpy as np
import pandas as pd

CAND = 0  # subscript of list which represents the candidate
SCORE = 1  # subscript of list which represents the score of the candidate
PLACE = 2  # subscript of list which represents the ranking, lowest is best


def create_voting(voters, candidates):
    names = [
        "Alice ",
        "Bart  ",
        "Cindy ",
        "Darin ",
        "Elmer ",
        "Finn  ",
        "Greg  ",
        "Hank  ",
        "Ian   ",
        "Jim   ",
        "Kate  ",
        "Linc  ",
        "Mary  ",
        "Nancy ",
        "Owen  ",
        "Peter ",
        "Quinn ",
        "Ross  ",
        "Sandy ",
        "Tom   ",
        "Ursula",
        "Van   ",
        "Wendy ",
        "Xavier",
        "Yan   ",
        "Zach  ",
    ]

    connections = [[0 for i in range(voters)] for j in range(voters)]
    ordered = [[] for i in range(voters)]
    np.random.seed(1052)
    for i in range(voters):
        conn = round(np.random.uniform(0, voters / 2))
        for j in range(conn):
            connectTo = np.random.randint(0, voters)
            if connectTo != i:
                connections[i][connectTo] = 1
    candidateRanking = [[list() for i in range(candidates)] for j in range(voters)]
    for i in range(voters):
        for j in range(candidates):
            candidateRanking[i][j] = [j + 1, round(np.random.uniform(0, 100)) / 10, 0]
        # print(candidateRanking[i])
        s = sorted(candidateRanking[i], reverse=True, key=lambda v: v[SCORE])
        ordered[i] = [s[i][CAND] for i in range(candidates)]
        for v in range(candidates):
            candidate = s[v][CAND] - 1  # which candidate has rank v+1
            candidateRanking[i][candidate][PLACE] = v + 1

    start_voting(names, connections, voters, candidates, candidateRanking, ordered)


def print_connections(names, c, voters, candidates):
    print("CONNECTIONS")
    for i in range(voters):
        print("%10s" % (names[i]), end=" ")
        for j in range(voters):
            print(c[i][j], end=" ")
        print()


def print_rankings(names, r, voters, candidates, ordered):
    print("CANDIDATE Rankings")
    for i in range(voters):
        # print("First choice for {} is {}".format(names[i], ordered[i][CAND]), end=" ")
        print(names[i], end=" ")
        for j in range(candidates):
            print(r[i][j], end="")
        print(" ORDER ", ordered[i])


def start_voting(names, connections, voters, candidates, candidateRanking, ordered):
    original = copy.deepcopy(ordered)
    print("STARTING INFORMATION".center(20, "-"))
    print_connections(names, connections, voters, candidates)
    print_rankings(names, candidateRanking, voters, candidates, ordered)

    print("\n")
    print("PART 1: RANKED CHOICE VOTING".center(20, "-"))
    winner_rank = eleminate_candidates(names, voters, candidates, ordered.copy())
    rank_card, rank_ord = social_welware(
        winner_rank, voters, candidateRanking, candidates, original
    )

    print("\n")
    print("PART 2: SOCIAL NETWORK VOTING".center(20, "-"))
    winner_social = social_network_voting(
        names, connections, voters, candidates, ordered.copy()
    )
    social_card, social_ord = social_welware(
        winner_social, voters, candidateRanking, candidates, original
    )

    print("\n")
    print("COMPARING RESULTS".center(21, "-"))
    print()
    print("Ranked Choice Winner: ", winner_rank)
    print("\tRanked Choice Cardinal Utility: ", rank_card)
    print("\tRanked Choice Ordinal Utility: ", rank_ord)
    print()
    print("Social Network Winner: ", winner_social)
    print("With original ordering:")
    print("\tSocial Network Cardinal Utility: ", social_card)
    print("\tSocial Network Ordinal Utility: ", social_ord)


def eleminate_candidates(names, voters, candidates, ordered):

    eleminate_candidates = []
    remaining_candidates = list(range(1, candidates + 1))
    for round in range(candidates - 1):
        df = pd.DataFrame(ordered)
        firsts = df[0].value_counts(ascending=True).to_frame()
        firsts.index.name = "Candidate"
        firsts.columns = ["Votes"]
        firsts = firsts.reindex(remaining_candidates, fill_value=0)

        if round == 0:
            print()
            print("--INITIAL RANKINGS--".center(20, "-"))
        else:
            print()
            print(f"--AFTER ROUND {round}--".center(21, "-"))

        for i in range(voters):
            print(names[i], end=" ")
            print("->", ordered[i])

        print("\nCURRENT FIRST PLACE TIES:")
        print(firsts.T)

        min_votes = firsts.min().values[0]
        tied = firsts[firsts.values == min_votes].index.tolist()
        # tie for first place
        if len(tied) > 1:
            print("\nTIE")

            last = [sublist[-1] for sublist in ordered]
            last = pd.DataFrame(last)
            lasts = last[0].value_counts().to_frame()
            lasts.index.name = "Candidate"
            lasts.columns = ["Votes"]
            print("\nCURRENT LAST PLACE COUNTS:")
            print(lasts.T)

            lasts = lasts[lasts.index.isin(tied)]
            lasts_max = lasts.max().values[0]
            tied_last = lasts[lasts.values == lasts_max].index.tolist()
            # tie again for last place votes
            if lasts.empty:
                print("(No Last Place Votes for Tied Candidates)")
                print(
                    f"(Randomly selecting loser between the tied first place candidates {tied})"
                )
                loser = np.random.choice(tied)
                eleminate_candidates.append(loser)
                remaining_candidates.remove(loser)

            elif len(tied_last) > 1:
                print("\nTIE AGAIN")
                print(f"(Randomly selecting loser between {tied})")
                loser = np.random.choice(tied)
                eleminate_candidates.append(loser)
                remaining_candidates.remove(loser)

            # no tie for last place votes
            else:
                loser = lasts.idxmax().values[0]
                eleminate_candidates.append(loser)
                remaining_candidates.remove(loser)

        # no tie for first place votes
        else:
            loser = firsts.idxmin().values[0]
            eleminate_candidates.append(loser)
            remaining_candidates.remove(loser)

        print("Losing Candidate: ", loser)
        ordered = [[j for j in i if j != loser] for i in ordered]
        if len(ordered[0]) == 1:
            winner = ordered[0][0]
            print("\nRESULTS:")
            print("Ranked Choice Winner: ", winner)
            print("Order of Elemination: ", eleminate_candidates)
            return winner


def social_network_voting(names, connections, voters, candidates, ordered):
    print_connections(names, connections, voters, candidates)

    knowledge = [[] for i in range(voters)]
    for i in range(len(connections)):
        for j in range(len(connections[i])):
            if connections[i][j] == 1:
                knowledge[i].append(ordered[j])

    # Initialize a variables to keep track of during while loop
    votes_changed = True
    previous_votes = [None for _ in range(voters)]
    round = 0
    cap = 10
    vote_changed = [False for _ in range(voters)]
    # Keep checking for changes every round until no votes change
    while votes_changed:
        votes_changed = False
        vote_changed = [False for _ in range(voters)]

        round += 1
        if round > cap:
            break
        print()
        print(f"Round {round}".center(20, "-"))

        counts = [
            [Counter(candidate[i] for candidate in sublist) for i in range(candidates)]
            for sublist in knowledge
        ]
        for i, sublist_counts in enumerate(counts):

            # Check if there is a tie for the most first-place votes
            most_votes = sublist_counts[0][list(sublist_counts[0].keys())[0]]
            tied_candidates = [
                candidate
                for candidate, votes in sublist_counts[0].items()
                if votes == most_votes
            ]

            if len(tied_candidates) > 1:
                # There is a tie
                if (
                    ordered[i][0] not in tied_candidates
                    and not vote_changed[i]
                    and ordered[i] != previous_votes[i]
                ):

                    # Find the highest-ranked tied candidate in the voter's ordered list
                    highest_ranked_tied_candidate = min(
                        (
                            candidate
                            for candidate in ordered[i]
                            if candidate in tied_candidates
                        ),
                        key=ordered[i].index,
                    )
                    original_choice = ordered[i].copy()
                    # Change vote to the highest-ranked tied candidate
                    ordered[i].remove(highest_ranked_tied_candidate)
                    ordered[i].insert(0, highest_ranked_tied_candidate)
                    print(f"{names[i]}: {original_choice} -> {ordered[i]}")
                    print(
                        "\t(tie of first place, changed vote to highest-ranked tied candidate)"
                    )
                    previous_votes[i] = ordered[i].copy()
                    votes_changed = True
                    vote_changed[i] = True

            # first choice is not the most popular
            if (
                sublist_counts[0][ordered[i][0]] + 1
                < sublist_counts[0][list(sublist_counts[0].keys())[0]]
                and not vote_changed[i]
            ):
                # second choice is a popular first choice
                if ordered[i][1] in list(sublist_counts[0].keys()) or ordered[i][
                    1
                ] in list(sublist_counts[1].keys()):
                    original_choice = ordered[i].copy()
                    # swap first and second choice
                    ordered[i][0], ordered[i][1] = ordered[i][1], ordered[i][0]
                    print(f"{names[i]}: {original_choice} -> {ordered[i]}")
                    print("\t(second choice is more popular than first choice)")
                    previous_votes[i] = ordered[i].copy()
                    votes_changed = True
                    vote_changed[i] = True

            if (
                ordered[i][0] != list(sublist_counts[0].keys())[0]
                and not vote_changed[i]
            ):
                # third choice is popular first choice
                if ordered[i][2] in list(sublist_counts[0].keys()):
                    original_choice = ordered[i].copy()
                    # swap first and third choice
                    ordered[i][0], ordered[i][2] = ordered[i][2], ordered[i][0]
                    print(f"{names[i]}: {original_choice} -> {ordered[i]}")
                    print("\t(third choice is more popular than first choice)")
                    previous_votes[i] = ordered[i].copy()
                    votes_changed = True
                    vote_changed[i] = True

    # After all voters have potentially revised their votes, determine the winner by plurality
    print("\nRESULTS:")
    print("Final Votes:")
    for i in range(voters):
        print(names[i], ordered[i])
    winner = Counter(candidate[0] for candidate in ordered).most_common(1)[0][0]
    print(
        f"Social Network Winner: {winner} with {Counter(candidate[0] for candidate in ordered)[winner]} votes"
    )

    return winner


def social_welware(winner, voters, candidateRanking, candidates, ordered):
    card = cardinal_utility(winner, candidates, voters, candidateRanking, ordered)
    ord = ordinal_utility(winner, voters, ordered)
    print("Cardinal Utility: ", round(card, 2))
    print("Ordinal Utility: ", ord)
    return round(card, 2), ord


def cardinal_utility(winner, candidates, voters, candidateRanking, ordered):
    card_sum = 0

    for i in range(voters):
        values = []
        for j in range(candidates):
            values.append(candidateRanking[i][j][1])
        pref_winner_val = pd.DataFrame(values)[0].max()
        actual_winner_val = candidateRanking[i][winner - 1][1]

        card_sum += abs(actual_winner_val - pref_winner_val)
    return card_sum


def ordinal_utility(winner, voters, ordered):
    ord_sum = 0
    for i in range(voters):
        ord_sum += abs(1 - (ordered[i].index(winner) + 1))
    return ord_sum


if __name__ == "__main__":
    # create_voting(20, 5)
    create_voting(20, 7)
    # create_voting(5, 10)
    # create_voting(7, 5)
