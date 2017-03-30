import operator
from cache_helper import load_cache, log_recs
from evaluate import Evaluation

""" STRATEGY 1::2::3 respectively
scoring functions - "weighted-neg", "weighted-nonneg", "nonweighted-nonneg"
[Weighted: weighting by interaction type and prem user]
[Nonneg: filter out users that have any type 4-only observations]
[not content based, no thresholding]
"""

"""
Online | tr + va obs | target_items_list
Local | tr obs | local_eval_items_set
"""


def baseline(prep_cache_dir, sol_dir):
    print "Starting Baseline"
    e = Evaluation(prep_cache_dir)
    t_users = load_cache(prep_cache_dir, 'target_users_set')
    local_t_items = load_cache(prep_cache_dir, 'local_eval_t_item_set')
    local_baseline_counts = load_cache(prep_cache_dir, 'tr_baseline_counts')
    online_t_items = set(load_cache(prep_cache_dir, 'target_items_list'))
    online_baseline_counts = load_cache(prep_cache_dir, 'tr_va_baseline_counts')

    strategy = [1, 2, 3]
    for s in strategy:
        print "Baseline strategy", s
        local_filename = str(s)+'_baseline_local_eval_scores.txt'
        sub_filename = str(s)+'_baseline_submission.txt'
        local_rec_dump = str(s) +'_baseline_local_raw_rec'
        online_rec_dump = str(s) + '_baseline_online_raw_rec'
        local_recs = baseline_recommend(t_users, local_baseline_counts, local_t_items, s, prep_cache_dir)
        online_recs = baseline_recommend(t_users, online_baseline_counts, online_t_items, s, prep_cache_dir)
        log_recs(local_recs, local_rec_dump, sol_dir)
        log_recs(online_recs, online_rec_dump, sol_dir)
        e.format_submission(local_recs, online_recs, sol_dir, local_filename, sub_filename)
    print "Done with Baseline"


def baseline_recommend(t_users, obs, t_items, strategy, prep_cache_dir):
    ranked = rank_by_activity(t_users, obs, strategy, prep_cache_dir)
    recs = recommend(ranked, t_items)
    return recs


def recommend(activity_ranked_users, target_items_list):
    recs = {}
    for t in target_items_list:
        recs[t] = activity_ranked_users
    return recs


def rank_by_activity(t_users, obs, strategy, prep_cache_dir):
    print 'Ranking by activity'
    prem_users = load_cache(prep_cache_dir, 'prem_user')
    s = score_users(t_users, obs, strategy, prem_users)
    ranked = get_rank_list(s)
    print "Finished rank by activity"
    return ranked


def score_users(t_users, obs, strategy, prem_users):
    user_scores_weighted, user_scores_nonweighted, neg_users = score_users_by_obs(t_users, obs, prem_users)
    if strategy == 1:
        return user_scores_weighted
    elif strategy == 2:
        return filter_out_neg(user_scores_weighted, neg_users)
    elif strategy == 3:
        return filter_out_neg(user_scores_nonweighted, neg_users)
    elif strategy == 4:
        return user_scores_nonweighted
    else:
        return {}


def filter_out_neg(user_scores, neg_users):
    s = {}
    for user in user_scores:
        if user not in neg_users:
            s[user] = user_scores[user]
    return s


def score_users_by_obs(t_users, obs, prem_users):
    user_scores_weighted = {}
    user_scores_nonweighted = {}
    neg_users = set()

    for key in t_users:
        user_scores_weighted[key] = 0
        user_scores_nonweighted[key] = 0

    for user, counts in obs.items():

        if counts[4] > 0:
            neg_users.add(user)

        user_scores_nonweighted[user] += 1
        add_score = 0
        add_score += counts[1]
        add_score += 5 * (counts[2] + counts[3])
        add_score += 20 * counts[5]
        add_score -= 10 * counts[4]

        premium_boost = 2 if user in prem_users else 1
        add_score *= premium_boost
        user_scores_weighted[user] += add_score

        user_scores_nonweighted[user] += counts[1] + counts[2] + counts[3] + counts[5]

    return user_scores_weighted, user_scores_nonweighted, neg_users


def get_rank_list(s):
    ranked_list = sorted(s.items(), key=operator.itemgetter(1), reverse=True)
    ranked_list = ranked_list[0:100]
    rank = []
    for r in ranked_list:
        rank.append(r[0])
    return rank


if __name__ == '__main__':
    prep_cache_dir = "../examples/preprocessing_cache"
    sol_dir = "../solutions"
    baseline(prep_cache_dir, sol_dir)


"""
for row in obs:
        user = row[1]
        int_type = row[3]
        # re-ordered: item_id, user_id, time, type
        if int_type == '4':
            neg_users.add(user)
        if user not in user_scores_weighted:
            user_scores_weighted[user] = 0
        if user not in user_scores_nonweighted:
            user_scores_nonweighted[user] = 0
        user_scores_nonweighted[user] += 1
        add_score = 0
        if int_type == '1':
            add_score += 1
        elif int_type == '2' or int_type == '3':
            add_score += 5
        elif int_type == '5':
            add_score += 20
        elif int_type == '4':
            add_score -= 10
        premium_boost = 2 if user in prem_users else 1
        add_score *= premium_boost
        user_scores_weighted[user] += add_score
"""
