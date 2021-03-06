from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math, os, sys
import random, time
import logging
import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf
sys.path.insert(0, '../utils')
sys.path.insert(0, '../attributes')
sys.path.insert(0, '../scoring')

import pickle

from input_attribute import read_data, read_data2
from weight import Weights
from prepare_train import positive_items, item_frequency, sample_items

# datasets, paths, and preprocessing
tf.app.flags.DEFINE_string("dataset", "xing", ".")
tf.app.flags.DEFINE_string("raw_data", "../raw_data", "input data directory")
tf.app.flags.DEFINE_string("prep_dir", "../examples/preprocessing_cache", "Preprocessing cache directory used in evaluation.")
tf.app.flags.DEFINE_string("data_dir", "./cache0", "Cached data directory")
tf.app.flags.DEFINE_string("train_dir", "./tmp", "Training directory.")
tf.app.flags.DEFINE_boolean("test", False, "Test on test splits")
tf.app.flags.DEFINE_string("combine_att", 'mix', "method to combine attributes: het or mix")
tf.app.flags.DEFINE_boolean("use_user_feature", True, "RT")
tf.app.flags.DEFINE_boolean("use_item_feature", True, "RT")
tf.app.flags.DEFINE_integer("user_vocab_size", 150000, "User vocabulary size.")
tf.app.flags.DEFINE_integer("item_vocab_size", 50000, "Item vocabulary size.")
tf.app.flags.DEFINE_integer("item_vocab_min_thresh", 2, "filter inactive tokens.")

# tuning hypers
tf.app.flags.DEFINE_string("loss", 'ce', "loss function: ce, warp, (mw, mce, bpr)")
tf.app.flags.DEFINE_float("learning_rate", 0.1, "Learning rate.")
tf.app.flags.DEFINE_float("keep_prob", 0.5, "dropout rate.")
tf.app.flags.DEFINE_float("learning_rate_decay_factor", 1.0,
                          "Learning rate decays by this much.")
tf.app.flags.DEFINE_integer("batch_size", 64,
                            "Batch size to use during training.")
tf.app.flags.DEFINE_integer("size", 20, "Size of each embedding.")
tf.app.flags.DEFINE_integer("patience", 20,
                            "exit if the model can't improve for $patience evals")
tf.app.flags.DEFINE_integer("n_epoch", 1000, "How many epochs to train.")
tf.app.flags.DEFINE_integer("steps_per_checkpoint", 4000,
                            "How many training steps to do per checkpoint.")

# to recommend
tf.app.flags.DEFINE_boolean("recommend", False,
                            "Set to True for recommend items.")
tf.app.flags.DEFINE_string("saverec", True, "")
tf.app.flags.DEFINE_integer("top_N_items", 100,
                            "number of items output")
tf.app.flags.DEFINE_boolean("recommend_new", True,
                            "Set to True for recommend new items that were not used to train.")

# evaluation
tf.app.flags.DEFINE_boolean("true_targets", False,
                            "Set to True for recommend true targets on tr model.")
tf.app.flags.DEFINE_string("raw_data_daily", "../raw_data_daily/2017-05-05",
                            "Set to point to daily raw data.")
tf.app.flags.DEFINE_boolean("new_users", False, 'true for new users')
tf.app.flags.DEFINE_boolean("reverse", True, 'whether to reverse users and items')

# attribute model variants
tf.app.flags.DEFINE_boolean("no_user_id", False, "use user id or not")
tf.app.flags.DEFINE_boolean("no_item_id", False, "use item id or not")
tf.app.flags.DEFINE_boolean("weighted_loss", False, "use weighted_loss or not")


# nonlinear
tf.app.flags.DEFINE_string("nonlinear", 'linear', "nonlinear activation")
tf.app.flags.DEFINE_integer("hidden_size", 500, "when nonlinear proj used")
tf.app.flags.DEFINE_integer("num_layers", 1, "Number of layers in the model.")

# algorithms with sampling
tf.app.flags.DEFINE_float("power", 0.5, "related to sampling rate.")
tf.app.flags.DEFINE_integer("n_resample", 50, "iterations before resample.")
tf.app.flags.DEFINE_integer("n_sampled", 1024, "sampled softmax/warp loss.")

tf.app.flags.DEFINE_string("sample_type", 'random', "random, sweep, permute")
tf.app.flags.DEFINE_float("user_sample", 1.0, "user sample rate.")

