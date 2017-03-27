from os.path import join
import pickle
from pprint import pprint

class CacheHelper(object):

    def __init__(self, pr_cache='../examples/preprocessing_cache', stats_dir='../stats'):
        self.preprocessing_cache = pr_cache
        self.stats_dir = stats_dir

    def load_cache(self, filename):
        filepath = join(self.preprocessing_cache, filename)
        return pickle.load(open(filepath, 'rb'))

    def write_cache(self, object_to_write, filename):
        filepath = join(self.preprocessing_cache, filename)
        pickle.dump(object_to_write, open(filepath, 'wb'))

    def write_to_file(self, object_to_write, filename):
        print "Writing: " + filename
        filepath = join(self.stats_dir, filename)
        f = open(filepath, 'w')
        pprint(object_to_write, f)
        f.close()

