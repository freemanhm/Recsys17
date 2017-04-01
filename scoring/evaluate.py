from cache_helper import load_cache
from os.path import join
import pickle


class Evaluation(object):

    def __init__(self, prep_cache_dir):
        self.local_eval_t_items = load_cache(prep_cache_dir, 'target_items_local_set')
        self.t_item_list = load_cache(prep_cache_dir, 'target_items_list')
        self.true_interactions = load_cache(prep_cache_dir, 'val_interaction_counts')
        self.prem_user = load_cache(prep_cache_dir, 'prem_user_set')
        self.paid_item = load_cache(prep_cache_dir, 'paid_item_set')

    def format_submission(self, recs_local, recs_online, sol_dir, local_filename, sub_filename):
        scores = self.local_eval_on(recs_local)
        self.local_write_scores(scores, local_filename, sol_dir)
        self.online_solutions_write(recs_online, sol_dir, sub_filename)

    def local_write_scores(self, score_list, filename, sol_dir):
        filepath = join(sol_dir, filename)
        f = open(filepath, 'w')
        f.write(str(score_list[0]) + ", "+ str(score_list[1])+ ", " +str(score_list[2])+", "+str(score_list[3])+"\n")
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
            if t in rec:
                for u in rec[t]:
                    string_users = string_users + str(u) + ","
                if len(string_users) > 0:
                    string_users = string_users.rstrip(",")
            f.write(str(t) + "\t" + string_users + '\n')
        f.close()
        print "Wrote solutions"

    def local_eval_on(self, recs):
        print "Beginning evaluations"
        eval_scores_list = [0, 0, 0, 0]
        for item, recoms in recs.items():
            item_scores_list = self.score_item(item, recoms)
            for i in range(4):
                eval_scores_list[i]+= item_scores_list[i]
        print "Done with evaluation scores"
        return eval_scores_list

    def score_item(self, item, recoms):

        item_score_cum, item_score_neg_excl_cum = 0, 0
        success, neg_excluded_success = False, False
        for user in recoms:
            user_success_score, neg_excluded_score = self.get_user_success(item, user)
            item_score_cum += user_success_score
            item_score_neg_excl_cum += neg_excluded_score
            if user_success_score > 0:
                success = True
            if neg_excluded_score > 0:
                neg_excluded_success = True

        """
        0 - item_score_cum + success
        1 - item_score_neg_excl_cum + neg_excluded_success
        2 - item_score_cum
        3 - item_score_neg_excl_cum
        """
        item_scores_list = [0, 0, 0, 0]
        item_scores_list[2] = item_score_cum
        item_scores_list[3] = item_score_neg_excl_cum
        item_scores_list[0] = item_score_cum + self.get_item_success(item, success)
        item_scores_list[1] = item_score_neg_excl_cum + self.get_item_success(item, neg_excluded_success)

        return item_scores_list

    def get_item_success(self, item, success):
        item_success_score = 0
        if success and item in self.paid_item:
            item_success_score = 50
        elif success:
            item_success_score = 25
        return item_success_score

    def get_user_success(self, item, user):
        interaction_score = 0
        neg_excluded_score = 0
        key_str = str(item) + "-" + str(user)
        if key_str in self.true_interactions:
            type_counts = self.true_interactions[key_str]
            add_score = 0
            if type_counts[1] > 0:
                add_score += 1
            elif type_counts[2] > 0 or type_counts[3] > 0:
                add_score += 5
            elif type_counts[5] > 0:
                add_score += 20

            neg_excluded_score += add_score
            interaction_score += add_score

            if type_counts[4] > 0 and add_score == 0:
                interaction_score -= 10

        if user in self.prem_user:
            interaction_score *= 2
            neg_excluded_score *= 2

        return interaction_score, neg_excluded_score