#
tf.app.flags.DEFINE_integer("gpu", -1, "gpu card number")
tf.app.flags.DEFINE_boolean("profile", False, "False = no profile, True = profile")
tf.app.flags.DEFINE_boolean("device_log", False,
                            "Set to True for logging device usages.")
tf.app.flags.DEFINE_boolean("eval", True,
                            "Set to True for evaluation.")
tf.app.flags.DEFINE_boolean("use_more_train", False,
                            "Set true if use non-appearred items to train.")
tf.app.flags.DEFINE_string("model_option", 'loss',
                           "model to evaluation")

# tf.app.flags.DEFINE_integer("max_train_data_size", 0,
#                             "Limit on the size of training data (0: no limit).")
# Xing related
# tf.app.flags.DEFINE_integer("ta", 0, "target_active")



FLAGS = tf.app.flags.FLAGS

def mylog(msg):
    print(msg)
    logging.info(msg)
    return

def create_model(session, u_attributes=None, i_attributes=None,
                 item_ind2logit_ind=None, logit_ind2item_ind=None,
                 loss = FLAGS.loss, logit_size_test=None, ind_item = None,
                 u_attributes2=None, i_attributes2=None,
                 logit_ind2item_ind_target=None):
    gpu = None if FLAGS.gpu == -1 else FLAGS.gpu
    n_sampled = FLAGS.n_sampled if FLAGS.loss in ['mw', 'mce'] else None
    import hmf_model
    model = hmf_model.LatentProductModel(FLAGS.user_vocab_size,
                                         FLAGS.item_vocab_size, FLAGS.size, FLAGS.num_layers,
                                         FLAGS.batch_size, FLAGS.learning_rate,
                                         FLAGS.learning_rate_decay_factor, u_attributes, i_attributes,
                                         item_ind2logit_ind, logit_ind2item_ind, loss_function = loss, GPU=gpu,
                                         logit_size_test=logit_size_test, nonlinear=FLAGS.nonlinear,
                                         dropout=FLAGS.keep_prob, n_sampled=n_sampled, indices_item=ind_item,
                                         top_N_items=FLAGS.top_N_items, hidden_size=FLAGS.hidden_size,
                                         u_attributes2=u_attributes2, i_attributes2=i_attributes2,
                                         logit_ind2item_ind_target=logit_ind2item_ind_target,
                                         true_targets=FLAGS.true_targets, new_users=FLAGS.new_users)

    if not os.path.isdir(FLAGS.train_dir):
        os.mkdir(FLAGS.train_dir)
    ckpt = tf.train.get_checkpoint_state(FLAGS.train_dir)

    if ckpt:
        print("Reading model parameters from %s" % ckpt.model_checkpoint_path)
        logging.info("Reading model parameters from %s" % ckpt.model_checkpoint_path)
        model.saver.restore(session, ckpt.model_checkpoint_path)
    else:
        print("Created model with fresh parameters.")
        logging.info("Created model with fresh parameters.")
        # session.run(tf.global_variables_initializer())
        session.run(tf.global_variables_initializer())
    return model

