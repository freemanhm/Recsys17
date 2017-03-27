from os.path import join, isfile
import pandas as pd
import numpy as np
import codecs

print "Load Data"
def build_index(values):
  count, index = 0, {}
  opt = 1 if values.shape[1] else 0
  for v in values:
    if opt == 1:
      index[v[0]] = count
    elif opt == 0:
      index[v] = count
    count += 1
  return index

def load_csv(filename, indexing=True, sep = "\t", header=0):
  if not isfile(filename):
    return [],None, None if indexing else [], None
  data = pd.read_csv(filename, sep=sep, header=header)
  columns = list(data.columns)
  values = data.values
  if indexing:
    index = build_index(values)
    return values, columns, index
  else:
    return values, columns

def file_check(filename):
  if not isfile(filename):
    print("Error: user file {} does not exit!".format(filename))
    exit(1)
  return

def load_users(data_dir, sep='\t'):
  filename = join(data_dir, 'u.csv')
  file_check(filename)
  users, attr_names, user_index = load_csv(filename)
  filename = join(data_dir, 'u_attr.csv')
  if isfile(filename):
    vals, _ = load_csv(filename, False)
    attr_types = vals.flatten().tolist()
  else:
    attr_types = [0] * len(attr_names)
  return users, (attr_names, attr_types), user_index

def load_items(data_dir, sep='\t'):
  filename = join(data_dir, 'i.csv')
  file_check(filename)
  items, attr_names, item_index = load_csv(filename)
  filename = join(data_dir, 'i_attr.csv')
  if isfile(filename):
    vals, _ = load_csv(filename, False)
    attr_types = vals.flatten().tolist()
  else:
    attr_types = [0] * len(attr_names)
  return items, (attr_names, attr_types), item_index

def load_interactions(data_dir, sep='\t'):
  filename0 = join(data_dir, 'obs_')
  suffix = ['tr.csv', 'va.csv', 'te.csv']
  ints, names = [], []
  for s in suffix:
    filename = filename0 + s
    interact, name = load_csv(filename, False)
    assert(interact.shape[1] >= 2)
    if interact.shape[1] == 2:
      l = interact.shape[0]
      interact = np.append(interact, np.zeros((l, 1), dtype=int), 1)
    ints.append(interact)
    names.append(name)
  return ints, names[0]

def load_raw_data(data_dir, _submit=0):
  users, u_attr, user_index = load_users(data_dir)
  items, i_attr, item_index = load_items(data_dir)
  ints, names = load_interactions(data_dir)
  for v in ints:
    for i in range(len(v)):
      v[i][0] = user_index[v[i][0]]
      v[i][1] = item_index[v[i][1]]
  interact_tr, interact_va, interact_te = ints

  data_va, data_te = None, None
  if _submit == 1:    
    interact_tr = np.append(interact_tr, interact_va, 0)
    data_tr = zip(list(interact_tr[:, 0]), list(interact_tr[:, 1]), 
      list(interact_tr[:, 2]))
    data_va = zip(list(interact_te[:, 0]), list(interact_te[:, 1]), 
      list(interact_te[:, 2]))
  else:
    data_tr = zip(list(interact_tr[:, 0]), list(interact_tr[:, 1]), 
      list(interact_tr[:, 2]))
    data_va = zip(list(interact_va[:, 0]), list(interact_va[:, 1]), 
      list(interact_va[:, 2]))
  return users, items, data_tr, data_va, u_attr, i_attr, user_index, item_index

