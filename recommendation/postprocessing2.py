import cPickle as pickle
from os.path import join, isfile
import sys
sys.path.insert(0, '../utils')
sys.path.insert(0, '../attributes')
sys.path.insert(0, '../scoring')

def total_count_ui_pairs(x):
  c = 0
  for k, v in x.items():
    c += len(v)
  return c

def filter_out_negs(recs, neg_set_integers):
    filtered = {}
    for item, values in recs.items():
        user_list = []
        for u in values:
            if u not in neg_set_integers:
                user_list.append(u)
        filtered[item] = user_list
    return filtered


def process_rec_single_user_online_round(recs):
    user_item_ranks = {}
    for item, users in recs.items():
        rank = 0
        for user in users:
            rank += 1
            if user in user_item_ranks:
                best_rank = user_item_ranks[user][1]
                if rank < best_rank:
                    user_item_ranks[user] = [item, rank]
            else:
                user_item_ranks[user] = [item, rank]
    for item in recs.keys():
        rec_list = []
        for user in recs[item]:
            if item == user_item_ranks[user][0]:
                rec_list.append(user)
        recs[item] = rec_list
    return recs

def load_data(file_path, prep_dir='../examples/preprocessing_cache/'):
  reclogfile = 'online_raw_rec_hmf'
  filename = join(file_path, reclogfile)
  print('loading file {}'.format(filename))
  raw_rec = pickle.load(open(filename, 'rb'))
  print('\tdata type is {}, len is {}'.format(type(raw_rec), len(raw_rec)))
  print('\tlength of first element of raw_rec: {}'.format(len(raw_rec[raw_rec.keys()[0]])))  
  filename = join(prep_dir, 'neg_users_set')
  print('loading negative users from {}'.format(filename))
  neg_users = pickle.load(open(filename, 'rb')) 

  print('\tdata type is {}, length is {}'.format(type(neg_users), len(neg_users)))

  return raw_rec, neg_users



'''
load recommendation and do post processing
'''
if len(sys.argv) < 2:
  print('Error! need one prediction log file path!')
  error(-1)

daily_dir = sys.argv[1]

rec, neg_u = load_data(daily_dir)
print('before filtering: total counts {}'.format(total_count_ui_pairs(rec)))

rec_filtered = filter_out_negs(rec, neg_u)
print('after filtering:  total counts {}'.format(total_count_ui_pairs(rec_filtered)))

rec_processed = process_rec_single_user_online_round(rec_filtered)

print('after postprocess:  total counts {}'.format(total_count_ui_pairs(rec_processed)))



'''
local evalation part
'''

prep_dir='../examples/preprocessing_cache/'
raw_data='../raw_data/xing/'

if len(sys.argv) >= 3:
  gt_dir = sys.argv[2]

from evaluate import Evaluation
e = Evaluation(prep_dir, raw_data, daily_dir, gt_dir)

scores = e.local_eval_on(rec_processed)
print('scores: {}'.format(scores))


