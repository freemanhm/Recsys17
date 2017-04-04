from os.path import join
import pandas as pd
import pickle


def load_df(directory, filename):
    f_path = join(directory, filename)
    f = open(f_path, 'r')
    return pd.read_csv(f, delimiter='\t')


def load_df_list(directory, list_filenames):
    final_df = pd.DataFrame()
    for filename in list_filenames:
        df = load_df(directory, filename)
        final_df.append(df)
    return final_df


def dump_to_cache(object_to_save, directory, filename):
    f_path = join(directory, filename)
    f = open(f_path, 'wb')
    pickle.dump(object_to_save, f)


def load_from_cache(directory, filename):
    f_path = join(directory, filename)
    f = open(f_path, 'rb')
    return pickle.load(f)
