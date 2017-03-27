from stats_io_helper import CacheHelper
from operator import add

class Stats(object):

    def __init__(self):
        self.cache_helper_instance = CacheHelper()

    def user_dist(self):
        print "Loading for user dist"
        user_int_counts = self.cache_helper_instance.load_cache('user_inter_dist')
        target_users = self.cache_helper_instance.load_cache('target_users_set')
        print "Done loading"
        t_users_counts = {}
        t_users_cumulative = {}
        for u in target_users:
            if u in user_int_counts:
                t_users_counts[u] = user_int_counts[u]
                count_cum = [0]*6
                for w, count in user_int_counts[u].items():
                    count_cum = map(add, count_cum, count)
                t_users_cumulative[u] = count_cum
        self.cache_helper_instance.write_to_file(t_users_cumulative, 'target-users-cumulative')
        self.cache_helper_instance.write_to_file(t_users_counts, 'target-user-per-week')
        self.cache_helper_instance.write_to_file(user_int_counts, 'all-user-per-week')
        print "Finished user dist"


def main():
    s = Stats()
    s.user_dist()
    print "Finished"

if __name__ == main():
    main()