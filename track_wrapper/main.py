from .track_stats import *
from .track_generic import *
from .composite import *
import os
import pickle
import shutil

__all__ = ['Case', 'get_case', 'delete_case']

def get_case():
    with open('/home/users/as7424/pyTRACK_dev/track_wrapper/caselog', 'rb') as f:
        log=pickle.load(f)
        for i in log:
            print(i.cname)

def delete_case(case):
    new_log=[]
    with open('/home/users/as7424/pyTRACK_dev/track_wrapper/caselog', 'rb') as f:
        log=pickle.load(f)
        for i in log:
            if i.cname!=case:
                new_log.append(i)
    
    with open('/home/users/as7424/pyTRACK_dev/track_wrapper/caselog', 'wb') as f:
                    pickle.dump(new_log, f)


class Case(object):
                
    def __init__(self, cname, outdir=None, data_dir=None, restart=False):
        self.cname=cname
        self.outdir = outdir
        self.data_dir = data_dir

        with open('/home/users/as7424/pyTRACK_dev/track_wrapper/caselog', 'rb') as f:
            log=pickle.load(f)
            for i in log:
                if i.cname==self.cname:
                    if restart:
                        self.cname=i.cname
                        self.outdir=i.outdir
                        self.data_dir=i.data_dir
                        
                    else:
                        raise Exception("Case name already exists - run with restart flag set to True")

            if (not restart):
                log.append(self)
                if os.path.exists(outdir):
                    shutil.rmtree(outdir)
                os.makedirs(outdir)
                
                with open('/home/users/as7424/pyTRACK_dev/track_wrapper/caselog', 'wb') as f:
                    pickle.dump(log, f)
        
        
    def format(self):
        print('Formatting input files and saving to ' + self.outdir+'/data')
        format_data(self.data_dir, self.outdir+'/data')
        
    def track(self):
        print('Running track and outputting to ' + self.outdir+'/track')
        track_uv(self.outdir+'/data/combined.nc', self.outdir+'/track')