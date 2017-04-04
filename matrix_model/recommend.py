# for every target item and target user, find the cells to consider and sum up the weights to compute score

from discretize_features import Features
from helper import load_df, load_df_list, dump_to_cache, load_from_cache
import numpy as np
from scipy.sparse import lil_matrix
import os
import operator
from scoring import Evaluation

# count and normalize by row/col/cell/row&col
# matrix with all discrete values of features of items vs users
# count for every match, store count
# log(count+1) to normalize


def recommend(item_id, mat, t_users_list, f):
    user_scores = {}
    item_vec = f.get_item_feature_vector(item_id)
    for user_id in t_users_list:
        score = 0
        user_vec = f.get_user_feature_vector(user_id)
        for i_f_col in item_vec.nonzero()[1]:
            for u_f_col in user_vec.nonzero()[1]:
                score += mat[i_f_col, u_f_col]
        user_scores[user_id] = score
    ranked = get_rank_list(user_scores)
    return ranked


def get_rank_list(s):
    ranked_list = sorted(s.items(), key=operator.itemgetter(1), reverse=True)
    ranked_list = ranked_list[0:100]
    rank = []
    for r in ranked_list:
        rank.append(r[0])
    return rank

if __name__ == '__main__':
    data_dir = "../examples/dataset"
    cache_dir = "../matrix_model_cache"
    test = False

    # todo speedup f and create smaller trial set

    print "Loading from cache.."
    # separate out va matr and te matr
    mat = load_from_cache(cache_dir, 'feature_matrix')
    f = load_from_cache(cache_dir, 'features')

    print "matrix ready.."

    R = {}
    if test:
        t_items_list = [260, 300]
    else:
        t_items_list = [260, 300]

    t_users_list = [360]

    for t_item in t_items_list:
        R[t_item] = recommend(t_item, mat, t_users_list, f)

    print R
    # todo save and evaluate etc, target list loading and test Flag setting, including neg filtered R

    print "Done with recommendations"