def train(raw_data=FLAGS.raw_data, train_dir=FLAGS.train_dir, mylog=mylog,
          data_dir=FLAGS.data_dir, combine_att=FLAGS.combine_att, test=FLAGS.test,
          logits_size_tr=FLAGS.item_vocab_size, thresh=FLAGS.item_vocab_min_thresh,
          use_user_feature=FLAGS.use_user_feature,
          use_item_feature=FLAGS.use_item_feature,
          no_user_id=FLAGS.no_user_id, no_item_id=FLAGS.no_item_id,
          batch_size=FLAGS.batch_size, steps_per_checkpoint=FLAGS.steps_per_checkpoint,
          loss_func=FLAGS.loss, max_patience=FLAGS.patience, go_test=FLAGS.test,
          max_epoch=FLAGS.n_epoch, sample_type=FLAGS.sample_type, power=FLAGS.power,
          use_more_train=FLAGS.use_more_train, profile=FLAGS.profile,
          device_log=FLAGS.device_log):
    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True,
                                          log_device_placement=device_log)) as sess:
        run_options = None
        run_metadata = None
        if profile:
            # in order to profile
            from tensorflow.python.client import timeline
            run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
            run_metadata = tf.RunMetadata()
            steps_per_checkpoint = 30

        mylog("reading data")
        (data_tr, data_va, u_attributes, i_attributes,item_ind2logit_ind,
         logit_ind2item_ind, user_index, item_index) = read_data(
            raw_data_dir=raw_data,
            data_dir=data_dir,
            combine_att=combine_att,
            logits_size_tr=logits_size_tr,
            thresh=thresh,
            use_user_feature=use_user_feature,
            use_item_feature=use_item_feature,
            no_user_id=no_user_id,
            no_item_id=no_item_id,
            test=test,
            mylog=mylog)

        mylog("train/dev size: %d/%d" %(len(data_tr),len(data_va)))

        '''
        remove some rare items in both train and valid set
        this helps make train/valid set distribution similar
        to each other
        '''
        mylog("original train/dev size: %d/%d" %(len(data_tr),len(data_va)))
        data_tr = [p for p in data_tr if (p[1] in item_ind2logit_ind)]
        data_va = [p for p in data_va if (p[1] in item_ind2logit_ind)]
        mylog("new train/dev size: %d/%d" %(len(data_tr),len(data_va)))

        item_pop, p_item = item_frequency(data_tr, power)

        if use_more_train:
            item_population = range(len(item_ind2logit_ind))
        else:
            item_population = item_pop

        model = create_model(sess, u_attributes, i_attributes, item_ind2logit_ind,
                             logit_ind2item_ind, loss=loss_func, ind_item=item_population)

        pos_item_list, pos_item_list_val = None, None
        if loss_func in ['warp', 'mw', 'bbpr']:
            pos_item_list, pos_item_list_val = positive_items(data_tr, data_va)
            model.prepare_warp(pos_item_list, pos_item_list_val)

        mylog('started training')
        step_time, loss, current_step, auc = 0.0, 0.0, 0, 0.0

        repeat = 5 if loss_func.startswith('bpr') else 1
        patience = max_patience

        if os.path.isfile(os.path.join(train_dir, 'auc_train.npy')):
            auc_train = list(np.load(os.path.join(train_dir, 'auc_train.npy')))
            auc_dev = list(np.load(os.path.join(train_dir, 'auc_dev.npy')))
            previous_losses = list(np.load(os.path.join(train_dir,
                                                        'loss_train.npy')))
            losses_dev = list(np.load(os.path.join(train_dir, 'loss_dev.npy')))
            best_auc = max(auc_dev)
            best_loss = min(losses_dev)
        else:
            previous_losses, auc_train, auc_dev, losses_dev = [], [], [], []
            best_auc, best_loss = -1, 1000000

        item_sampled, item_sampled_id2idx = None, None

        if sample_type == 'random':
            get_next_batch = model.get_batch
        elif sample_type == 'permute':
            get_next_batch = model.get_permuted_batch
        else:
            print('not implemented!')
            exit()

        if FLAGS.weighted_loss:
            wei = Weights(user_index, item_index)


        train_total_size = float(len(data_tr))
        n_epoch = max_epoch
        steps_per_epoch = int(1.0 * train_total_size / batch_size)
        total_steps = steps_per_epoch * n_epoch

        mylog("Train:")
        mylog("total: {}".format(train_total_size))
        mylog("Steps_per_epoch: {}".format(steps_per_epoch))
        mylog("Total_steps:{}".format(total_steps))
        mylog("Dev:")
        mylog("total: {}".format(len(data_va)))

        mylog("\n\ntraining start!")
        while True:
            ranndom_number_01 = np.random.random_sample()
            start_time = time.time()
            (user_input, item_input, neg_item_input, types) = get_next_batch(data_tr)
            if FLAGS.weighted_loss:
                weights = wei.get_loss_weight(user_input, item_input, types)
            else:
                weights = None

            if loss_func in ['mw', 'mce'] and current_step % FLAGS.n_resample == 0:
                item_sampled, item_sampled_id2idx = sample_items(item_population,
                                                                 FLAGS.n_sampled, p_item)
            else:
                item_sampled = None

            step_loss = model.step(sess, user_input, item_input,
                                   neg_item_input, item_sampled, item_sampled_id2idx, loss=loss_func,
                                   weights=weights, run_op=run_options, run_meta=run_metadata)
            # if weights is not None:
            #   step_loss = step_loss * batch_size / sum(weights)

            step_time += (time.time() - start_time) / steps_per_checkpoint
            loss += step_loss / steps_per_checkpoint
            current_step += 1
            if current_step > total_steps:
                mylog("Training reaches maximum steps. Terminating...")
                break

            if current_step % steps_per_checkpoint == 0:

                if loss_func in ['ce', 'mce']:
                    perplexity = math.exp(loss) if loss < 300 else float('inf')
                    mylog("global step %d learning rate %.4f step-time %.4f perplexity %.2f" % (model.global_step.eval(), model.learning_rate.eval(), step_time, perplexity))
                else:
                    mylog("global step %d learning rate %.4f step-time %.4f loss %.3f" % (model.global_step.eval(), model.learning_rate.eval(), step_time, loss))
                if profile:
                    # Create the Timeline object, and write it to a json
                    tl = timeline.Timeline(run_metadata.step_stats)
                    ctf = tl.generate_chrome_trace_format()
                    with open('timeline.json', 'w') as f:
                        f.write(ctf)
                    exit()

                # Decrease learning rate if no improvement was seen over last 3 times.
                if len(previous_losses) > 2 and loss > max(previous_losses[-3:]):
                    sess.run(model.learning_rate_decay_op)
                previous_losses.append(loss)
                auc_train.append(auc)

                # Reset timer and loss.
                step_time, loss, auc = 0.0, 0.0, 0.0

                if not FLAGS.eval:
                    continue


                # Run evals on development set and print their loss.
                l_va = len(data_va)
                eval_loss, eval_auc = 0.0, 0.0
                count_va = 0
                start_time = time.time()
                for idx_s in range(0, l_va, batch_size):
                    idx_e = idx_s + batch_size
                    if idx_e > l_va:
                        break
                    lt = data_va[idx_s:idx_e]
                    user_va = [x[0] for x in lt]
                    item_va = [x[1] for x in lt]
                    if len(lt[0]) > 3:
                        type_va = [x[3] for x in lt]

                    if FLAGS.weighted_loss:
                        weights = wei.get_loss_weight(user_va, item_va, type_va)
                    else:
                        weights = None

                    for _ in range(repeat):
                        item_va_neg = None
                        the_loss = 'warp' if loss_func == 'mw' else loss_func
                        eval_loss0 = model.step(sess, user_va, item_va, item_va_neg,
                                                None, None, forward_only=True,
                                                weights=weights,
                                                loss=the_loss)
                        # if weights is not None:
                        #   eval_loss0 = eval_loss0 * len(weights) / sum(weights)

                        eval_loss += eval_loss0
                        count_va += 1
                eval_loss /= count_va
                eval_auc /= count_va
                step_time = (time.time() - start_time) / count_va
                if loss_func in ['ce', 'mce']:
                    eval_ppx = math.exp(eval_loss) if eval_loss < 300 else float('inf')
                    mylog("  dev: perplexity %.2f eval_auc %.4f step-time %.4f" % (
                        eval_ppx, eval_auc, step_time))
                else:
                    mylog("  dev: loss %.3f eval_auc %.4f step-time %.4f" % (eval_loss,
                                                                             eval_auc, step_time))
                sys.stdout.flush()

                if eval_loss < best_loss and not go_test:
                    best_loss = eval_loss
                    patience = max_patience
                    checkpoint_path = os.path.join(train_dir, "best.ckpt")
                    mylog('Saving best model...')
                    model.saver.save(sess, checkpoint_path,
                                     global_step=0, write_meta_graph = False)

                if go_test:
                    checkpoint_path = os.path.join(train_dir, "best.ckpt")
                    mylog('Saving best model...')
                    model.saver.save(sess, checkpoint_path,
                                     global_step=0, write_meta_graph = False)

                if eval_loss > best_loss:
                    patience -= 1

                auc_dev.append(eval_auc)
                losses_dev.append(eval_loss)

                if patience < 0 and not go_test:
                    mylog("no improvement for too long.. terminating..")
                    mylog("best loss %.4f" % best_loss)
                    sys.stdout.flush()
                    break
    return

