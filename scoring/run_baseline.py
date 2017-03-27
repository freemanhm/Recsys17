import operator
from pprint import pprint

from evaluation import Evaluation

from eval_io_helper import CacheHelper


class ActiveUsersBaseline(object):

    def __init__(self):
        self.cache_helper_instance = CacheHelper()
        # not match on attributes, no thresholding - all 100 taken
        # now considered: week based scoring, revenue based, interaction types
        # 1: 'clicked', '2': 'bookmarked', 3: 'replied', 4:'deleted', 5:'recruiter'}
        # positive interaction types (1, 2, 3, 5) neg interactions (4), impressions (0)
        #  if week_num >= 45:
        #    local_score += 5

    def baseline_recommend(self):
        print "Calculating baseline by recommending recently active users:"
        target_items_list = self.cache_helper_instance.load_cache('target_items_list')
        r1, r2, r3 = self.rank_by_activity()
        print "Performing baselining 1"
        self.solutions(r1, 1, target_items_list)
        print "Performing baselining 2"
        self.solutions(r2, 2, target_items_list)
        print "Performing baselining 3"
        self.solutions(r3, 3, target_items_list)
        print "Finished"

    def solutions(self, activity_ranked_users, i, target_items_list):
        recs = {}
        for t in target_items_list:
            recs[t] = activity_ranked_users
        self.cache_helper_instance.write_cache(recs, 'raw_rec_baseline')
        e = Evaluation('baseline'+str(i), recs)
        # e.evaluate_recommendations()

    def rank_by_activity(self):
        print "Load preprocessing cache files:"
        inters = self.cache_helper_instance.load_cache('user_inter_dist')
        prem_users = self.cache_helper_instance.load_cache('prem_user')
        # paid_items = self.cache_helper_instance.load_cache('paid_item')
        target_users_set = self.cache_helper_instance.load_cache('target_users_set')
        print "Ranking by activity:"

        # scoring functions - "weighted-neg", "weighted-nonneg", "nonweighted-nonneg"
        s1 = {}
        s2 = {}
        s3 = {}
        for u in target_users_set:
            if u in inters:
                interactions_u = inters[u]
                score_list = self.score_users(interactions_u, u in prem_users)
                if score_list[0]!=-1:
                    s1[u] = score_list[0]
                if score_list[1]!=-1:
                    s2[u] = score_list[1]
                if score_list[2]!=-1:
                    s3[u] = score_list[2]
        r1 = self.get_rank_list(s1)
        r2 = self.get_rank_list(s2)
        r3 = self.get_rank_list(s3)
        return r1, r2, r3


    def get_rank_list(self, s):
        ranked_list = sorted(s.items(), key=operator.itemgetter(1), reverse=True)
        ranked_list = ranked_list[0:100]
        print ranked_list
        rank = []
        for r in ranked_list:
            rank.append(r[0])
        print "Finished Ranking"
        return rank

    def score_users(self, inter_u, isPrem):
        scores = list()
        "weighted-neg", "weighted-nonneg", "nonweighted-nonneg"

        local_score = 0; has_neg = False; non_weighted_local_score = 0
        for week_num in inter_u.keys():
            if inter_u[week_num][4] > 0:
                has_neg = True
            for inter_type in range(0, 5):
                count = inter_u[week_num][inter_type]
                non_weighted_local_score += count
                if inter_type == 1:
                    local_score += count
                elif inter_type == 2 or inter_type == 3:
                    local_score += 5 * count
                elif inter_type == 5:
                    local_score += 20 * count

        premium_boost = 2 if isPrem else 1
        local_score *= premium_boost

        weight_neg_score = local_score
        weighted_nonneg_score = -1 if has_neg else local_score
        nonweighted_nonneg_score = -1 if has_neg else non_weighted_local_score

        scores.append(weight_neg_score)
        scores.append(weighted_nonneg_score)
        scores.append(nonweighted_nonneg_score)
        return scores

def main():
    b = ActiveUsersBaseline()
    b.baseline_recommend()

if __name__ == '__main__':
    main()




