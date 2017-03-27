from os.path import join
from datetime import datetime
import pandas as pd
from pprint import pprint
import pickle

input_data_dir = "../data_2017_weeks"
output_data_dir = "../data_2017_weeks"

interactions_file = 'interactions.csv'


class FindLocalEvalStats(object):

    def create_stats(self):
        print "Reading interactions"
        df = self.read_data_frame(interactions_file)
        # original : user_id, item_id, interaction_type, time

        timestamp = df.iloc[:, 3]
        week_num = [self._to_week(t) for t in timestamp]
        max_week_num = max(week_num)
        min_week_num = min(week_num)

        week_dict = {1: 1, 2:2, 3:3, 4:4, 5:5, 6:6, 44: 7, 45:8, 46:9, 50:10, 51:11, 52:12}
        f = open(join(output_data_dir, 'local_eval_stats'), 'w')
        fdump = open(join(output_data_dir, 'local_eval_dump'), 'wb')

        f.write("\nMAX="+str(max_week_num))
        f.write("\nMIN="+str(min_week_num))
        f.write("\nCount interactions: All items -> Week : With T users (no imps) \n")

        count_in_week = {}

        target_items = set(self.read_target_list('targetItems.csv'))
        target_users = set(self.read_target_list('targetUsers.csv'))

        rows = df.values

        for row, week in zip(rows, week_num):
            user = row[0]
            item = row[1]
            if user in target_users and item not in target_items:
                if item not in count_in_week:
                    count_in_week[item] = [0]*13
                count_in_week[item][week_dict[week]] += 1

        pprint(count_in_week, f)
        f.close()
        pickle.dump(count_in_week, fdump)
        fdump.close()

    def _to_week(self, timestamp):
        return datetime.fromtimestamp(int(timestamp)).isocalendar()[1]

    def read_data_frame(self, filename):
        filename = join(input_data_dir, filename)
        df = pd.read_csv(open(filename, 'r'), sep="\t", header=0, dtype=str)
        return df

    def read_target_list(self, filename):
        filename = join(input_data_dir, filename)
        doc = open(filename, 'r')
        doc.readline()
        values = []
        for line in doc.readlines():
            values.append(line.strip('\n'))
        return values


def main():
    print ("Data Recsys 2017 Pre-processing Limiting interactions by week:")
    p = FindLocalEvalStats()
    p.create_stats()
    print ("Finished preprocessing")

if __name__ == "__main__":
    main()
