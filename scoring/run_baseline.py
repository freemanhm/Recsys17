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
    print "Loading cache"
    t_users = load_cache(prep_cache_dir, 'target_users_set')
    local_t_items = load_cache(prep_cache_dir, 'target_items_local_set')
    local_baseline_counts = load_cache(prep_cache_dir, 'tr_baseline_counts')
    online_t_items = set(load_cache(prep_cache_dir, 'target_items_list'))
    online_baseline_counts = load_cache(prep_cache_dir, 'tr_va_baseline_counts')
    prem_users = load_cache(prep_cache_dir, 'prem_user_set')
    print "Done loading"
    print "Score users by tr obs"
    local_temp = score_users_by_obs(t_users, local_baseline_counts, prem_users)
    print "Score users by tr+va obs"
    online_temp = score_users_by_obs(t_users, online_baseline_counts, prem_users)

    strategy = [1, 2, 3]
    for s in strategy:
        print "Baseline strategy", s
        local_filename = str(s)+'_baseline_local_eval_scores.txt'
        sub_filename = str(s)+'_baseline_submission.txt'
        local_rec_dump = str(s) +'_baseline_local_raw_rec'
        online_rec_dump = str(s) + '_baseline_online_raw_rec'
        local_recs = baseline_recommend(local_temp, local_t_items, s)
        online_recs = baseline_recommend(online_temp, online_t_items, s)
        log_recs(local_recs, local_rec_dump, sol_dir)
        log_recs(online_recs, online_rec_dump, sol_dir)
        e.format_submission(local_recs, online_recs, sol_dir, local_filename, sub_filename)
    print "Done with Baseline"


def baseline_recommend(temp_list, t_items, strategy):
    ranked = rank_by_activity(temp_list, strategy)
    recs = recommend(ranked, t_items)
    return recs


def recommend(activity_ranked_users, target_items_list):
    u_integers = []
    for user in activity_ranked_users:
        u_integers.append(user)
    recs = {}
    for t in target_items_list:
        recs[t] = u_integers
    return recs


def rank_by_activity(temp_list, strategy):
    s = {}
    user_scores_weighted, user_scores_nonweighted, neg_users = temp_list[0], temp_list[1], temp_list[2]
    if strategy == 1:
        s = user_scores_weighted
    elif strategy == 2:
        s = filter_out_neg(user_scores_weighted, neg_users)
    elif strategy == 3:
        s = filter_out_neg(user_scores_nonweighted, neg_users)
    elif strategy == 4:
        s = user_scores_nonweighted
    ranked = get_rank_list(s)
    return ranked


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