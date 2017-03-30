from data_helper import DataHelper
from datetime import datetime
import pandas as pd

i_attr = ['id','jobroles','career_level','discipline_id','industry_id','country','region',
          'experience_n_entries_class','experience_years_experience','experience_years_in_current',
          'edu_degree','edu_fieldofstudies','wtcj','premium']

i_attr_values = [[0,1,0,1,1,0,0,
                 0,0,0,
                 0,1,0,0]]

u_attr = ['id','title','career_level','discipline_id','industry_id','country','is_paid',
          'region','latitude','longitude','employment','tags','created_at']
u_attr_values = [[0, 1, 0, 1, 1, 0, 0,
                  0, 2, 2, 0, 1, 2]]


class ProcessData(object):

    def __init__(self):
        self.data_helper_instance = DataHelper(input_dir='../data_2017',
                                               op_dir='../examples/dataset',
                                               preprocessing_cache='../examples/preprocessing_cache')
        self.limited_interactions = 'target_user_interactions.csv'
        self.create_targets()

    def create_targets(self):
        print "Reading target items and target users"
        t_item_list = self.data_helper_instance.read_target_list('targetItems.csv')
        self.data_helper_instance.write_cache(t_item_list, 'target_items_list')
        self.t_items = set(t_item_list)
        self.t_users = set(self.data_helper_instance.read_target_list('targetUsers.csv'))
        self.data_helper_instance.write_cache(self.t_users, 'target_users_set')

    def create_u_files(self, en_items):
        print "Reading item (u) files"
        item_df = self.data_helper_instance.read_data_frame(self.data_helper_instance.items_file)
        df = self._restrict_by_ids(item_df, en_items)
        prem_item_set = self._restrict_by_attr(df, 6, '1')
        self.data_helper_instance.write_cache(prem_item_set, 'paid_item')
        self.data_helper_instance.write_data_frame('u.csv', df)
        self.data_helper_instance.write_data_frame('u_attr.csv', self.attr_df(u_attr, u_attr_values))

    def create_i_files(self, en_users):
        print "Reading user (i) files"
        user_df = self.data_helper_instance.read_data_frame(self.data_helper_instance.users_file)
        df = self._restrict_by_ids(user_df, en_users)
        prem_user_set = self._restrict_by_attr(df, 13, '1')
        self.data_helper_instance.write_cache(prem_user_set, 'prem_user')
        self.data_helper_instance.write_data_frame('i.csv', df)
        self.data_helper_instance.write_data_frame('i_attr.csv', self.attr_df(i_attr, i_attr_values))

    def attr_df(self, attr_header, attr_values):
        df = pd.DataFrame(attr_values)
        df.columns = attr_header
        return df

    def _restrict_by_ids(self, df, target_set):
        new_values = []
        for row in df.values:
            if row[0] in target_set:
                new_values.append(row)
        new_frame = pd.DataFrame(new_values)
        return new_frame

    def _restrict_by_attr(self, df, attr_index, attr_value):
        prem_set = []
        for row in df.values:
            if row[attr_index] == attr_value:
                prem_set.append(row[0])
        return prem_set

    def create_observations(self):

        print "Reading interactions"
        df = self.data_helper_instance.read_interactions_data_frame(self.limited_interactions)
        col_list = list(df.columns)
        # original : user_id, item_id, interaction_type, time
        col_list[0], col_list[1], col_list[2], col_list[3] = col_list[1], col_list[0], col_list[3], col_list[2]
        df = df[col_list]
        # re-ordered: item_id, user_id, time, type

        val_week_set = set([6, 5])

        encountered_items = set()
        encountered_items.update(self.t_items)
        encountered_users = set()
        encountered_users.update(self.t_users)

        print "Starting with iterations on interactions"

        rows = df.values
        te, va, tr = [], [], []
        tr_baseline_counts = {}
        tr_va_baseline_counts = {}
        true_va_int_counts = {}

        for row in rows:
            week = self._to_week(row[2])
            encountered_items.add(row[0])
            encountered_users.add(row[1])
            item = row[0]
            user = row[1]
            int_type = int(row[3])
            key_str = item +"-"+user

            if week in val_week_set:
                va.append(row)
                self._update_count(true_va_int_counts, key_str, int_type)
            else:
                tr.append(row)
                self._update_count(tr_baseline_counts, user, int_type)
            self._update_count(tr_va_baseline_counts, user, int_type)

        # print va
        te_df = pd.DataFrame(te)
        va_df = pd.DataFrame(va)
        tr_df = pd.DataFrame(tr)
        # print va_df
        self.data_helper_instance.write_data_frame('obs_tr.csv', tr_df)
        self.data_helper_instance.write_data_frame('obs_va.csv', va_df)
        self.data_helper_instance.write_data_frame('obs_te.csv', te_df)

        self.data_helper_instance.write_cache(true_va_int_counts, 'val_interaction_counts')
        self.data_helper_instance.write_cache(tr_baseline_counts, 'tr_baseline_counts')
        self.data_helper_instance.write_cache(tr_va_baseline_counts, 'tr_va_baseline_counts')

        # save validation interaction counts - for local evaluations
        return encountered_items, encountered_users

    def _to_week(self, timestamp):
        t = int(timestamp)
        return datetime.fromtimestamp(t).isocalendar()[1]

    def _update_count(self, count_dict, key_str, int_type):
        if key_str not in count_dict:
            count_dict[key_str] = [0]*6
        count_dict[key_str][int_type] += 1


def main():
    print ("Data Recsys 2017 Pre-processing:")
    p = ProcessData()
    en_items, en_users = p.create_observations()
    p.create_u_files(en_items)
    p.create_i_files(en_users)

    print ("Finished preprocessing")

if __name__ == "__main__":
    main()
