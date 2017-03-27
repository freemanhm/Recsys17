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
        self.data_helper_instance = DataHelper(input_dir='../data_2017_weeks',
                                               op_dir='../examples/dataset',
                                               preprocessing_cache='../examples/preprocessing_cache')
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
        df = self.data_helper_instance.read_data_frame(self.data_helper_instance.interactions_file)
        col_list = list(df.columns)
        # original : user_id, item_id, interaction_type, time
        col_list[0], col_list[1], col_list[2], col_list[3] = col_list[1], col_list[0], col_list[3], col_list[2]
        df = df[col_list]
        # re-ordered: item_id, user_id, time, type

        timestamp = df.iloc[:, 2]
        week_num = [self._to_week(t) for t in timestamp]
        max_week_num = max(week_num)

        encountered_items = set()
        encountered_items.update(self.t_items)
        encountered_users = set()
        encountered_users.update(self.t_users)

        test_week_true_data = {}
        user_inter_dist = {}

        print "Starting with iterations on interactions"

        rows = df.values

        te, va, tr = [], [], []
        for row, week in zip(rows, week_num):
            encountered_items.add(row[0])
            encountered_users.add(row[1])
            if week == max_week_num:
                te.append(row)
                # if row[0] in self.t_items and row[1] in self.t_users: #(Has none - cold start)
                keystr = row[0] + '-' + row[1]
                if keystr not in test_week_true_data:
                    test_week_true_data[keystr] = [0] * 6
                test_week_true_data[keystr][int(row[3])] += 1
            elif week == max_week_num-1:
                va.append(row)
            else:
                tr.append(row)
            if row[1] not in user_inter_dist:
                user_inter_dist[row[1]] = {}
            if week not in user_inter_dist[row[1]]:
                user_inter_dist[row[1]][week] = [0] * 6
            counts = user_inter_dist[row[1]][week]
            counts[int(row[3])] += 1

        # print va
        te_df = pd.DataFrame(te)
        va_df = pd.DataFrame(va)
        tr_df = pd.DataFrame(tr)
        # print va_df
        self.data_helper_instance.write_data_frame('obs_tr.csv', tr_df)
        self.data_helper_instance.write_data_frame('obs_va.csv', va_df)
        self.data_helper_instance.write_data_frame('obs_te.csv', te_df)
        self.data_helper_instance.write_cache(test_week_true_data, 'test_week_true_data')
        self.data_helper_instance.write_cache(user_inter_dist, 'user_inter_dist')
        return encountered_items, encountered_users

    def _to_week(self, timestamp):
        t = int(timestamp)
        return datetime.fromtimestamp(t).isocalendar()[1]


def main():
    print ("Data Recsys 2017 Pre-processing:")
    p = ProcessData()
    en_items, en_users = p.create_observations()
    p.create_u_files(en_items)
    p.create_i_files(en_users)

    print ("Finished preprocessing")

if __name__ == "__main__":
    main()
