from argparse import ArgumentParser
import os, pickle
import pandas as pd

u_attr = ['id','industry_id','discipline_id','career_level','country','latitude','longitude',
          'created_at','is_payed','region','employment','title','tags']

u_attr_values = [[0, 0, 0, 0, 0, 2, 2,
                  2, 0, 0, 0, 1, 1]]


parser = ArgumentParser()
parser.add_argument('-f', '--fetch', dest='folder', help='Folder with fetched daily data')

workspace = '/local/recsys'


def clean_daily_items(daily_folder):
    data_dir = os.path.join(workspace+"/online/", daily_folder)
    write_dir = data_dir
    f_names = ['items.csv']
    w_names = ['clean_items.csv']
    for name, w_name in zip(f_names, w_names):
        f = open(os.path.join(data_dir, name), 'r')
        w = open(os.path.join(write_dir, w_name), 'w')
        for line in f.readlines():
            line = line.replace('NULL', '-1')
            w.write(line)
        w.close()
        f.close()
    return

def process_daily_data(daily_folder):
    data_dir = workspace+'/online/'+daily_folder
    print data_dir
    write_dir = os.path.join(workspace+"/raw_data_daily/", daily_folder)
    f_names = ['clean_items.csv']
    w_names = ['daily_u.csv']

    item_df = read_data_frame(data_dir, f_names[0])
    df = _reformat_columns(item_df)
    paid_item_set = _restrict_by_attr(df, 'is_payed', 1)
    pf = open(os.path.join(write_dir, 'daily_paid_item_set'), 'wb')
    # print list(paid_item_set)[0:10]
    pickle.dump(paid_item_set, pf)
    write_data_frame(write_dir, w_names[0], df)

    target_items_ids_list = df['id'].values
    pf = open(os.path.join(write_dir+'/'+'daily_target_items_list'), 'wb')
    # print list(target_items_ids_list)[0:10]
    pickle.dump(target_items_ids_list, pf)

    users_df = read_data_frame(data_dir, 'users.csv')
    users = [user[0] for user in users_df.values]
    target_users_set = set(users)
    pf = open(os.path.join(write_dir+'/'+'daily_target_users_set'), 'wb')
    # print list(target_users_set)[0:10]
    pickle.dump(target_users_set, pf)

    u_attr_df = attr_df(u_attr, u_attr_values)
    write_data_frame(write_dir, 'u_attr.csv', u_attr_df)
    return

def attr_df(attr_header, attr_values):
    df = pd.DataFrame(attr_values)
    df.columns = attr_header
    return df

def read_data_frame(data_dir, filename):
    filename = os.path.join(data_dir, filename)
    doc = open(filename, 'r')
    df = pd.read_csv(doc, sep="\t", header=0)
    return df


def write_data_frame(out_dir, filename, data):
    filename = os.path.join(out_dir, filename)
    doc = open(filename, 'w')
    data.to_csv(doc, sep='\t', header=True, index=False)
    return


def _reformat_columns(df):
    c_list = []
    for c in df.columns.values:
        c_list.append(c.split('.')[1])
    return pd.DataFrame(df.values, columns=c_list)


def _restrict_by_attr(df, attr_index, attr_value):
    prem_set = set()
    index = df.columns.get_loc(attr_index)
    for row in df.values:
        if row[index] == attr_value:
            prem_set.add(row[0])
    return prem_set



if __name__ == '__main__':
    args = parser.parse_args()
    daily_folder = args.folder
    # eg -f 2017-05-01
    print daily_folder

    clean_daily_items(daily_folder)
    process_daily_data(daily_folder)
    print "Finished preprocessing"

    import subprocess
    subprocess.call("~/recommendation/recommend.sh "+daily_folder, shell=True)
    print "Finished recommendations"

    # subprocess.call("~/recommendation/submission.sh "+daily_folder, shell=True)
    # print "Finished submission for " + daily_folder





'''
online/daily_folder (similar to clean_*.py)
@ fetched data [interactions.csv, users.csv, items.csv]
@ cleaned data [ clean_items.csv ]
raw_data | raw_data_daily/daily_folder (similar to preprocess_for_hmf.py)
@ basic files original same=[i_attr, i, 'obs', 'locals', u_attr] cannot use the same u.csv
@ new files = [daily target items list, daily target users set, daily u.csv, daily_paid_item_set]
'''




