from comb_attribute import HET, MIX
import attribute
import cPickle as pickle
import sys, os

sys.path.insert(0, '../utils')
from load_data import load_raw_data, load_raw_data2, load_raw_data3


def read_data(raw_data_dir='../raw_data/data/', data_dir='../cache/data/',
              combine_att='mix', logits_size_tr='10000',
              thresh=2, use_user_feature=True, use_item_feature=True, no_user_id=False,
              no_item_id=False, test=False, mylog=None):

    if not mylog:
        def mylog(val):
            print(val)

    data_filename = os.path.join(data_dir, 'data')
    if os.path.isfile(data_filename):
        mylog("data file {} exists! loading cached data. \nCaution: change cached data dir (--data_dir) if new data (or new preprocessing) is used.".format(data_filename))
        (data_tr, data_va, u_attr, i_attr, item_ind2logit_ind,
         logit_ind2item_ind, user_index, item_index) = pickle.load(
            open(data_filename, 'rb'))
        # u_attr.overview(mylog)
        # i_attr.overview(mylog)

    else:
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        _submit = 1 if test else 0
        (users, items, data_tr, data_va, user_features, item_features,
         user_index, item_index) = load_raw_data(data_dir=raw_data_dir, _submit=_submit)
        if not use_user_feature:
            n = len(users)
            users = users[:, 0].reshape(n, 1)
            user_features = ([user_features[0][0]], [user_features[1][0]])
        if not use_item_feature:
            m = len(items)
            items = items[:, 0].reshape(m, 1)
            item_features = ([item_features[0][0]], [item_features[1][0]])

        if no_user_id:
            users[:, 0] = 0

        if no_item_id:
            items[:, 0] = 0

        if combine_att == 'het':
            het = HET(data_dir=data_dir, logits_size_tr=logits_size_tr, threshold=thresh)
            u_attr, i_attr, item_ind2logit_ind, logit_ind2item_ind = het.get_attributes(
                users, items, data_tr, user_features, item_features)
        elif combine_att == 'mix':
            mix = MIX(data_dir=data_dir, logits_size_tr=logits_size_tr,
                      threshold=thresh)
            users2, items2, user_features, item_features = mix.mix_attr(users, items,
                                                                        user_features, item_features)
            (u_attr, i_attr, item_ind2logit_ind,
             logit_ind2item_ind) = mix.get_attributes(users2, items2, data_tr,
                                                      user_features, item_features)

        mylog("saving data format to data directory")
        from preprocess import pickle_save
        pickle_save((data_tr, data_va, u_attr, i_attr,
                     item_ind2logit_ind, logit_ind2item_ind, user_index, item_index), data_filename)

    mylog('length of item_ind2logit_ind: {}'.format(len(item_ind2logit_ind)))

    # if FLAGS.dataset in ['ml', 'yelp']:
    #   mylog('disabling the lstm-rec fake feature')
    #   u_attr.num_features_cat = 1

    return (data_tr, data_va, u_attr, i_attr, item_ind2logit_ind,
            logit_ind2item_ind, user_index, item_index)

'''
when new set of users and items are used in the testing phase
'''
def read_data2(raw_data_dir='../raw_data/data/', data_dir='../cache/data/',
              combine_att='mix', logits_size_tr='10000',
              thresh=2, use_user_feature=True, use_item_feature=True, 
              no_user_id=False, no_item_id=False, test=False, mylog=None,
              raw_data_daily='../raw_data_daily/', reverse=True):

    if not mylog:
        def mylog(val):
            print(val)

    data_filename = os.path.join(data_dir, 'data')
    if not os.path.isfile(data_filename):
        mylog("data file not exists! error!")
        exit(-1)
        
    else:
        if reverse: 
            (users, items, user_features, item_features, user_index, 
                item_index) = load_raw_data2(
                data_dir=raw_data_dir, data_daily_dir=raw_data_daily)
            target_items_list = list(pickle.load(open(os.path.join(raw_data_daily, 'daily_target_users_set'))))
        else:
            (users, items, user_features, item_features, user_index, 
                item_index) = load_raw_data3(
                data_dir=raw_data_dir, data_daily_dir=raw_data_daily)
            target_user_set = set(pickle.load(open(os.path.join(raw_data_daily, 'daily_target_users_set'))))
            import numpy as np
            users2 = np.copy(users)
            count = 0
            for j in range(len(users)):
                if users[j,0] in target_user_set:
                    users2[count, :] = users[j, :]
                    count += 1
            users2 = users2[:count, :]

            target_items_list = list(items[:,0])
        if not use_user_feature:
            n = len(users)
            users = users[:, 0].reshape(n, 1)
            user_features = ([user_features[0][0]], [user_features[1][0]])

        if no_user_id:
            users[:, 0] = 0

        if no_item_id:
            items[:, 0] = 0

        item_inds = [item_index[v] for v in target_items_list]
        if combine_att == 'het':
            het = HET(data_dir=data_dir, logits_size_tr=logits_size_tr, threshold=thresh)
            u_attr, i_attr, item_ind2logit_ind, logit_ind2item_ind = het.get_attributes2(
                users, items, user_features, item_features, item_inds)

        elif combine_att == 'mix':
            mix = MIX(data_dir=data_dir, logits_size_tr=logits_size_tr,
                      threshold=thresh)
            users2, items2, user_features, item_features = mix.mix_attr(users, items,
                                                                        user_features, item_features)
            (u_attr, i_attr, item_ind2logit_ind,
             logit_ind2item_ind) = mix.get_attributes(users2, items2, data_tr,
                                                      user_features, item_features)


    mylog('length of item_ind2logit_ind: {}'.format(len(item_ind2logit_ind)))
    
    return u_attr, i_attr, item_ind2logit_ind, logit_ind2item_ind, user_index, item_index
    
