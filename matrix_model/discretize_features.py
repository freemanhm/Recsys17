from helper import load_df
import numpy as np
from scipy.sparse import lil_matrix

# todo id and is_payed vectorization issue

# dict of feature type and all possible values it can take
# all items and target users dataset

"""
Current feature matrix - using pos obs only, no differentiation between interaction types
(using target users and all items)
"""

user_attr = ['id','jobroles','career_level','discipline_id','industry_id','country','region',
          'experience_n_entries_class','experience_years_experience','experience_years_in_current',
          'edu_degree','edu_fieldofstudies','wtcj','premium']

user_attr_types = [2,1,0,1,1,0,0,
                  0,0,0,
                  0,1,0,0]

item_attr = ['id','title','career_level','discipline_id','industry_id','country','is_payed',
          'region','latitude','longitude','employment','tags','created_at']

item_attr_types = [2, 1, 0, 1, 1, 0, 0,
                  0, 2, 2, 0, 1, 2]


class Features(object):

    def __init__(self, data_dir):
        print "Loading data.."
        item_df = load_df(data_dir, 'u.csv')
        user_df = load_df(data_dir, 'i.csv')
        print "Done loading.."
        # f_map stores feature name as key and set of its values as value
        item_f_map = self.init_maps(item_df.columns)
        user_f_map = self.init_maps(user_df.columns)
        print "Item Features:", item_f_map.keys()
        print "User Features:", user_f_map.keys()
        # f_type_map stores feature name as key and its type as value -
        # categorical (0), multihot (1), to_ignore (2)
        self.item_f_type_map = self.init_type_maps(item_attr, item_attr_types)
        self.user_f_type_map = self.init_type_maps(user_attr, user_attr_types)
        print "Discretizing.."
        self.discretize(item_df, item_f_map, self.item_f_type_map)
        self.discretize(user_df, user_f_map, self.user_f_type_map)
        self.item_f_index = self.build_discrete_f_index(item_f_map)
        self.user_f_index = self.build_discrete_f_index(user_f_map)
        self.item_vec_len = len(self.item_f_index.keys())
        self.user_vec_len = len(self.user_f_index.keys())
        print "Indexing items and users by id"
        self.item_id_index = self.build_indices(item_df)
        self.user_id_index = self.build_indices(user_df)
        print "Vectorizing items"
        self.item_vector_mat = self.build_f_vectors_map(item_df, self.item_id_index, self.item_f_type_map, self.item_f_index, self.item_vec_len)
        print "Vectorizing users"
        self.user_vector_mat = self.build_f_vectors_map(user_df, self.user_id_index, self.user_f_type_map, self.user_f_index, self.user_vec_len)
        print "Finished feature creations"

    def build_indices(self, entity_df):
        ind = {}
        counter = 0
        id_col = entity_df['id']
        for idv in id_col:
            ind[idv] = counter
            counter += 1
        return ind

    def build_f_vectors_map(self, entity_df, id_index, f_type_map, f_index, vec_len):
        f_vectors_mat = lil_matrix((len(entity_df.values), vec_len), dtype=np.int8)
        id_col = entity_df['id']
        for f_name, f_type in f_type_map.items():
            print f_name
            if f_type == 2:
                continue
            col = entity_df[f_name]
            for id, value in zip(id_col, col):
                vec_row = id_index[id]
                if f_type == 1:
                    v_list = str(value).split(",")
                else:
                    v_list = [value]
                for v in v_list:
                    key = str(f_name) + "-" + str(v)
                    vec_off = f_index[key]
                f_vectors_mat[vec_row, vec_off] = 1
        return f_vectors_mat

    def build_discrete_f_index(self, f_map):
        counter = 0
        f_index = {}
        for k, v_set in f_map.items():
            if len(v_set) > 0:
                for v in v_set:
                    key_str = str(k) + '-' + str(v)
                    f_index[key_str] = counter
                    counter += 1
        return f_index

    def init_maps(self, df_header):
        f_map = {}
        for c in df_header:
            f_map[c] = set()
        return f_map

    def init_type_maps(self, attr, attr_types):
        attr_map = {}
        for a, t in zip(attr, attr_types):
            attr_map[a] = t
        return attr_map

    def discretize(self, entity, f_map, types_map):
        for name, val in f_map.items():
            if types_map[name] == 2:
                continue
            df_col = entity[name]
            for v in df_col:
                if types_map[name] == 1:
                    str_v = str(v)
                    v_list = str_v.split(",")
                    val.update(set(v_list))
                else:
                    val.add(v)
        return

    def get_item_feature_vector(self, item_id):
        return self.item_vector_mat.getrow(self.item_id_index[item_id])
        # [self.item_id_index[item_id], :]

    def get_user_feature_vector(self, user_id):
        return self.user_vector_mat.getrow(self.user_id_index[user_id])
        # [self.user_id_index[user_id], :]
