import pandas as pd
from os.path import join
import pickle
from pprint import pprint


class DataHelper(object):

    def __init__(self, input_dir, op_dir, preprocessing_cache, stats_dir):

        self.input_data_dir = input_dir
        self.output_data_dir = op_dir
        self.preprocessing_cache = preprocessing_cache
        self.stats_dir = stats_dir

        self.items_file = 'items.csv'
        self.users_file = 'users.csv'
        self.target_items = 'targetItems.csv'
        self.target_users = 'targetUsers.csv'

    def read_data_frame(self, filename):
        filename = join(self.input_data_dir, filename)
        doc = open(filename, 'r')
        df = pd.read_csv(doc, sep="\t", header=0)
        return df

    def read_interactions_data_frame(self, limited_interactions_file):
        dir = '../data_2017_filtered_interactions'
        filename = join(dir, limited_interactions_file)
        doc = open(filename, 'r')
        df = pd.read_csv(doc, sep="\t", header=0)
        return df

    def write_data_frame(self, filename, data):
        filename = join(self.output_data_dir, filename)
        doc = open(filename, 'w')
        data.to_csv(doc, sep='\t', header=True, index=False)
        return

    def read_target_list(self, filename):
        filename = join(self.input_data_dir, filename)
        doc = open(filename, 'r')
        doc.readline()
        values = []
        for line in doc.readlines():
            values.append(int(line.strip('\n')))
        return values

    def load_cache(self, filename):
        filepath = join(self.preprocessing_cache, filename)
        return pickle.load(open(filepath, 'rb'))

    def write_cache(self, object_to_write, filename):
        filepath = join(self.preprocessing_cache, filename)
        pickle.dump(object_to_write, open(filepath, 'wb'))

    def write_int_targets(self, int_t_item_list, filename):
        filepath = join(self.output_data_dir, filename)
        pickle.dump(int_t_item_list, open(filepath, 'wb'))

    def write_stats(self, statistics, filename, msg):
        f = open(join(self.stats_dir, filename), 'w')
        f.write(msg)
        pprint(statistics, f)
        f.close()






