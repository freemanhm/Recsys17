from cache_helper import load_cache
from os.path import join
import pickle

class Evaluation(object):

    def __init__(self, prep_cache_dir):
        self.local_eval_t_items = load_cache(prep_cache_dir, 'local_eval_t_item_set')
        self.t_item_list = load_cache(prep_cache_dir, 'target_items_list')
        self.true_interactions = load_cache(prep_cache_dir, 'val_interaction_counts')
        self.prem_user = load_cache(prep_cache_dir, 'prem_user')
        self.paid_item = load_cache(prep_cache_dir, 'paid_item')

    def format_submission(self, recs_local, recs_online, sol_dir, local_filename, sub_filename):
        scores = self.local_eval_on(recs_local)
        self.local_write_scores(scores, local_filename, sol_dir)
        self.online_solutions_write(recs_online, sol_dir, sub_filename)

    def local_eval_on(self, recs):
        print "Beginning evaluations"
        score_list = list()
        score_list.append(self.evaluate(False, False, recs))
        score_list.append(self.evaluate(True, False, recs))
        score_list.append(self.evaluate(False, True, recs))
        score_list.append(self.evaluate(True, True, recs))
        print "Done with evaluation scores"
        return score_list

    def local_write_scores(self, score_list, filename, sol_dir):
        filepath = join(sol_dir, filename)
        f = open(filepath, 'w')
        f.write("Evaluation Score (Overall: Neg included, ItemSucess included):" + str(score_list[0]) + '\n')
        f.write("Evaluation Score (Positive: Neg excluded, Itemsuccess included):" + str(score_list[1]) + '\n')
        f.write("Evaluation Score (Overall_UserSuccess: Neg included, Itemsuccess excluded):" + str(score_list[2]) + '\n')
        f.write("Evaluation Score (Positive_UserSuccess: Neg excluded, Itemsuccess excluded):" + str(score_list[3]) + '\n')
        f.close()
        print "Wrote Evaluation Score to file"

    def online_solutions_write(self, rec, solutions_dir, subfilename):
        print ("Writing submission file")
        submissionsfilepath = join(solutions_dir, subfilename)
        f = open(submissionsfilepath, 'w')
        for t in self.t_item_list:
            string_users = ''
            for u in rec[t]:
                string_users = string_users + str(u) + ","
            if len(string_users) > 0:
                string_users = string_users.rstrip(",")
            f.write(str(t) + "\t" + string_users + '\n')
        f.close()
        print "Wrote solutions"

    def evaluate(self, score_function_exclude_neg, score_function_exclude_itemsuccess, recs):
        print "Evaluating.."
        score = sum(map(lambda item: self.scoring(item, recs[item], score_function_exclude_neg,
                                                  score_function_exclude_itemsuccess), self.local_eval_t_items))
        return score

    def scoring(self, item, users, score_function_exclude_neg, score_function_exclude_itemsuccess):
        user_success_scores = {}
        score = sum(map(lambda u: self.user_success(item, u, score_function_exclude_neg, user_success_scores), users))
        if not score_function_exclude_itemsuccess:
            score += self.item_success(item, users, user_success_scores)
        return score

    def user_success(self, item, user, score_function_exclude_neg, user_success_scores):
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

        user_success_scores[keystr] = interaction_score
        return interaction_score

    def premium_boost(self, user):
        if user in self.prem_user:
            return 2
        else:
            return 1

    def item_success(self, item, users, user_success_scores):
        success = filter(lambda u: user_success_scores[item+'-'+u] > 0, users)
        if len(success) > 0:
            if item in self.paid_item:
                item_success = 50
            else:
                item_success = 25
        else:
            item_success = 0
        return item_success
