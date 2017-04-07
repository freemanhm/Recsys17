import cPickle as pickle

DIR = '../examples/preprocessing_cache/'
class Weights(object):
  def __init__(self, user_index, item_index):
    self.rewards = {1:1, 2:5, 3:5, 5:20}

    prem_user = list(pickle.load(open(DIR + 'prem_user_set', 'r')))
    self.prem_user = set([user_index[u]  for u in prem_user if u in user_index])
    paid_item = list(pickle.load(open(DIR + 'paid_item_set', 'r')))
    self.paid_item = set([item_index[i] for i in paid_item if i in item_index])
    return

  def get_loss_weight(self, user, item, types):
    w = [self.rewards[t] for t in types]
    ux = [1 + float(u in self.prem_user) for u in user]
    ix = [1 + float(i in self.paid_item) for i in item]
    w = [wx[0] * wx[1] for wx in zip(w, ux)]
    w = [wx[0] * wx[1] for wx in zip(w, ix)]
    return w