def recommend(target_uids=[], raw_data=FLAGS.raw_data, data_dir=FLAGS.data_dir,
              combine_att=FLAGS.combine_att, logits_size_tr=FLAGS.item_vocab_size,
              item_vocab_min_thresh=FLAGS.item_vocab_min_thresh, loss=FLAGS.loss,
              top_n=FLAGS.top_N_items, test=FLAGS.test, mylog=mylog,
              use_user_feature=FLAGS.use_user_feature,
              use_item_feature=FLAGS.use_item_feature,
              batch_size=FLAGS.batch_size, device_log=FLAGS.device_log):

    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True,
                                          log_device_placement=device_log)) as sess:
        mylog("reading data")
        (_, _, u_attributes, i_attributes, item_ind2logit_ind,
         logit_ind2item_ind, user_index, item_index) = read_data(
            raw_data_dir=raw_data,
            data_dir=data_dir,
            combine_att=combine_att,
            logits_size_tr=logits_size_tr,
            thresh=item_vocab_min_thresh,
            use_user_feature=use_user_feature,
            use_item_feature=use_item_feature,
            test=test,
            mylog=mylog)

        # TODO: check if item_index2 is identical to item_index
        (u_attributes2, i_attributes2, item_ind2logit_ind2,
         logit_ind2item_ind2, new_user_index, item_index2) = read_data2(
            raw_data_dir=raw_data,
            data_dir=data_dir,
            combine_att=combine_att,
            logits_size_tr=logits_size_tr,
            thresh=item_vocab_min_thresh,
            use_user_feature=use_user_feature,
            use_item_feature=use_item_feature,
            test=test,
            mylog=mylog, raw_data_daily=FLAGS.raw_data_daily, reverse=FLAGS.reverse)

        model = create_model(sess, u_attributes, i_attributes, item_ind2logit_ind,
                             logit_ind2item_ind, loss=loss, ind_item=None, 
                             u_attributes2=u_attributes2, i_attributes2=i_attributes2,
                             logit_ind2item_ind_target=logit_ind2item_ind2)

        Uinds = [new_user_index[v] for v in target_uids]

        N = len(Uinds)
        mylog("%d target users to recommend" % N)
        rec = np.zeros((N, top_n), dtype=int)

        count = 0
        time_start = time.time()
        for idx_s in range(0, N, batch_size):
            count += 1
            if count % 100 == 0:
                mylog("idx: %d, c: %d" % (idx_s, count))

            idx_e = idx_s + batch_size
            if idx_e <= N:
                users = Uinds[idx_s: idx_e]
                recs = model.step(sess, users, None, None, forward_only=True,
                                  recommend=True, 
                                  new_users=FLAGS.new_users)
                rec[idx_s:idx_e, :] = recs
            else:
                users = range(idx_s, N) + [0] * (idx_e - N)
                users = [Uinds[t] for t in users]
                recs = model.step(sess, users, None, None, forward_only=True,
                                  recommend=True,
                                  new_users=FLAGS.new_users)
                idx_e = N
                rec[idx_s:idx_e, :] = recs[:(idx_e-idx_s),:]

        time_end = time.time()
        mylog("Time used %.1f" % (time_end - time_start))

        # transform result to a dictionary
        # R[user_id] = [item_id1, item_id2, ...]

        if FLAGS.true_targets and FLAGS.new_users:
            item_index_reqd = item_index2
            logit_ind2item_ind_reqd = logit_ind2item_ind2
        else:
            item_index_reqd = item_index
            logit_ind2item_ind_reqd = logit_ind2item_ind

        ind2id = {}
        for iid in item_index_reqd:
            uind = item_index_reqd[iid]
            assert(uind not in ind2id)
            ind2id[uind] = iid
        R = {}
        for i in xrange(N):
            uid = target_uids[i]
            R[uid] = [ind2id[logit_ind2item_ind_reqd[v]] for v in list(rec[i, :])]

    return R

