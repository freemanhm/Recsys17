
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf
from tensorflow.python.framework import ops
from tensorflow.python.ops import variable_scope as vs
from tensorflow.python.ops import init_ops
from tensorflow.python.ops import embedding_ops
from tensorflow.python.ops import array_ops
from tensorflow.python.ops.embedding_ops import embedding_lookup as lookup
import itertools

from mulhot_index import *

class EmbeddingAttribute(object):
  def __init__(self, user_attributes, item_attributes, mb, n_sampled,
               input_steps=0, item_output=False,
               item_ind2logit_ind=None, logit_ind2item_ind=None, indices_item=None, 
               new_user_attributes=None, target_item_attributes=None, 
               logit_ind2item_ind_target=None,
               devices=['/gpu:0']):

    self.user_attributes = user_attributes
    self.item_attributes = item_attributes
    if new_user_attributes:
      self.new_user_attributes = new_user_attributes
    if target_item_attributes:
      self.target_item_attributes = target_item_attributes

    self.batch_size = mb
    self.n_sampled = n_sampled
    self.input_steps = input_steps
    self.item_output = item_output # whether to use separate embedding for item output
    self.num_item_features = (item_attributes.num_features_cat +
                              item_attributes.num_features_mulhot)
    self.reuse_item_tr = None

    self.item_ind2logit_ind = item_ind2logit_ind
    self.logit_ind2item_ind = logit_ind2item_ind
    if logit_ind2item_ind is not None:
      self.logit_size = len(logit_ind2item_ind)
    if logit_ind2item_ind_target:
      self.logit_size_target = len(logit_ind2item_ind_target)

    if indices_item is not None:
      self.indices_item = indices_item
    else:
      self.indices_item = range(self.logit_size)
    # self.logit_size_test = logit_size_test
    self.mask = {}
    self.zero_logits = {}
    self.pos_indices = {}
    self.l_true = {}
    self.l_false = {}

    self.devices = devices

    self.att = {}
    self._init_attributes(user_attributes, name='user', device=devices[0])
    self._init_attributes(item_attributes, name='item', device=devices[0])
    # if new_user_attributes:
    #   self._init_attributes(new_user_attributes, name='new_user', device=devices[0])
    # if target_item_attributes:
    #   self._init_attributes(target_item_attributes, name='target_item', device=devices[0])

    if self.item_output:
      self._init_attributes(item_attributes, name='item_output',
                            device=devices[-1])

    # user embeddings
    self.user_embs_cat, self.user_embs_mulhot = self._embedded(user_attributes,
                                                               prefix='user', device=devices[0])
    #item embeddings
    self.item_embs_cat, self.item_embs_mulhot = self._embedded(item_attributes,
                                                               prefix='item', transpose=False, device=devices[0])
    self.i_biases_cat, self.i_biases_mulhot = self._embedded_bias(
      item_attributes, 'item', device=devices[0])
    if item_output:
      self.item_embs2_cat, self.item_embs2_mulhot = self._embedded(
        item_attributes, prefix='item_output', transpose=False, device=devices[-1])
      self.i_biases2_cat, self.i_biases2_mulhot = self._embedded_bias(
        item_attributes, 'item_output', device=devices[-1])

    # input users
    self.u_indices = {}
    self.u_indices['input'] = self._placeholders('user', 'input', mb, device=devices[0])
    self.u_indices['new_input'] = self._placeholders('user', 'new_input', mb, device=devices[0])
    self.i_indices = {}

    # item -- positive/negative sample indices
    print("construct postive/negative items/scores ")
    self.i_indices['pos'] = self._placeholders('item', 'pos', mb, device=devices[0])
    self.i_indices['neg'] = self._placeholders('item', 'neg', mb, device=devices[0])

    # mini-batch item candidate pool
    print("construct mini-batch item candicate pool")
    if self.n_sampled is not None:
      self.i_indices['sampled_pass'] = self._placeholders('item', 'sampled',
                                                          self.n_sampled, device=devices[-1])

    # input items (for lstm etc)
    print("construct input item")
    for step in xrange(input_steps):
      name_ = 'input{}'.format(step)
      self.i_indices[name_] = self._placeholders('item', name_, mb, device=devices[0])

    # item for prediction
    ''' full version'''
    with tf.device(devices[-1]):
      ia = item_attributes
      print("construct full prediction layer")
      indices_cat, indices_mulhot, segids_mulhot, lengths_mulhot = [],[],[],[]
      for i in xrange(ia.num_features_cat):
        indices_cat.append(tf.constant(ia.full_cat_tr[i]))
      for i in xrange(ia.num_features_mulhot):
        indices_mulhot.append(tf.constant(ia.full_values_tr[i]))
        segids_mulhot.append(tf.constant(ia.full_segids_tr[i]))
        lengths_mulhot.append(tf.constant(ia.full_lengths_tr[i]))
      self.i_indices['full'] = (indices_cat, indices_mulhot, segids_mulhot,
                                lengths_mulhot)

    ''' target version'''
    with tf.device(devices[-1]):
      ia = target_item_attributes
      print("construct full prediction layer")
      indices_cat, indices_mulhot, segids_mulhot, lengths_mulhot = [],[],[],[]
      for i in xrange(ia.num_features_cat):
        indices_cat.append(tf.constant(ia.full_cat_tr[i]))
      for i in xrange(ia.num_features_mulhot):
        indices_mulhot.append(tf.constant(ia.full_values_tr[i]))
        segids_mulhot.append(tf.constant(ia.full_segids_tr[i]))
        lengths_mulhot.append(tf.constant(ia.full_lengths_tr[i]))
      self.i_indices['target'] = (indices_cat, indices_mulhot, segids_mulhot,
                                lengths_mulhot)

    ''' sampled version '''
    print("sampled prediction layer")
    if self.n_sampled is not None:
      prefix = 'item_output' if self.item_output else 'item'
      self.i_indices['sampled'] = self._var_indices(self.n_sampled,
                                                    device=devices[-1])
      self.update_sampled = self._pass_sampled_items(prefix, device=devices[-1])
    return

  def _var_indices(self, size, name='sampled', opt='item', device='/gpu:0'):
    cat_indices, mulhot_indices, mulhot_segids, mulhot_lengths = [],[], [], []
    att = self.item_attributes
    with tf.device(device):
      init_int32 = tf.constant(0)
      for i in xrange(att.num_features_cat):
        cat_indices.append(tf.get_variable(dtype = tf.int32,
                                           name = "var{}_{}_cat_ind_{}".format(opt, name, i), trainable=False,
                                           initializer=tf.zeros([size],dtype=tf.int32)))
      for i in xrange(att.num_features_mulhot):
        l1 = len(att.full_values_tr[i])
        mulhot_indices.append(tf.get_variable(dtype = tf.int32, trainable=False,
                                              initializer=tf.zeros([l1],dtype=tf.int32),
                                              name = "var{}_{}_mulhot_ind_{}".format(opt, name, i)))
        l2 = len(att.full_segids_tr[i])
        assert(l1==l2), 'length of indices/segids should be the same %d/%d'%(l1,l2)
        mulhot_segids.append(tf.get_variable(dtype = tf.int32, trainable=False,
                                             initializer=tf.zeros([l2],dtype=tf.int32),
                                             name = "var{}_{}_mulhot_seg_{}".format(opt, name, i)))
        mulhot_lengths.append(tf.get_variable(dtype =tf.float32, shape= [size, 1],
                                              name = "var{}_{}_mulhot_len_{}".format(opt, name, i), trainable=False))
      return (cat_indices, mulhot_indices, mulhot_segids, mulhot_lengths)

  def _placeholders(self, opt, name, size, device='/gpu:0'):
    with tf.device(device):
      r = tf.placeholder(tf.int32, shape=[size], name = "{}_{}_ind".format(opt,
                                                                           name))
    return r

  def get_prediction(self, latent, pool='full', device='/gpu:0', output_feat=1):
    '''
    output_feat: in prediction stage
      0: not using attributes 
      1: using attributes, use mean to combine multi-hot features
      2: using attributes, use max  to combine multi-hot features
      3: same as 2, but softmax (instead of max)
    '''
    # compute inner product between item_hidden and {user_feature_embedding}
    # then lookup to compute logits
    with tf.device(device):
      out_layer = self.i_indices[pool]
      indices_cat, indices_mulhot, segids_mulhot, lengths_mulhot = out_layer
      innerps = []

      n1 = 1 if output_feat == 0 else self.item_attributes.num_features_cat
      n2 = 0 if output_feat == 0 else self.item_attributes.num_features_mulhot

      for i in xrange(n1):
        item_emb_cat = self.item_embs2_cat[i] if self.item_output else self.item_embs_cat[i]
        i_biases_cat = self.i_biases2_cat[i] if self.item_output else self.i_biases_cat[i]
        u = latent[i] if isinstance(latent, list) else latent
        inds = indices_cat[i]
        innerp = tf.matmul(item_emb_cat, tf.transpose(u)) + i_biases_cat # Vf by mb
        innerps.append(lookup(innerp, inds)) # V by mb
      offset = self.item_attributes.num_features_cat

      for i in xrange(n2):
        item_embs_mulhot = self.item_embs2_mulhot[i] if self.item_output else self.item_embs_mulhot[i]
        item_biases_mulhot = self.i_biases2_mulhot[i] if self.item_output else self.i_biases_mulhot[i]
        u = latent[i+offset] if isinstance(latent, list) else latent
        lengs = lengths_mulhot[i]
        if pool == 'full' or pool == 'target':
          inds = indices_mulhot[i]
          segids = segids_mulhot[i]
          V = self.logit_size if pool == 'full' else self.logit_size_target
        else:
          inds = tf.slice(indices_mulhot[i], [0], [self.sampled_mulhot_l[i]])
          segids = tf.slice(segids_mulhot[i], [0], [self.sampled_mulhot_l[i]])
          V = self.n_sampled
        innerp = tf.add(tf.matmul(item_embs_mulhot, tf.transpose(u)),
                        item_biases_mulhot)

        if output_feat == 1:
          innerps.append(tf.div(tf.unsorted_segment_sum(lookup(innerp,
                                                               inds), segids, V), lengs))
        elif output_feat == 2:
          innerps.append(tf.segment_max(lookup(innerp, inds), segids))
        elif output_feat == 3:
          score_max = tf.reduce_max(innerp)
          innerp = tf.subtract(innerp, score_max)
          innerps.append(score_max + tf.log(1 + tf.unsorted_segment_sum(tf.exp(
            lookup(innerp, inds)), segids, V)))
        else:
          print('Error: Attribute combination not implemented!')
          exit(1)

      logits = tf.transpose(tf.reduce_mean(innerps, 0))
    return logits

  def get_target_score(self, latent, inds, device='/gpu:0'):
    ''' TODO: max-pooling bug'''
    item_emb_cat = self.item_embs2_cat if self.item_output else self.item_embs_cat
    i_biases_cat = self.i_biases2_cat if self.item_output else self.i_biases_cat
    item_embs_mulhot = self.item_embs2_mulhot if self.item_output else self.item_embs_mulhot
    item_biases_mulhot = self.i_biases2_mulhot if self.item_output else self.i_biases_mulhot

    cat_l, mulhot_l, i_bias = self._get_embedded(item_emb_cat, item_embs_mulhot,
                                                 i_biases_cat, item_biases_mulhot, inds, self.batch_size,
                                                 self.item_attributes, 'item', concatenation=False, device=device)
    with tf.device(device):
      target_item_emb = tf.reduce_mean(cat_l + mulhot_l, 0)
      return tf.reduce_sum(tf.multiply(latent, target_item_emb), 1) + i_bias

  def get_batch_user(self, keep_prob, concat=True, name='input', no_id=False, device='/gpu:0'):
    u_inds = self.u_indices[name]
    with tf.device(device):
      if concat:
        embedded_user, user_b = self._get_embedded(self.user_embs_cat,
                                                   self.user_embs_mulhot, b_cat=None, b_mulhot=None, inds=u_inds,
                                                   mb=self.batch_size, attributes=self.user_attributes, prefix='user',
                                                   concatenation=concat, no_id=no_id, device=device)
      else:
        user_cat, user_mulhot, user_b = self._get_embedded(
          self.user_embs_cat, self.user_embs_mulhot, b_cat=None, b_mulhot=None,
          inds=u_inds, mb=self.batch_size, attributes=self.user_attributes,
          prefix='user', concatenation=concat, no_id=no_id, device=device)
        embedded_user =  tf.reduce_mean(user_cat + user_mulhot, 0)
      embedded_user = tf.nn.dropout(embedded_user, keep_prob)
    return embedded_user, user_b

  def get_batch_item(self, name, batch_size, concat=False, keep_prob=1.0,
                     no_attribute = False, device='/gpu:0'):
    assert(name in self.i_indices)
    assert(keep_prob == 1.0), 'otherwise not implemented'
    i_inds = self.i_indices[name]
    if concat:
      return self._get_embedded(self.item_embs_cat, self.item_embs_mulhot,
                                self.i_biases_cat, self.i_biases_mulhot, i_inds, batch_size,
                                self.item_attributes, 'item', True,
                                no_attribute=no_attribute, device=device)
    else:
      item_cat, item_mulhot, item_b = self._get_embedded(self.item_embs_cat,
                                                         self.item_embs_mulhot, self.i_biases_cat, self.i_biases_mulhot, i_inds,
                                                         batch_size, self.item_attributes, 'item', False,
                                                         no_attribute=no_attribute, device=device)
      return item_cat + item_mulhot, item_b

  def get_sampled_item(self, n_sampled, device='/gpu:0'):
    name = 'sampled'
    mapping = self.i_indices[name]
    with tf.device(device):
      item_cat, item_mulhot, item_b = self._get_embedded_sampled(
        self.item_embs_cat, self.item_embs_mulhot, self.i_biases_cat,
        self.i_biases_mulhot, mapping, n_sampled, self.item_attributes)
      return tf.reduce_mean(item_cat + item_mulhot, 0), item_b

  def _embedded(self, attributes, prefix='', transpose=False, device='/gpu:0'):
    '''
    variables of full vocabulary for each type of features
    '''
    with tf.device(device):
      embs_cat, embs_mulhot = [], []
      for i in xrange(attributes.num_features_cat):
        d = attributes._embedding_size_list_cat[i]
        V = attributes._embedding_classes_list_cat[i]
        if not transpose:
          embedding = tf.get_variable(name=prefix + "embed_cat_{0}".format(i),
                                      shape=[V,d], dtype=tf.float32)
        else:
          embedding = tf.get_variable(name=prefix + "embed_cat_{0}".format(i),
                                      shape=[d,V], dtype=tf.float32)
        embs_cat.append(embedding)
      for i in xrange(attributes.num_features_mulhot):
        d = attributes._embedding_size_list_mulhot[i]
        V = attributes._embedding_classes_list_mulhot[i]
        if not transpose:
          embedding = tf.get_variable(name=prefix + "embed_mulhot_{0}".format(i),
                                      shape=[V,d], dtype=tf.float32)
        else:
          embedding = tf.get_variable(name=prefix + "embed_mulhot_{0}".format(i),
                                      shape=[d,V], dtype=tf.float32)
        embs_mulhot.append(embedding)
    return embs_cat, embs_mulhot

  def _embedded_bias(self, attributes, prefix, device='/gpu:0'):
    with tf.device(device):
      biases_cat, biases_mulhot = [], []
      for i in range(attributes.num_features_cat):
        V = attributes._embedding_classes_list_cat[i]
        b = tf.get_variable(prefix + "_bias_cat_{0}".format(i), [V, 1],
                            dtype = tf.float32)
        biases_cat.append(b)
      for i in range(attributes.num_features_mulhot):
        V = attributes._embedding_classes_list_mulhot[i]
        b = tf.get_variable(prefix + "_bias_mulhot_{0}".format(i), [V, 1],
                            dtype = tf.float32)
        biases_mulhot.append(b)
    return biases_cat, biases_mulhot

  def _init_attributes(self, att, name='user', device='/gpu:0'):
    features_cat, features_mulhot, mulhot_starts, mulhot_lengths=[],[],[],[]
    with tf.device(device):
      for i in range(att.num_features_cat):
        features_cat.append(tf.constant(att.features_cat[i], dtype=tf.int32))
      for i in range(att.num_features_mulhot):
        features_mulhot.append(tf.constant(att.features_mulhot[i], dtype=tf.int32))
        mulhot_starts.append(tf.constant(att.mulhot_starts[i], dtype=tf.int32))
        mulhot_lengths.append(tf.constant(att.mulhot_lengths[i], dtype=tf.int32))
      self.att[name] = (features_cat, features_mulhot, mulhot_starts,
                        mulhot_lengths)

  def _pass_sampled_items(self, prefix='item', device='/gpu:0'):
    self.sampled_mulhot_l = []
    res = []
    var_s = self.i_indices['sampled']
    att = self.item_attributes
    inds = self.i_indices['sampled_pass']
    with tf.device(device):
      for i in xrange(att.num_features_cat):
        vals = lookup(self.att[prefix][0][i], inds)
        res.append(tf.assign(var_s[0][i], vals))
      for i in xrange(att.num_features_mulhot):
        begin_ = lookup(self.att[prefix][2][i], inds)
        size_ = lookup(self.att[prefix][3][i], inds)
        b = tf.unstack(begin_)
        s = tf.unstack(size_)
        mulhot_indices = batch_slice2(self.att[prefix][1][i], b, s, self.n_sampled)
        mulhot_segids = batch_segids2(s, self.n_sampled)

        l0 = tf.reduce_sum(size_)
        indices = tf.range(l0)
        res.append(tf.scatter_update(var_s[1][i], indices, mulhot_indices))
        res.append(tf.scatter_update(var_s[2][i], indices, mulhot_segids))
        res.append(tf.assign(var_s[3][i], tf.reshape(tf.to_float(size_), [self.n_sampled, 1])))

        l = tf.get_variable(name='sampled_l_mulhot_{}'.format(i), dtype=tf.int32,
                            initializer=tf.constant(0), trainable=False)
        self.sampled_mulhot_l.append(l)
        res.append(tf.assign(l, l0))
    return res

  def _get_embedded(self, embs_cat, embs_mulhot, b_cat, b_mulhot,
                    inds, mb, attributes, prefix='', concatenation=True, no_id=False,
                    no_attribute=False, device='/gpu:0'):
    cat_list, mulhot_list = [], []
    bias_cat_list, bias_mulhot_list = [], []
    with tf.device(device):
      if no_id and attributes.num_features_cat == 1:
        if b_cat is not None or b_mulhot is not None:
          print('error: not implemented')
          exit()
        bias = None
        dim = attributes._embedding_size_list_cat[0]
        cat_list = [tf.zeros([mb, dim],dtype=tf.float32)]
        if concatenation:
          return cat_list[0], bias
        else:
          return cat_list, [], bias

      n1 = 1 if no_attribute else attributes.num_features_cat
      n2 = 0 if no_attribute else attributes.num_features_mulhot

      for i in xrange(n1):
        if no_id and i == 0:
          continue
        cat_indices = lookup(self.att[prefix][0][i], inds)
        embedded = lookup(embs_cat[i], cat_indices,
                          name='emb_lookup_item_{0}'.format(i))  # on cpu?
        cat_list.append(embedded)
        if b_cat is not None:
          b = lookup(b_cat[i], cat_indices,
                     name = 'emb_lookup_item_b_{0}'.format(i))
          bias_cat_list.append(b)
      for i in xrange(n2):
        begin_ = lookup(self.att[prefix][2][i], inds)
        size_ = lookup(self.att[prefix][3][i], inds)
        # mulhot_indices, mulhot_segids = batch_slice_segids(
        #   self.att[prefix][1][i], begin_, size_, mb)

        # mulhot_indices = batch_slice(self.att[prefix][1][i], begin_,
        #   size_, mb)
        # mulhot_segids = batch_segids(size_, mb)

        b = tf.unstack(begin_)
        s = tf.unstack(size_)
        mulhot_indices = batch_slice2(self.att[prefix][1][i], b,
                                      s, mb)
        mulhot_segids = batch_segids2(s, mb)
        embedded_flat = lookup(embs_mulhot[i], mulhot_indices)
        embedded_sum = tf.unsorted_segment_sum(embedded_flat, mulhot_segids, mb)
        lengs = tf.reshape(tf.to_float(size_), [mb, 1])
        embedded = tf.div(embedded_sum, lengs)
        mulhot_list.append(embedded)
        if b_mulhot is not None:
          b_embedded_flat = lookup(b_mulhot[i], mulhot_indices)
          b_embedded_sum = tf.unsorted_segment_sum(b_embedded_flat, mulhot_segids,
                                                   mb)
          b_embedded = tf.div(b_embedded_sum, lengs)
          bias_mulhot_list.append(b_embedded)

      if b_cat is None and b_mulhot is None:
        bias = None
      else:
        bias = tf.squeeze(tf.reduce_mean(bias_cat_list + bias_mulhot_list, 0))

      if concatenation:
        return concat_versions(1, cat_list + mulhot_list), bias
      else:
        return cat_list, mulhot_list, bias

  def _get_embedded2(self, embs_cat, embs_mulhot, b_cat, b_mulhot,
                     inds, mb, attributes, prefix='', concatenation=True, no_id=False,
                     device='/gpu:0'):
    cat_list, mulhot_list = [], []
    bias_cat_list, bias_mulhot_list = [], []
    with tf.device(device):
      if no_id and attributes.num_features_cat == 1:
        if b_cat is not None or b_mulhot is not None:
          print('error: not implemented')
          exit()
        bias = None
        dim = attributes._embedding_size_list_cat[0]
        cat_list = [tf.zeros([mb, dim],dtype=tf.float32)]
        if concatenation:
          return cat_list[0], bias
        else:
          return cat_list, [], bias

      for i in xrange(attributes.num_features_cat):
        if no_id and i == 0:
          continue
        cat_indices = lookup(self.att[prefix][0][i], inds)
        embedded = lookup(embs_cat[i], cat_indices,
                          name='emb_lookup_item_{0}'.format(i))  # on cpu?
        cat_list.append(embedded)
        if b_cat is not None:
          b = lookup(b_cat[i], cat_indices,
                     name = 'emb_lookup_item_b_{0}'.format(i))
          bias_cat_list.append(b)
      for i in xrange(attributes.num_features_mulhot):
        begin_ = tf.unstack(lookup(self.att[prefix][2][i], inds))
        size_ = tf.unstack(lookup(self.att[prefix][3][i], inds))
        mulhot_i = []
        b_mulhot_i = []
        for j in xrange(mb):
          b = begin_[j]
          s = size_[j]
          m_inds = tf.slice(self.att[prefix][1][i], [b], [s])
          mulhot_i.append(tf.reduce_mean(lookup(embs_mulhot[i], m_inds), 0))
          # mulhot_i.append(tf.reduce_mean(lookup(embs_mulhot[i], m_inds), 0, True))
          if b_mulhot is not None:
            b_mulhot_i.append(tf.reduce_mean(lookup(b_mulhot[i], m_inds), 0))
            # b_mulhot_i.append(tf.reduce_mean(lookup(b_mulhot[i], m_inds), 0,
            #   True))
        # mulhot_list.append(concat_versions(0, mulhot_i))
        mulhot_list.append(tf.stack(mulhot_i))
        if b_mulhot is not None:
          # bias_mulhot_list.append(concat_versions(0, b_mulhot_i))
          bias_mulhot_list.append(tf.stack(b_mulhot_i))

      if b_cat is None and b_mulhot is None:
        bias = None
      else:
        bias = tf.squeeze(tf.reduce_mean(bias_cat_list + bias_mulhot_list, 0))

      if concatenation:
        return concat_versions(1, cat_list + mulhot_list), bias
      else:
        return cat_list, mulhot_list, bias

  def _get_embedded_sampled(self, embs_cat, embs_mulhot, b_cat, b_mulhot,
                            mappings, n_sampled, attributes, device='/gpu:0'):
    cat_indices, mulhot_indices, mulhot_segids, mulhot_lengths = mappings
    cat_list, mulhot_list = [], []
    bias_cat_list, bias_mulhot_list = [], []
    with tf.device(device):
      for i in xrange(attributes.num_features_cat):
        embedded = lookup(embs_cat[i], cat_indices[i])
        cat_list.append(embedded)
        if b_cat is not None:
          b = lookup(b_cat[i], cat_indices[i])
          bias_cat_list.append(b)
      for i in xrange(attributes.num_features_mulhot):
        inds = tf.slice(mulhot_indices[i], [0], [self.sampled_mulhot_l[i]])
        segids = tf.slice(mulhot_segids[i], [0], [self.sampled_mulhot_l[i]])
        embedded_flat = lookup(embs_mulhot[i], inds)
        embedded_sum = tf.unsorted_segment_sum(embedded_flat, segids, n_sampled)
        embedded = tf.div(embedded_sum, mulhot_lengths[i])
        mulhot_list.append(embedded)
        if b_mulhot is not None:
          b_embedded_flat = lookup(b_mulhot[i], inds)
          b_embedded_sum = tf.unsorted_segment_sum(b_embedded_flat,
                                                   segids, n_sampled)
          b_embedded = tf.div(b_embedded_sum, mulhot_lengths[i])
          bias_mulhot_list.append(b_embedded)
      if b_cat is None and b_mulhot is None:
        bias = None
      else:
        bias = tf.squeeze(tf.reduce_mean(bias_cat_list + bias_mulhot_list, 0))
      return cat_list, mulhot_list, bias

  def get_user_model_size(self, no_id=False, concat=True):
    if concat == True:
      cat_start = 1 if no_id else 0
      return (sum(self.user_attributes._embedding_size_list_cat[cat_start:self.user_attributes.num_features_cat]) +
              sum(self.user_attributes._embedding_size_list_mulhot[0:self.user_attributes.num_features_mulhot]))
    else:
      return self.user_attributes._embedding_size_list_cat[0]

  def get_item_model_size(self, concat=True):
    if concat:
      return (sum(self.item_attributes._embedding_size_list_cat[0:self.item_attributes.num_features_cat]) +
              sum(self.item_attributes._embedding_size_list_mulhot[0:self.item_attributes.num_features_mulhot]))
    else:
      return self.item_attributes._embedding_size_list_cat[0]

  def compute_loss(self, logits, item_target, loss='ce', pool='full', device='/gpu:0'):
    assert(loss in ['ce', 'mce', 'warp', 'mw', 'bbpr', 'bpr', 'bpr-hinge'])
    with tf.device(device):
      if loss == 'ce':
        return tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=item_target)
      elif loss == 'warp':
        return self._compute_warp_loss(logits, item_target, pool=pool)
      elif loss == 'mw':
        return self._compute_mw_loss(logits, item_target, pool=pool)
      elif loss =='bbpr':
        return self._compute_bbpr_loss(logits, item_target, pool=pool)
      elif loss == 'bpr':
        return tf.log(1 + tf.exp(logits))
      elif loss == 'bpr-hinge':
        return tf.maximum(1 + logits, 0)
      else:
        print('Error: not implemented other loss!!')
        exit(1)

  def _compute_bbpr_loss(self, logits, item_target):
    loss = 'bbpr'
    if loss not in self.mask:
      self._prepare_warp_vars(loss)
    V = self.logit_size
    mb = self.batch_size
    flat_matrix = tf.reshape(logits, [-1])
    idx_flattened = self.idx_flattened0 + item_target
    logits_ = tf.gather(flat_matrix, idx_flattened)
    logits_ = tf.reshape(logits_, [mb, 1])
    logits2 = tf.subtract(logits, logits_) + 1
    mask2 = tf.reshape(self.mask[loss], [mb, V])
    target = tf.where(mask2, logits2, self.zero_logits[loss])
    return tf.reduce_sum(tf.nn.relu(target), 1)

  def _compute_warp_loss(self, logits, item_target, pool='full'):
    loss = 'warp'    
    if loss not in self.mask:
      self._prepare_warp_vars(loss)
    if pool == 'target':
      return tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=item_target)

    # V = self.logit_size
    V = self.logit_size if pool == 'full' else self.logit_size_target
    mb = self.batch_size
    flat_matrix = tf.reshape(logits, [-1])
    idx_flattened = self.idx_flattened0 + item_target
    logits_ = tf.gather(flat_matrix, idx_flattened)
    logits_ = tf.reshape(logits_, [mb, 1])
    logits2 = tf.subtract(logits, logits_) + 1
    mask2 = tf.reshape(self.mask[loss], [mb, V])
    target = tf.where(mask2, logits2, self.zero_logits[loss])
    return tf.log(1 + tf.reduce_sum(tf.nn.relu(target), 1))

  def _compute_mw_loss(self, logits, item_target):
    if 'mw' not in self.mask:
      self._prepare_warp_vars('mw')
    V = self.n_sampled
    mb = self.batch_size
    logits2 = tf.subtract(logits, tf.reshape(item_target, [mb, 1])) + 1
    mask2 = tf.reshape(self.mask['mw'], [mb, V])
    target = tf.where(mask2, logits2, self.zero_logits['mw'])
    return tf.log(1 + tf.reduce_sum(tf.nn.relu(target), 1)) # scale or not??

  def _prepare_warp_vars(self, loss= 'warp'):
    if loss == 'mw':
      V = self.n_sampled
    elif loss == 'warp':
      V = self.logit_size
    elif loss == 'warp-target':
      V = self.logit_size_target
    # V = self.n_sampled if loss == 'mw' else self.logit_size
    mb = self.batch_size
    self.idx_flattened0 = tf.range(0, mb) * V
    self.mask[loss] = tf.Variable([True] * V * mb, dtype=tf.bool,
                                  trainable=False)
    self.zero_logits[loss] = tf.constant([[0.0] * V] * mb)
    self.pos_indices[loss] = tf.placeholder(tf.int32, shape = [None])
    self.l_true[loss] = tf.placeholder(tf.bool, shape = [None], name='l_true')
    self.l_false[loss] = tf.placeholder(tf.bool, shape = [None], name='l_false')

  def get_warp_mask(self, device='/gpu:0'):
    self.set_mask, self.reset_mask = {}, {}
    with tf.device(device):
      for loss in ['mw', 'warp', 'bbpr']:
        if loss not in self.mask:
          continue
        self.set_mask[loss] = tf.scatter_update(self.mask[loss],
                                                self.pos_indices[loss], self.l_false[loss])
        self.reset_mask[loss] = tf.scatter_update(self.mask[loss],
                                                  self.pos_indices[loss], self.l_true[loss])
      return self.set_mask, self.reset_mask

  def prepare_warp(self, pos_item_set, pos_item_set_eval):
    self.pos_item_set = pos_item_set
    self.pos_item_set_eval = pos_item_set_eval
    return

  def target_mapping(self, item_target):
    m = self.item_ind2logit_ind
    target = []
    for items in item_target:
      target.append([m[v] for v in items])
    return target

  def _add_input(self, input_feed, opt, input_, name_):
    if opt == 'user':
      att = self.user_attributes
      mappings = self.u_indices[name_]
    elif opt == 'item':
      att = self.item_attributes
      mappings = self.i_indices[name_]
    else:
      exit(-1)
    input_feed[mappings.name] = input_

  def add_input(self, input_feed, user_input, item_input,
                neg_item_input=None, item_sampled = None, item_sampled_id2idx = None,
                forward_only=False, recommend=False, loss=None, new_users=False):
    # users
    if self.user_attributes is not None and not new_users:
      self._add_input(input_feed, 'user', user_input, 'input')
    elif self.new_user_attributes and new_users:
      self._add_input(input_feed, 'user', user_input, 'new_input')
    # pos
    # if self.item_attributes is not None and recommend is False and self.input_steps == 0:
    #   self._add_input(input_feed, 'item', item_input, 'pos')
    #   self._add_input(input_feed, 'item', neg_item_input, 'neg')    

    # input item: for lstm, skipgram,
    if self.item_attributes is not None and self.input_steps > 0:
      for step in range(len(item_input)):
        self._add_input(input_feed, 'item', item_input[step],
                        'input{}'.format(step))

    # sampled item: when sampled-loss is used
    input_feed_sampled = {}
    update_sampled = []
    if self.item_attributes is not None and recommend is False and item_sampled is not None and loss in ['mw', 'mce']:
      self._add_input(input_feed_sampled, 'item', item_sampled, 'sampled_pass')
      update_sampled = self.update_sampled

    # for warp loss.
    input_feed_warp = {}
    if loss in ['warp', 'mw', 'bbpr'] and recommend is False:
      V = self.n_sampled if loss == 'mw' else self.logit_size
      mask_indices, c = [], 0
      s_2idx = self.item_ind2logit_ind if loss in ['warp', 'bbpr'] else item_sampled_id2idx
      item_set = self.pos_item_set_eval if forward_only else self.pos_item_set

      if loss in ['warp', 'bbpr']:
        for u in user_input:
          offset = c * V
          if u in item_set:
            mask_indices.extend([s_2idx[v] + offset for v in item_set[u]])
          c += 1
      else:
        for u in user_input:
          offset = c * V
          if u in item_set:
            mask_indices.extend([s_2idx[v] + offset for v in item_set[u]
                                 if v in s_2idx])
          c += 1
      L = len(mask_indices)
      input_feed_warp[self.pos_indices[loss].name] = mask_indices
      input_feed_warp[self.l_false[loss].name] = [False] * L
      input_feed_warp[self.l_true[loss].name] = [True] * L

    return update_sampled, input_feed_sampled, input_feed_warp

    
