from os.path import join
import pickle
import pandas as pd


def load_cache(directory, filename):
    filepath = join(directory, filename)
    return pickle.load(open(filepath, 'rb'))


def read_obs(files, dataset):
    final_df = pd.DataFrame()
    for filename in files:
        df = get_obs(dataset, filename)
        final_df = final_df.append(df)
    return final_df.values


def get_obs(dataset, filename):
    filepath = join(dataset, filename)
    df = pd.read_csv(filepath, delimiter='\t', dtype='str')
    return df


def log_recs(recs, filename, sol_dir):
    f = open(join(sol_dir, filename), 'wb')
    pickle.dump(recs, f)


def read_recs(filename, sol_dir):
    f = open(join(sol_dir, filename), 'rb')
    return pickle.load(f)