def compute_scores(raw_data_dir=FLAGS.raw_data, data_dir=FLAGS.data_dir,
                   dataset=FLAGS.dataset, save_recommendation=FLAGS.saverec,
                   train_dir=FLAGS.train_dir, test=FLAGS.test, true_targets=FLAGS.true_targets):

    from evaluate import Evaluation
    from post_processing import filter_out_negs
    e = Evaluation(FLAGS.prep_dir, raw_data_dir, FLAGS.raw_data_daily)

    daily_raw_data_dir=FLAGS.raw_data_daily

    if true_targets:
        if FLAGS.reverse:
            user_file_name = os.path.join(daily_raw_data_dir, 'daily_target_items_list')
        else:
            user_file_name = os.path.join(daily_raw_data_dir, 'daily_target_users_set')
    else:
        if FLAGS.reverse:
            user_file_name = os.path.join(raw_data_dir, 'daily_target_local_list')
        else:
            user_file_name = os.path.join(raw_data_dir, 'target_users_set')
            
        
    if FLAGS.new_users:
        if FLAGS.reverse:
            item_file_name = os.path.join(daily_raw_data_dir, 'daily_target_users_set')
        else:
            item_file_name = os.path.join(daily_raw_data_dir, 'daily_target_items_list')
    else:
        if FLAGS.reverse:
            item_file_name = os.path.join(raw_data_dir, 'target_users_set')
        else:
            item_file_name = os.path.join(raw_data_dir, 'daily_target_local_list')

