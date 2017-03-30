from scoring.eval_io_helper import CacheHelper

# todo

class Filter:


    def __init__(self):
        self.cache_helper_instance = CacheHelper()

        self.neg_users = self.cache_helper_instance.load_cache('neg_users')
        self.n_set = set()
        for user, count in self.neg_users.items():
            if count[1] > 0:
                self.n_set.add(user)
        self.cache_helper_instance.write_cache('neg_users_set')

    def filter_rec(self, rec):
        self.neg_users = self.cache_helper_instance.load_cache('neg_users_set')
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

if __name__ == '__main__':
    Filter()

