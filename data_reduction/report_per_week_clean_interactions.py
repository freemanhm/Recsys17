from os.path import join
from datetime import datetime
import pandas as pd
from pprint import pprint

input_data_dir = "../data_2017_filtered_interactions"
output_data_dir = "../stats"

interactions_file = 'clean_interactions.csv'

"""
Will work after separation of clean interactions from other target_user limiting
"""
"""
Reports target users based statistics for interaction counts
Note: Weeks wrap around - 44 to 52 then 1 to 6
"""
class FindLocalEvalStats(object):

    def __init__(self):
        self.target_items = set(self.read_target_list('targetItems.csv'))
        self.target_users = set(self.read_target_list('targetUsers.csv'))

    def create_stats(self):
        print "Reading interactions"
        df = self.read_data_frame(interactions_file)
        # original : user_id, item_id, interaction_type, time

        timestamp = df.iloc[:, 3]
        week_num = [self._to_week(t) for t in timestamp]
        print set(week_num)

        week_keys = [44, 45, 46, 47, 48, 49, 50, 51, 52, 1, 2, 3, 4, 5, 6]
        count_in_week_with_imp = {}
        count_in_week_without_imp = {}

        # but impresssions are removed from data_2017_weeks

        for w in week_keys:
            count_in_week_with_imp[w] = [0]*5
            count_in_week_without_imp[w] = [0]*5

        # All t_item-nt_user  t_item-t_user nt_item-nt_user  nt_item-t_user

        rows = df.values

        for row, week in zip(rows, week_num):
            user = row[0]
            item = row[1]
            if row[2] != '0':
                count_array = count_in_week_without_imp[week]
                self.update(count_array, user, item)
            count_array = count_in_week_with_imp[week]
            self.update(count_array, user, item)

        f = open(join(output_data_dir, 'week_max_min_interation-counts'), 'w')
        f.write("\nCount interactions: Per Weeks\n")
        '''
        f.write("\n---------------------------------")
        f.write("\nWith impressions")
        f.write("\nAll\tt_item-nt_user\tt_item-t_user\tnt_item-nt_user\tnt_item-t_user\n")
        pprint(count_in_week_with_imp, f)
        '''
        f.write("\n---------------------------------")
        f.write("\nWithout impressions")
        f.write("\nAll\tt_item-nt_user\tt_item-t_user\tnt_item-nt_user\tnt_item-t_user\n")
        pprint(count_in_week_without_imp, f)
        f.close()

    def update(self, count_array, user, item):
        count_array[0] += 1
        t_item = 1 if item in self.target_items else 0
        t_user = 1 if user in self.target_users else 0
        if t_item and not t_user:
            count_array[1] += 1
        elif t_item:
            count_array[2] += 1
        elif not t_item and not t_user:
            count_array[3] += 1
        else:
            count_array[4] += 1
        return

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
    print ("Data Recsys 2017 Initial Interaction Stats:")
    p = FindLocalEvalStats()
    p.create_stats()
    print ("Finished.")

if __name__ == "__main__":
    main()
