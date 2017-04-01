from cache_helper import load_cache
from post_processing import filter_recs, filter_out_negs, cutoff100
from evaluate import Evaluation
sol_dir = "../solutions"
prep_dir = "../examples/preprocessing_cache"

print "Loading saved recommendations"
# online_raw_rec_hmf
# local_raw_rec_hmf
rec_local = load_cache(sol_dir, 'raw_rec_local')
rec_online = load_cache(sol_dir, 'raw_rec_online')
# rec_local = load_cache(sol_dir, '1_baseline_local_raw_rec')
# rec_online = load_cache(sol_dir, '1_baseline_online_raw_rec')
print "Finished loading"

print "Starting post processing"
t_users_int_set = load_cache(prep_dir, 'target_users_set')
neg_user_int_set = load_cache(prep_dir, 'neg_users_set')

filtered_rec_local = filter_recs(rec_local, t_users_int_set)
filtered_rec_online = filter_recs(rec_online, t_users_int_set)
print "Intermediate"
neg_filtered_rec_local = filter_out_negs(filtered_rec_local, neg_user_int_set)
neg_filtered_rec_online = filter_out_negs(filtered_rec_online, neg_user_int_set)

print "Cutoff"
filtered_rec_local = cutoff100(filtered_rec_local)
filtered_rec_online = cutoff100(filtered_rec_online)
neg_filtered_rec_local = cutoff100(neg_filtered_rec_local)
neg_filtered_rec_online = cutoff100(neg_filtered_rec_online)

print "Finished post processing"

print "Starting evaluation and submission"
e = Evaluation(prep_cache_dir=prep_dir)
e.format_submission(filtered_rec_local, filtered_rec_online, sol_dir, '_eval_scores_hmf1_filtered_1000to100.txt', '_subm_hmf1_filtered_1000to100.txt')
e.format_submission(neg_filtered_rec_local, neg_filtered_rec_online, sol_dir, '_eval_scores_hmf1_negfiltered_1000to100.txt', '_subm_hmf1_negfiltered_1000to100.txt')
print "Done"



