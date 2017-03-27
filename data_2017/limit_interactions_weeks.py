from os.path import join
from datetime import datetime
import pandas as pd
from pprint import pprint

input_data_dir = "../data_2017"
output_data_dir = "../data_2017_weeks"

interactions_file = 'interactions.csv'
limited_interactions_file = 'interactions.csv'


class LimitInteractions(object):

    def create_observations(self):
        print "Reading interactions"
        df = self.read_data_frame(interactions_file)
        df = df.drop_duplicates()
        # original : user_id, item_id, interaction_type, time

        timestamp = df.iloc[:, 3]
        week_num = [self._to_week(t) for t in timestamp]
        max_week_num = max(week_num)
        min_week_num = min(week_num)

        f = open(join(output_data_dir, 'week_max_min_interation-counts'), 'w')
        f.write("\nMAX="+str(max_week_num))
        f.write("\nMIN="+str(min_week_num))
        f.write("\nCount interactions: Week -> [All] [Target i and all u] [Target i and target u] ([] [] [] same without impression counts)\n")

        count_in_week = {}
        for w in week_num:
            count_in_week[w] = [0]*6

        target_items = set(self.read_target_list('targetItems.csv'))
        target_users = set(self.read_target_list('targetUsers.csv'))

        rows = df.values
        newrows = []
        pos_int_pairs = set()
        neginters = []
        for row, week in zip(rows, week_num):
            user = row[0]
            item = row[1]
            if item in target_items:
                count_in_week[week][1] += 1
                if user in target_users:
                    count_in_week[week][2] += 1
            count_in_week[week][0] += 1

            if row[2] != '0':
                if item in target_items:
                    count_in_week[week][4] += 1
                    if user in target_users:
                        count_in_week[week][5] += 1
                count_in_week[week][3] += 1

            if row[2] != '0': # and week >= max_week_num - 8:
                if row[2] == '4':
                    neginters.append(row)
                else:
                    pos_int_pairs.add(row[0]+'-'+row[1])
                    newrows.append(row)

        for row in neginters:
            key = row[0] + '-' + row[1]
            if key not in pos_int_pairs:
                newrows.append(row)

        pprint(count_in_week, f)
        f.close()
        newdf = pd.DataFrame(newrows)
        self.write_data_frame(limited_interactions_file, newdf)

    def _to_week(self, timestamp):
        return datetime.fromtimestamp(int(timestamp)).isocalendar()[1]

    def read_data_frame(self, filename):
        filename = join(input_data_dir, filename)
        df = pd.read_csv(open(filename, 'r'), sep="\t", header=0, dtype=str)
        return df

    def write_data_frame(self, filename, data):
        filename = join(output_data_dir, filename)
        data.to_csv(filename, sep='\t', header=True, index=False)
        return

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
    p = LimitInteractions()
    p.create_observations()
    print ("Finished preprocessing")

if __name__ == "__main__":
    main()
