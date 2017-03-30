from os.path import join
from datetime import datetime
import pandas as pd
from pprint import pprint

target_dir = '../data_2017'
input_data_dir = "../data_2017_filtered_interactions"
output_data_dir = "../data_2017_filtered_interactions"

interactions_file = 'clean_interactions.csv'
limited_interactions_file = 'target_user_interactions.csv'

"""
Combined into clean_interactions.py currently
"""

class LimitInteractions(object):

    def create_observations(self):
        print "Reading interactions"
        df = self.read_data_frame(interactions_file)
        # original : user_id, item_id, interaction_type, time

        # target_items = set(self.read_target_list('targetItems.csv'))
        target_users = set(self.read_target_list(target_dir, 'targetUsers.csv'))

        rows = df.values
        new_rows = []

        for row in rows:
            user = row[0]
            if user in target_users:
                new_rows.append(row)

        new_df = pd.DataFrame(new_rows)
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

    def read_target_list(self, dir, filename):
        filename = join(dir, filename)
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
