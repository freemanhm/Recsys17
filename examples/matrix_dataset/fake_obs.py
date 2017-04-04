import codecs
from os.path import join
import datetime

input_data_dir = "./"
output_data_dir = "./"

u_file = 'u.csv'
i_file = 'i.csv'
obs_file = 'obs_te.csv'

class FakeObs(object):

    def __init__(self):
        u_set = []
        i_set = []
        filename = join(input_data_dir, u_file)
        doc = codecs.open(filename, 'r', 'utf8')
        doc.readline()
        for i in range(1, 8):
            line = doc.readline()
            vals = line.split('\t')
            u_set.append(vals[0])

        filename = join(input_data_dir, i_file)
        doc = codecs.open(filename, 'r', 'utf8')
        doc.readline()
        for i in range(1, 8):
            line = doc.readline()
            vals = line.split('\t')
            i_set.append(vals[0])

        u_set.remove('')
        i_set.remove('')
        i_set.remove('')

        print u_set
        print i_set

        writefile = join(output_data_dir, obs_file)
        writedoc = codecs.open(writefile, 'w', 'utf8')
        writedoc.write('item_id\tuser_id\ttime\ttype\n')
        for i in u_set:
            for u in i_set:
                obs = str(i)+'\t'+str(u)+'\t'+str(4578)+"\t1\n"
                writedoc.write(obs)

FakeObs()