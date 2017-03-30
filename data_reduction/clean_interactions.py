from os.path import join
from datetime import datetime
import pandas as pd

input_data_dir = "../data_2017"
output_data_dir = "../data_2017_filtered_interactions"

interactions_file = 'interactions.csv'
limited_interactions_file = 'clean_interactions.csv'

"""
Removal of duplicates
Removal of impressions
Removal of negatives between pairs that have postive interactions (Retain neg only type)
"""
class LimitInteractions(object):

    def create_observations(self):
        print "Reading interactions"
        df = self.read_data_frame(interactions_file)
        print "Loaded interactions"
        print "Reading target users"
        target_users = set(self.read_target_list('targetUsers.csv'))
        print "Read targets"
        # df = df.drop_duplicates()
        # original : user_id, item_id, interaction_type, time

        # timestamp = df.iloc[:, 3]
        # week_num = [self._to_week(t) for t in timestamp]

        rows = df.values
        new_rows = []
        pos_int_pairs = set()
        neg_inters = []
        print "Starting iterations"
        for row in rows:
            user = row[0]
            if user not in target_users:
                continue
            if row[2] == '4':
                neg_inters.append(row)
            elif row[2] != '0':
                pos_int_pairs.add(row[0]+'-'+row[1])
                new_rows.append(row)

        for row in neg_inters:
            key = row[0] + '-' + row[1]
            if key not in pos_int_pairs:
                new_rows.append(row)

        new_df = pd.DataFrame(new_rows)
        new_df = new_df.drop_duplicates()
        self.write_data_frame(limited_interactions_file, new_df)

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
