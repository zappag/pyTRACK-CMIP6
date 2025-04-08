from .track_stats import *
from .track_generic import *
from .composite import *
import os
import pickle
import shutil

# get path of this file
dir_path = os.path.dirname(__file__)

__all__ = ['Case', 'get_case', 'delete_case']

# returns a list of cases from the log file
def get_case():
    with open(dir_path+'/caselog', 'rb') as f:
        log=pickle.load(f)
        for i in log:
            print(i.cname)

# deletes a case from the log file
def delete_case(case):
    new_log=[]
    with open(dir_path+'/caselog', 'rb') as f:
        log=pickle.load(f)
        for i in log:
            if i.cname!=case:
                new_log.append(i)
    
    with open(dir_path+'/caselog', 'wb') as f:
                    pickle.dump(new_log, f)


# Defines a case object
class Case(object):

    '''
    Argument list:
    cname(String) : Name of the case
    outdir(PathString) : Directory to save the processed outputs
    data_dir(PathString) : Single .nc file containing u and v winds at a single height level. Can also pass a directory containing the data in multiple files (-- dev_flag)
    restart(Boolean) : Passing restart=True loads the case from the log file.
    '''
    def __init__(self, cname, outdir=None, data_dir=None, restart=False):
        self.cname=cname
        self.outdir = outdir
        self.data_dir = data_dir

        with open(dir_path+'/caselog', 'rb') as f:
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
                    raise Exception(outdir+' already exists - remove existing folder or input new location')
                    # shutil.rmtree(outdir)
                os.makedirs(outdir)
                
                with open(dir_path+'/caselog', 'wb') as f:
                    pickle.dump(log, f)
        
    ## List of functions

    def format(self):
        print('Formatting input files and saving to ' + self.outdir+'/data')
        format_data_single(self.data_dir, self.outdir+'/data', uname='U', vname='V', plev=85000)
        
    def track(self):
        print('Running track and outputting to ' + self.outdir+'/track')
        track_uv(self.outdir+'/data/'+os.path.basename(self.data_dir)[:-3]+'_CMIP.nc', self.outdir+'/track')

    def stats(self):
        print('Running stats and outputting to ' + self.outdir+'/stats')
        track_stats(self.outdir+'/track/', self.outdir+'/stats')