#     if FLAGS.reverse:
#         target_users = pickle.load(open(user_file_name, 'rb'))
#         t_ids = pickle.load(open(item_file_name, 'rb'))
#     else:
    target_users = pickle.load(open(item_file_name, 'rb'))
    t_ids = pickle.load(open(user_file_name, 'rb'))
        
    #t_ids = pickle.load(open(item_file_name, 'rb'))
    t_ids = list(t_ids)
    target_users = set(target_users)
    print(FLAGS.new_users, FLAGS.true_targets)
    print(len(t_ids),len(target_users))
    if FLAGS.reverse:
        suf = ''
    else:
        suf = '_rev'

    if true_targets and FLAGS.new_users:
        reclogfile = 'online_raw_rec_hmf' + suf
           
    elif not FLAGS.true_targets and not FLAGS.new_users:
        reclogfile = 'local_raw_rec_hmf' + suf

#     if true_targets:
#         reclogfile = "online_raw_rec_hmf"
#         t_ids = pickle.load(open(os.path.join(daily_raw_data_dir, 'daily_target_items_list'), 'rb'))
#         target_users = pickle.load(open(os.path.join(daily_raw_data_dir, 'daily_target_users_set'), 'rb'))
#     else:
#         reclogfile = "local_raw_rec_hmf"
#         t_ids = pickle.load(open(os.path.join(raw_data_dir, 'target_items_local_list'), 'rb'))
#         target_users = pickle.load(open(os.path.join(raw_data_dir, 'target_users_set'), 'rb'))

    R = recommend(t_ids, data_dir=data_dir)
    # rec_save_path = os.path.join(daily_raw_data_dir, reclogfile)
    # R = pickle.load(open(rec_save_path, 'rb'))

    if save_recommendation:
        rec_save_path = os.path.join(daily_raw_data_dir, reclogfile)
        pickle.dump(R, open(rec_save_path, 'wb'))

    # R = filter_recs(R, set(target_users))

    if not FLAGS.reverse:
        print('no post processing is needed. return')
        return
    neg_users_set = pickle.load(open(os.path.join(FLAGS.prep_dir, 'neg_users_set')+suf, 'rb'))

    # e.online_solutions_write(R, daily_raw_data_dir, 'basic_rec_done')
    R_filtered = filter_out_negs(R, neg_users_set)
    # e.online_solutions_write(R_filtered, daily_raw_data_dir, 'fitered_out_negs_done')

    if true_targets:
        # R = process_rec_single_user_online_round(R)
        # e.online_solutions_write(R, daily_raw_data_dir, 'online_submission.txt')
        R_filtered = process_rec_single_user_online_round(R_filtered)
        e.online_solutions_write(R_filtered, daily_raw_data_dir, 'neg_filtered_online_submission' + suf + '.txt')
    else:
        scores = e.local_eval_on(R)
        e.local_write_scores(scores, 'local_eval_scores'+suf+'.txt', train_dir)
        scores_filteredR = e.local_eval_on(R_filtered)
        e.local_write_scores(scores_filteredR, 'neg_filtered_local_eval_scores'+suf+'.txt', train_dir)

def filter_recs(recs, targets):
    filtered = {}
    for item, values in recs.items():
        user_list = []
        for u in values:
            if u in targets:
                user_list.append(u)
        filtered[item] = user_list[0:250]
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

def main(_):

    if FLAGS.test:
        if FLAGS.data_dir[-1] == '/':
            FLAGS.data_dir = FLAGS.data_dir[:-1] + '_test'
        else:
            FLAGS.data_dir = FLAGS.data_dir + '_test'

    if not os.path.exists(FLAGS.train_dir):
        os.mkdir(FLAGS.train_dir)
    if not FLAGS.recommend:
        print('train')
        log_path = os.path.join(FLAGS.train_dir,"log.txt")
        logging.basicConfig(filename=log_path,level=logging.DEBUG)
        train(data_dir=FLAGS.data_dir)
    else:
        print('recommend')
        log_path = os.path.join(FLAGS.train_dir,"log.recommend.txt")
        logging.basicConfig(filename=log_path,level=logging.DEBUG)
        compute_scores(data_dir=FLAGS.data_dir)
    return

if __name__ == "__main__":
    tf.app.run()
