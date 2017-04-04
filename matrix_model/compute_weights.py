from discretize_features import Features
from helper import load_df, load_df_list, dump_to_cache, load_from_cache
import numpy as np
from scipy.sparse import lil_matrix
import os

# count and normalize by row/col/cell/row&col
# matrix with all discrete values of features of items vs users
# count for every match, store count
# log(count+1) to normalize


def fill_feature_matrix(obs_data, f):

    mat = lil_matrix((f.item_vec_len, f.user_vec_len), dtype=np.int8)
    for obs in obs_data.values:
        item_id = obs[0]
        user_id = obs[1]
        item_vec = f.get_item_feature_vector(item_id)
        user_vec = f.get_user_feature_vector(user_id)
        for i_f_col in item_vec.nonzero()[1]:
            for u_f_col in user_vec.nonzero()[1]:
                mat[i_f_col, u_f_col] += 1
    return mat


if __name__ == '__main__':
    data_dir = "../examples/dataset"
    cache_dir = "../matrix_model_cache"
    test = False

    # todo speedup f and create smaller trial set
    if not os.path.isdir(cache_dir):
        print "Creating cache.."
        os.mkdir(cache_dir)
        f = Features(data_dir)
        dump_to_cache(f, cache_dir, 'features')
    else:
        print "Loading from cache.."
        f = load_from_cache(cache_dir, 'features')

    print "f ready.."

    if test:
        obs_df = load_df_list(data_dir, ['obs_tr.csv', 'obs_va'])
    else:
        obs_df = load_df(data_dir, 'obs_tr.csv')

    print "Rows (Item f):"+str(f.item_vec_len)+"\t Columns (User f):"+str(f.user_vec_len)

    m = fill_feature_matrix(obs_df, f)
    dump_to_cache(m, cache_dir, 'feature_matrix')
    print "Done compute weights"
