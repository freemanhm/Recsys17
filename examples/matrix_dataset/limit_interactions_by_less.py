import codecs
from os.path import join

input_data_dir = "./"
output_data_dir = "./"

interactions_file = 'u.csv'
limited_interactions_file = 'less_u.csv'


class LimitInteractions(object):

    def __init__(self):
        # read 100 interaction lines and log
        filename = join(input_data_dir, interactions_file)
        doc = codecs.open(filename, 'r', 'utf8')
        writefile = join(output_data_dir, limited_interactions_file)
        writedoc = codecs.open(writefile, 'w', 'utf8')
        for i in range(1, 8):
            line = doc.readline()
            # print line
            writedoc.write(line)
p = LimitInteractions()

