import pandas as pd
from os.path import join
import pickle

class DataHelper(object):

    def __init__(self, input_dir, op_dir, preprocessing_cache):

        self.input_data_dir = input_dir
        self.output_data_dir = op_dir
        self.preprocessing_cache = preprocessing_cache

        self.items_file = 'items.csv'
        self.users_file = 'users.csv'
        self.interactions_file = 'interactions.csv'
        self.target_items = 'targetItems.csv'
        self.target_users = 'targetUsers.csv'

    def read_data_frame(self, filename):
        filename = join(self.input_data_dir, filename)
        doc = open(filename, 'r')
        df = pd.read_csv(doc, sep="\t", header=0, dtype=str)
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
            values.append(line.strip('\n'))
        return values

    def load_cache(self, filename):
        filepath = join(self.preprocessing_cache, filename)
        return pickle.load(open(filepath, 'rb'))

    def write_cache(self, object_to_write, filename):
        filepath = join(self.preprocessing_cache, filename)
        pickle.dump(object_to_write, open(filepath, 'wb'))




