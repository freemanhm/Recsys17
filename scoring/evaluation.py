
from eval_io_helper import CacheHelper


class Evaluation(object):

    def __init__(self, tag, rec):
        self.cache_helper_instance = CacheHelper()
        self.tag = tag
        self.prem_user = self.cache_helper_instance.load_cache('prem_user')
        self.paid_item = self.cache_helper_instance.load_cache('paid_item')
        self.neg_users = self.cache_helper_instance.load_cache('neg_users_set')
        self.true_interactions = self.cache_helper_instance.load_cache('test_week_true_data')
        self.target_items_list = self.cache_helper_instance.load_cache('target_items_list')
        self.target_users_set = self.cache_helper_instance.load_cache('target_users_set')
        self.filtered_recs = self.filter_rec(rec)
        self.cache_helper_instance.solutions_write(self.filtered_recs, self.tag + '_submissions.txt',
                                                   self.target_items_list)

    def filter_rec(self, rec):
        print "Recommendations for target items: Filtering to include target users only (already restricted set)" \
              "Removing neg users"
        # dictionary mapping targetItem to its recommended users
        filtered_recs = {}
        for t_item in self.target_items_list:
            users_rec = []
            if t_item in rec:
                for u in rec[t_item]:
                    if u not in self.neg_users:
                        users_rec.append(u)
            filtered_recs[t_item] = users_rec
        print "Filtered"
        return filtered_recs

    def evaluate_recommendations(self):
        score_list = list()
        score_list.append(self.evaluate(False, False))
        score_list.append(self.evaluate(True, False))
        score_list.append(self.evaluate(False, True))
        score_list.append(self.evaluate(True, True))
        self.cache_helper_instance.evaluation_scores_write(self.tag+"_eval_scores.txt", score_list)

    def evaluate(self, score_function_exclude_neg, score_function_exclude_itemsuccess):
        print "Evaluating.."
        self.user_success_scores = {}
        score = sum(map(lambda item: self.scoring(item, self.filtered_recs[item], score_function_exclude_neg,
                                                  score_function_exclude_itemsuccess), self.target_items_list))
        return score

    def scoring(self, item, users, score_function_exclude_neg, score_function_exclude_itemsuccess):
        score = sum(map(lambda u: self.user_success(item, u, score_function_exclude_neg), users))
        if not score_function_exclude_itemsuccess:
            score += self.item_success(item, users)
        return score

    def user_success(self, item, user, score_function_exclude_neg):
        interaction_score = 0
        # 1: 'clicked', '2': 'bookmarked', 3: 'replied', 4:'deleted', 5:'recruiter'}
        keystr = item + "-" + user

        if keystr in self.true_interactions:
            type_counts = self.true_interactions[keystr]

            if type_counts[1] > 0:
                interaction_score += 1
            elif type_counts[2] > 0 or type_counts[3] > 0:
                interaction_score += 5
            elif type_counts[5] > 0:
                interaction_score += 20

            if (not score_function_exclude_neg) and (interaction_score == 0 and type_counts[4] > 0):
                interaction_score -= 10

            interaction_score *= self.premium_boost(user)

        self.user_success_scores[keystr] = interaction_score
        return interaction_score

    def premium_boost(self, user):
        if user in self.prem_user:
            return 2
        else:
            return 1

    def item_success(self, item, users):
        success = filter(lambda u: self.user_success_scores[item+'-'+u] > 0, users)
        if len(success) > 0:
            if item in self.paid_item:
                item_success = 50
            else:
                item_success = 25
        else:
            item_success = 0
        return item_success


def main():
    # baseline
    # local eval
    # online submission
    recs = CacheHelper().load_recs('raw_rec')
    e = Evaluation('', recs)
    e.evaluate_recommendations()

if __name__ == '__main__':
    main()
