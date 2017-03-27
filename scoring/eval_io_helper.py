from os.path import join
import pickle


class CacheHelper(object):

    def __init__(self, pr_cache='../examples/preprocessing_cache', solutions_dir='../solutions'):
        self.preprocessing_cache = pr_cache
        self.solutions_dir = solutions_dir

    def load_recs(self, filename):
        filepath = join(self.solutions_dir, filename)
        return pickle.load(open(filepath, 'rb'))

    def load_cache(self, filename):
        filepath = join(self.preprocessing_cache, filename)
        return pickle.load(open(filepath, 'rb'))

    def write_cache(self, object_to_write, filename):
        filepath = join(self.preprocessing_cache, filename)
        pickle.dump(object_to_write, open(filepath, 'wb'))

    def solutions_write(self, rec, subfilename, target_items_list):
        print ("Writing submission file")
        submissionsfilepath = join(self.solutions_dir, subfilename)
        f = open(submissionsfilepath, 'w')
        for t in target_items_list:
            string_users = ''
            for u in rec[t]:
                string_users = string_users + str(u) + ","
            if len(string_users) > 0:
                string_users = string_users.rstrip(",")
            f.write(str(t) + "\t" + string_users + '\n')
        f.close()
        print "Wrote solutions"

    def evaluation_scores_write(self, filename, score_list):
        filename = join(self.solutions_dir, filename)
        f = open(filename, 'w')
        f.write("Evaluation Score (Overall: Neg included, ItemSucess included):" + str(score_list[0]) + '\n')
        f.write("Evaluation Score (Positive: Neg excluded, Itemsuccess included):" + str(score_list[1]) + '\n')
        f.write("Evaluation Score (Overall_UserSuccess: Neg included, Itemsuccess excluded):" + str(score_list[2]) + '\n')
        f.write("Evaluation Score (Positive_UserSuccess: Neg excluded, Itemsuccess excluded):" + str(score_list[3]) + '\n')
        f.close()
        print "Finished Evaluations"




