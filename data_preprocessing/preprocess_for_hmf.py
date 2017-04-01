from data_helper import DataHelper
from datetime import datetime
import pandas as pd
from os.path import join

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
                                               preprocessing_cache='../examples/preprocessing_cache',
                                               stats_dir='../stats')
        self.stats_dir = "../stats"
        self.limited_interactions = 'target_user_interactions.csv'
        self.create_targets()

    def create_targets(self):
        print "Reading target items and target users"
        t_item_list = self.data_helper_instance.read_target_list('targetItems.csv')
        self.data_helper_instance.write_cache(t_item_list, 'target_items_list')
        self.data_helper_instance.write_int_targets(t_item_list, 'targets')
        self.t_items = set(t_item_list)
        self.data_helper_instance.write_cache(self.t_items, 'target_items_set')
        self.t_users = set(self.data_helper_instance.read_target_list('targetUsers.csv'))
        self.data_helper_instance.write_cache(self.t_users, 'target_users_set')

    def create_u_files(self, en_items):
        print "Reading item (u) files"
        item_df = self.data_helper_instance.read_data_frame(self.data_helper_instance.items_file)

        df = self._restrict_by_ids(item_df, en_items)
        prem_item_set = self._restrict_by_attr(df, 6, 1)
        self.data_helper_instance.write_cache(prem_item_set, 'paid_item_set')
        self.data_helper_instance.write_data_frame('u.csv', df)
        self.data_helper_instance.write_data_frame('u_attr.csv', self.attr_df(u_attr, u_attr_values))

    def create_i_files(self, en_users):
        print "Reading user (i) files"
        user_df = self.data_helper_instance.read_data_frame(self.data_helper_instance.users_file)
        df = self._restrict_by_ids(user_df, en_users)
        prem_user_set = self._restrict_by_attr(df, 13, 1)
        self.data_helper_instance.write_cache(prem_user_set, 'prem_user_set')
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
        new_frame = pd.DataFrame(new_values, columns=self.get_col_names(df.columns.values))
        return new_frame

    def get_col_names(self, cols):
        c_list = []
        for c in cols:
            c_list.append(c.split('.')[1])
        return c_list

    def _restrict_by_attr(self, df, attr_index, attr_value):
        prem_set = set()
        for row in df.values:
            if row[attr_index] == attr_value:
                prem_set.add(row[0])
        return prem_set

    def create_observations(self):

        print "Reading interactions"
        df = self.data_helper_instance.read_interactions_data_frame(self.limited_interactions)
        col_list = list(df.columns)
        # original : user_id, item_id, interaction_type, time
        col_list[0], col_list[1], col_list[2], col_list[3] = col_list[1], col_list[0], col_list[3], col_list[2]
        df = df[col_list]
        # re-ordered: item_id, user_id, time, type
        obs_cols = ['item_id', 'user_id', 'time', 'type']

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
        neg_users = set()
        # dict with keys as all non target items [count in va weeks, count in tr weeks] for va split sanity check
        count_per_item = {}

        pos_int_total = 0
        neg_int_total = 0

        for row in rows:
            week = self._to_week(row[2])
            encountered_items.add(row[0])
            encountered_users.add(row[1])
            item = row[0]
            user = row[1]
            int_type = row[3]
            key_str = str(item) +"-"+str(user)

            if week in val_week_set:
                if int_type != 4:
                    va.append(row)
                    pos_int_total += 1
                else:
                    neg_users.add(user)
                    neg_int_total += 1
                self._update_count(true_va_int_counts, key_str, int_type)
            else:
                if int_type != 4:
                    tr.append(row)
                    pos_int_total += 1
                else:
                    neg_users.add(user)
                    neg_int_total += 1
                self._update_count(tr_baseline_counts, user, int_type)
            self._update_count(tr_va_baseline_counts, user, int_type)

            if item not in self.t_items:
                if item not in count_per_item:
                    count_per_item[item] = [0]*2
                if week in val_week_set:
                    count_per_item[item][0] += 1
                else:
                    count_per_item[item][1] += 1

        # print va
        te_df = pd.DataFrame(te, columns=obs_cols)
        va_df = pd.DataFrame(va, columns=obs_cols)
        tr_df = pd.DataFrame(tr, columns=obs_cols)
        # print va_df
        self.data_helper_instance.write_data_frame('obs_tr.csv', tr_df)
        self.data_helper_instance.write_data_frame('obs_va.csv', va_df)
        self.data_helper_instance.write_data_frame('obs_te.csv', te_df)

        self.data_helper_instance.write_cache(true_va_int_counts, 'val_interaction_counts')
        self.data_helper_instance.write_cache(tr_baseline_counts, 'tr_baseline_counts')
        self.data_helper_instance.write_cache(tr_va_baseline_counts, 'tr_va_baseline_counts')

        # save validation interaction counts - for local evaluations
        self.data_helper_instance.write_stats(count_per_item, 'local_eval_stats', 'non-target items: val|tr\n\n')

        local_eval_item_set = self.write_local_eval_stats(count_per_item)
        print list(local_eval_item_set)
        self.data_helper_instance.write_cache(local_eval_item_set, 'target_items_local_set')
        self.data_helper_instance.write_int_targets(list(local_eval_item_set), 'targets_local')
        print list(neg_users)
        self.data_helper_instance.write_cache(neg_users, 'neg_users_set')

        print "Number of neg inter:", neg_int_total
        print "Number of pos inter:", pos_int_total

        return encountered_items, encountered_users

    def _to_week(self, timestamp):
        t = int(timestamp)
        return datetime.fromtimestamp(t).isocalendar()[1]

    def _update_count(self, count_dict, key_str, int_type):
        if key_str not in count_dict:
            count_dict[key_str] = [0]*6
        count_dict[key_str][int_type] += 1

    def write_local_eval_stats(self, count_per_item):
        f = open(join(self.stats_dir, 'local_eval_items'), 'w')
        f2 = open(join(self.stats_dir, 'local_eval_sanity_check'), 'w')
        local_eval_item_set = set()
        for item, count in count_per_item.items():
            if count[1] == 0:
                f.write(str(item) + '\t' + str(count[0]) + '\n')
                local_eval_item_set.add(item)
            else:
                f2.write(str(item) + '\t' + str(count[0]+count[1]) + '\t' + str(count[1]) + '\n')
        f.close()
        f2.close()
        return local_eval_item_set


def main():
    print ("Data Recsys 2017 Pre-processing:")
    p = ProcessData()
    en_items, en_users = p.create_observations()
    p.create_u_files(en_items)
    p.create_i_files(en_users)

    print ("Finished preprocessing")

if __name__ == "__main__":
    main()
