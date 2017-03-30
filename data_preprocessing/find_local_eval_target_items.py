from data_helper import DataHelper
from datetime import datetime
import pandas as pd
from pprint import pprint
from os.path import join


class ProcessData(object):

    def __init__(self):
        self.data_helper_instance = DataHelper(input_dir='../data_2017',
                                               op_dir='../stats',
                                               preprocessing_cache='../examples/preprocessing_cache')
        self.output_dir = '../stats'
        print "Reading interactions"
        self.limited_interactions = 'target_user_interactions.csv'
        self.df = self.data_helper_instance.read_interactions_data_frame(self.limited_interactions)

        print "Reading target items and target users"
        t_item_list = self.data_helper_instance.read_target_list('targetItems.csv')
        self.t_items = set(t_item_list)
        # self.t_users = set(self.data_helper_instance.read_target_list('targetUsers.csv'))

    def create_observation_stats(self):

        # original : user_id, item_id, interaction_type, time

        timestamp = self.df.iloc[:, 3]
        week_num = [self._to_week(t) for t in timestamp]
        val_week_set = set([6, 5])

        # dict with keys as all items [target item 1, count in va weeks, count in tr weeks]
        count_per_item = {}

        print "Starting with iterations on interactions"

        rows = self.df.values

        for row, week in zip(rows, week_num):
            item = row[1]
            if item in self.t_items:
                continue
            if item not in count_per_item:
                count_per_item[item] = [0]*2
            if week in val_week_set:
                count_per_item[item][0] += 1
            else:
                count_per_item[item][1] += 1

        f = open(join(self.output_dir, 'local_eval_stats'), 'w')
        f.write('non-target items: val|tr\n\n')
        pprint(count_per_item, f)
        f.close()
        f = open(join(self.output_dir, 'local_eval_items'), 'w')
        f2 = open(join(self.output_dir, 'local_eval_sanity_check'), 'w')
        local_eval_item_set = set()
        for item, count in count_per_item.items():
            if count[1] == 0:
                f.write(item + '\t' + str(count[0]) + '\n')
                # f.write(item + '\t' + '0' + '\n')
                local_eval_item_set.add(item)
            else:
                f2.write(item + '\t' + str(count[0]+count[1]) + '\t' + str(count[1]) + '\n')
        f.close()
        f2.close()
        self.data_helper_instance.write_cache(local_eval_item_set, 'local_eval_t_item_set')
        print len(local_eval_item_set)


    def _to_week(self, timestamp):
        t = int(timestamp)
        return datetime.fromtimestamp(t).isocalendar()[1]


def main():
    print ("Data Recsys 2017 Local Eval stats:")
    p = ProcessData()
    p.create_observation_stats()

    print ("Finished.")

if __name__ == "__main__":
    main()
