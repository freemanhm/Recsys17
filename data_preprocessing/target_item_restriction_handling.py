from data_helper import DataHelper

class ProcessData(object):

    def __init__(self):
        self.data_helper_instance = DataHelper(input_dir='../data_2017_weeks',
                                               op_dir='../examples/dataset', preprocessing_cache='../examples/preprocessing_cache')
        print "Reading target items and target users"
        t_item_df = self.data_helper_instance.read_data_frame(self.data_helper_instance.target_items)
        items = [0]*t_item_df.shape[0]

        t_item_df.insert(1, 'items', items)
        t_item_df.rename(columns={'item_id': 'user_id'}, inplace=True)
        self.data_helper_instance.write_data_frame('res', t_item_df)
        print "ok"

p = ProcessData()
