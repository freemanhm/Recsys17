

def filter_recs(recs, limited_set_integers):
    filtered = {}
    for item, values in recs.items():
        user_list = []
        for u in values:
            if u in limited_set_integers:
                user_list.append(u)
        filtered[item] = user_list
    return filtered


def filter_out_negs(recs, neg_set_integers):
    filtered = {}
    for item, values in recs.items():
        user_list = []
        for u in values:
            if u not in neg_set_integers:
                user_list.append(u)
        filtered[item] = user_list
    return filtered


def cutoff100(recs):
    filtered = {}
    for item, values in recs.items():
        filtered[item] = values[0:100]
    return filtered

