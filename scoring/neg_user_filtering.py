from eval_io_helper import CacheHelper


class Filter:

    def __init__(self):
        self.cache_helper_instance = CacheHelper()

        self.neg_users = self.cache_helper_instance.load_cache('neg_users')
        self.n_set = set()
        for user, count in self.neg_users.items():
            if count[1] > 0:
                self.n_set.add(user)
        self.cache_helper_instance.write_cache('neg_users_set')


if __name__ == '__main__':
    Filter()

