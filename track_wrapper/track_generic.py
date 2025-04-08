import os
from cdo import *
from netCDF4 import Dataset
from pathlib import Path
from math import ceil
import subprocess
import xarray as xr
import shutil

cdo = Cdo()

__all__ = ['track_uv', 'format_data']

class cmip6_indat(object):
    """Class to obtain basic information about the CMIP6 input data."""
    def __init__(self, filename):
        """
        Reads the netCDF file and scans its variables.

        Parameters
        ----------
        filename : string
            Filename of a .nc file containing CMIP6 sea level pressure or wind
            velocity data.

        """
        self.filename = filename
        self.data = Dataset(filename, 'r')
        self.vars = [var for var in self.data.variables]

    def get_nx_ny(self):
        # returns number of latitudes and longitudes in the grid
        return str(len(self.data.variables['lon'][:])), \
                str(len(self.data.variables['lat'][:]))

    def get_grid_type(self):
        # returns the grid type
        return cdo.griddes(input=self.filename)[3]

    def get_variable_type(self):
        # returns the variable type
        return self.vars[-1]

    def get_timesteps(self):
        # returns the number of timesteps
        return int(len(self.data.variables['time'][:]))

class data_indat(object):
    """Class to obtain basic information about the CMIP6/ERA input data."""
    def __init__(self, filename, data_type='cmip6'):
        """
        Reads the netCDF file and scans its variables.

        Parameters
        ----------


        filename : string
            Filename of a .nc file containing CMIP6 sea level pressure or wind
            velocity data.

        """
        self.filename = filename
        self.data_type = data_type
        self.data = Dataset(filename, 'r')
        self.vars = [var for var in self.data.variables]

    def get_nx_ny(self):
        # returns number of latitudes and longitudes in the grid
        if self.data_type == 'era5':
            return str(len(self.data.variables['longitude'][:])), \
                    str(len(self.data.variables['latitude'][:]))
        elif self.data_type == 'cmip6':
            return str(len(self.data.variables['lon'][:])), \
                    str(len(self.data.variables['lat'][:]))

    def get_grid_type(self):
        # returns the grid type
        return cdo.griddes(input=self.filename)[3]

    def get_variable_type(self):
        # returns the variable type
        return self.vars[-1]

    def get_timesteps(self):
        # returns the number of timesteps
        return int(len(self.data.variables['time'][:]))

    def has_equator(self):
        # check if the data has an equator
        if self.data_type == 'era5':
            if 0 in self.data.variables['latitude'][:]:
                return True
            else:
                return False
        elif self.data_type == 'cmip6':
            if 0 in self.data.variables['lat'][:]:
                return True
            else:
                return False

    def has_nh_pole(self):
        # check if the data has an NH
        if self.data_type == 'era5':
            if 90 in self.data.variables['latitude'][:]:
                return True
            else:
                return False
        elif self.data_type == 'cmip6':
            if 90 in self.data.variables['lat'][:]:
                return True
            else:
                return False

    def has_sh_pole(self):
        # check if the data has an NH
        if self.data_type == 'era5':
            if -90 in self.data.variables['latitude'][:]:
                return True
            else:
                return False
        elif self.data_type == 'cmip6':
            if -90 in self.data.variables['lat'][:]:
                return True
            else:
                return False

def merge_uv(file1, file2, outfile,uname,vname):
    """
    Merge  U and V files into a UV file.

    Parameters
    ----------

    file1 : string
        Path to .nc file containing either U or V data

    file2 : string
        Path to .nc file containing either V or U data, opposite of file1

    outfile : string
        Path of desired output file


    """
    data1 = cmip6_indat(file1)
    data2 = cmip6_indat(file2)

    if data1.get_variable_type() == uname:
        u_file = file1
        v_file = file2

    elif data1.get_variable_type() == vname:
        u_file = file2
        v_file = file1

    else:
        raise Exception("Invalid input variable type. Please input ERA5 \
                            u or v file.")

    dir_path = os.path.dirname(file1)
    
    outfile = os.path.join(dir_path, os.path.basename(outfile))

    print("Merging u&v files")
    cdo.merge(input=" ".join((u_file, v_file)), output=outfile)
    print("Merged U and V files into UV file named: ", outfile)
        
    return outfile


def regrid_cmip6(input, outfile):
    """
    Detect grid of input data and regrid to gaussian grid if necessary.

    Parameters
    ----------

    input : string
        Path to .nc file containing input data

    outfile : string
        Desired path of regridded file

    """
    data = cmip6_indat(input)

    gridtype = data.get_grid_type()

    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")

    # check for resolution and regrid
    else:
        nx, ny = data.get_nx_ny()
        if int(ny) <= 80:
            cdo.remapcon("n32", input=input, output=outfile)
            grid = 'n32'
        elif int(ny) <= 112:
            cdo.remapcon("n48", input=input, output=outfile)
            grid = 'n48'
        elif int(ny) <= 150:
            cdo.remapcon("n64", input=input, output=outfile)
            grid = 'n64'
        else:
            cdo.remapcon("n80", input=input, output=outfile)
            grid = 'n80'
        print("Regridded to " + grid + " Gaussian grid.")

    return

def calc_vorticity(uv_file, outfile, copy_file=True):
    """
    Use TRACK to calculate vorticity at 850 hPa from horizontal wind velocities.

    Parameters
    ----------

    uv_file : string
        Path to .nc file containing combined U and V data

    outfile : string
        Desired base name of .dat vorticity file that will be output into the
        TRACK/indat directory.

    copy_file : boolean, optional
        Whether or not the uv_file will be copied into the TRACK directory. This
        is not needed within the tracking functions, but needed for manual use.

    """
    os.chdir(str(Path.home()) + "/TRACK") # change to TRACK directory

    # gather information about data
    year = cdo.showyear(input=uv_file)[0]

    uv = cmip6_indat(uv_file)
    nx, ny = uv.get_nx_ny()
    u_name = uv.vars[-2]
    v_name = uv.vars[-1]

    # # generate input file and calculate vorticity using TRACK
    os.system("sed -e \"s/VAR1/"+ u_name + "/;s/VAR2/" + v_name + "/;s/NX/" +
                nx + "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile +
                "/\" indat/calcvor_onelev.in > indat/calcvor_onelev_spec.in")
    os.system("bin/track.linux -i " + os.path.basename(uv_file) + " -f y" + year + " < indat/calcvor_onelev_spec.in")

    return
    

def track_uv(infile, outdirectory, infile2='none', NH=True, ysplit=True, shift=False):

    """
    Calculate 850 hPa vorticity from generic horizontal wind velocity data
    and run TRACK.
    dev -- If the data is not in the CMIP format, align data with CMIP convention 
    dev -- do both north and south at same time
    
    Parameters
    ----------

    infile : string
        Path to .nc file containing combined UV data

    outdirectory : string
        Path of directory to output tracks to

    infile2 : string, optional
        Path to second input file, if U and V are in separate files and
        need to be combined.

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.

    shift : boolean, optional
        Pass true if data is shifted to track for DJF -- shifts time start time back to november after tracking
    """

    # set outdir -- full path the output track directory
    outdir = os.path.abspath(os.path.expanduser(outdirectory))

    # check if U and V are in the same file, if not merge them in "input"
    outfile_uv = "uv_merged.nc"
    dir_path = os.path.dirname(infile)
    if infile2 == 'none':
        os.system("cp " + infile + " " + dir_path+"/uv_merged.nc")
    else: # if U and V separate, merge into UV file
        outfile_uv = merge_uv(infile, infile2, outfile_uv,'ua','va')
    input = os.path.join(dir_path, os.path.basename(outfile_uv))
    
    print("input file for wind is: ", input)
    input_basename = os.path.basename(input)

    # read data charactheristics
    data = data_indat(input,'cmip6')
    gridtype = data.get_grid_type()
    if ("va" not in data.vars) or ("ua" not in data.vars):
        raise Exception("Invalid input variable type. Please input eithe " +
                            "a combined uv file or both ua and va")


    print("Starting preprocessing.")
    
    print("Remove unnecessary variables.")
    
    input_e = input[:-3] + "_extr.nc"
    if "time_bnds" in data.vars:
        ncks = "time_bnds"
        if "lat_bnds" in data.vars:
            ncks += ",lat_bnds,lon_bnds"
        os.system("ncks -C -O -x -v " + ncks + " " + input + " " + input_e)
    elif "lat_bnds" in data.vars:
        os.system("ncks -C -O -x -v lat_bnds,lon_bnds " + input + " " + input_e)
    else:
        os.system("mv " + input + " " + input_e)
    os.system("rm " + dir_path+"/uv_merged.nc")

    # interpolate, if not gaussian
    input_eg = input_e[:-3] + "_gaussian.nc"
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")
        os.system("mv " + input_e + " " + input_eg)
    else:
    # regrid
        regrid_cmip6(input_e, input_eg)
    os.system("rm " + dir_path+"/uv_merged_extr.nc")

    # fill missing values, modified to be xarray for now - ASh
    input_egf = input_eg[:-3] + "_filled.nc"

    os.system("cdo setmisstoc,0 " + input_eg +
              " " + input_egf)
    
    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + input_egf)
    
        
    # print("Filled missing values, if any.")
    os.system("rm " + dir_path+"/uv_merged_extr_gaussian.nc")
    
    #### Files created so far - 
    # uv_merged.nc -- removed
    # uv_merged_extr.nc -- removed
    # uv_merged_extr_gaussian.nc -- removed
    # uv_merged_extr_gaussian_filled.nc --removed

    # renaming final uv file and cleaning up

    input_final = dir_path+"/uv_final.nc"
    os.system("mv " + input_egf + " " + input_final)
    
    # get final data info
    data = cmip6_indat(input_final)
    nx, ny = data.get_nx_ny()

    #return
    ################## END OF PROCESSING ####################################################################
    
    # Link data to TRACK directory
    print('Linking data to TRACK/indat')
    os.system("ln -fs '" + input_final + "' " + str(Path.home()) + "/TRACK/indat/uv_processed.nc")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK")

    # Years
    years = cdo.showyear(input=input_final)[0].split()
    print("Years: ", years)

    if not ysplit:
        years = ["all"]

    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    input_basename="uv_processed.nc"
    
    for year in years:
        print("Running TRACK for year: " + year + "...")

        # select year from data
        if ysplit:
            print("Splitting: " + year)
            year_file = input_basename[:-3] + "_" + year + ".nc"
            cdo.selyear(year, input="indat/"+input_basename, output="indat/"+year_file)
        else:
            year_file=input_basename

        # directory containing year specific track output
        c_input = hemisphere + "_" + year 

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # calculate vorticity from UV
        vor850_name = "vor850y"+year+".dat"
        calc_vorticity("indat/"+year_file, vor850_name, copy_file=False)

        fname = "T42filt_" + vor850_name + ".dat"
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
            "/;s/TRUNC/42/\" specfilt.in > spec_T42_nx" + nx + "_ny" + ny + ".in"
        line_2 = "bin/track.linux -i " + vor850_name + " -f y" + year + \
                    " < spec_T42_nx" + nx + "_ny" + ny + ".in"
        line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        line_4 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
            fname + " -f=y" + year + \
            " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
            " -n=1,62," + \
            str(nchunks) + " -o='" + outdir + \
            "' -r=RUN_AT_ -s=RUNDATIN.VOR"

        # setting environment variables
        os.environ["CC"] = "gcc"
        os.environ["FC"] = "gfortran"
        os.environ["ARFLAGS"] = ""
        os.environ["PATH"] += ":." 

        # executing the lines to run TRACK
        print("Spectral filtering...")
        os.system(line_1)
        os.system(line_2)
        os.system(line_3)

        print("Running TRACK...")
        os.system(line_4)

        print("Turning track output to netCDF...")

        ### extract start date and time from data file
        filename="indat/"+year_file
        sdate = subprocess.check_output(f"cdo showdate {filename} | head -n 1 | awk '{{print $1}}'", shell=True)
        sdate = sdate.decode('utf-8').strip()
        stime1 = subprocess.check_output(f"cdo showtime {filename} | head -n 1 | awk '{{print $1}}'", shell=True)
        stime1 = stime1.decode('utf-8').strip()
        
        # hotfix for start year before 1979
        if sdate[0]=='0':
            sdate='2'+sdate[1:]
        
        # convert initial date to string for util/count, in format YYYYMMDDHH
        timestring=sdate[0:4]+sdate[5:7]+sdate[8:10]+stime1[0:2]
        datetime=sdate[0:4]+'-'+sdate[5:7]+'-'+sdate[8:10]+' '+stime1[0:2]
        timedelta=6

        if shift:
            sdate=str(int(sdate[0:4])-1)+'-11-'+sdate[8:10]
            print('shifted start date :', sdate)
            timestring=sdate[0:4]+sdate[5:7]+sdate[8:10]+stime1[0:2]
            datetime=sdate[0:4]+'-'+sdate[5:7]+'-'+sdate[8:10]+' '+stime1[0:2]

        # tr2nc - turn tracks into netCDF files
        os.system("gunzip '" + outdir + "'/" + c_input + "/ff_trs_*")
        os.system("gunzip '" + outdir + "'/" + c_input + "/tr_trs_*")
        tr2nc_vor(outdir + "/" + c_input + "/ff_trs_pos", timestring, datetime, timedelta)
        tr2nc_vor(outdir + "/" + c_input + "/ff_trs_neg", timestring, datetime, timedelta)
        tr2nc_vor(outdir + "/" + c_input + "/tr_trs_pos", timestring, datetime, timedelta)
        tr2nc_vor(outdir + "/" + c_input + "/tr_trs_neg", timestring, datetime, timedelta)

        ### cleanup fortran files ###########################

        if True: ## Change to false to keep files for debugging
            os.system("rm outdat/specfil*")
            os.system("rm outdat/ff_trs*")
            os.system("rm outdat/tr_trs*")
            os.system("rm outdat/interp_*")
            os.system("rm indat/"+year_file)
            os.system("rm indat/"+fname)
            os.system("rm indat/"+vor850_name)
        # os.system("rm indat/calcvor_onelev_" + ext + ".in")
    
    return

def tr2nc_vor(input, timestring, datetime, timedelta):
    """
    Convert vorticity tracks from ASCII to NetCDF using TR2NC utility

    Parameters
    ----------

    input : string
        Path to ASCII file containing tracks

    """

    ## ASh -- to get the right date range, modify the tr2nc.meta.elinor file with the right details 
    
    fullpath = os.path.abspath(input)
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK/utils/TR2NC")
    os.system("sed -e \"s/START/"+ str(timestring) + "/;s/DATE_TIME/" + str(datetime) + "/;s/STEP/" + str(timedelta) + "/\" tr2nc.meta.elinor > tr2nc.meta.elinor_mod")
    os.chdir(str(Path.home()) + "/TRACK/utils/bin")
    os.system("tr2nc '" + fullpath + "' s ../TR2NC/tr2nc.meta.elinor_mod")
    os.chdir(cwd)
    return


def format_data(indir, outdir, create_seasonal=False):
    
    # custom function to extract out uv data from generic climate model data
    # changes variable names and adds units to match CMIP conventions

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    os.chdir(indir)
    files=os.listdir()

    for f in files[:]:
        if f[-2:]=='nc':
            print(f)
            if not (os.path.exists(outdir+'/corr_'+f)):
                dat=xr.open_dataset(f)
                dat=dat.transpose("time", "plev", "lat", "lon")
                dat.lon.attrs["units"]="degrees_east"; dat.lat.attrs["units"]="degrees_north"
                dat=dat[['U', 'V']].rename_vars({'U':'ua', 'V':'va'})#.drop_vars(['plev'])
                dat=dat.sel(plev=85000)
                dat.to_netcdf(outdir+'/corr_'+f, unlimited_dims={'time'})

    os.chdir('/gws/nopw/j04/csgap/abel')
    os.chdir(outdir)
    
    os.system('cdo mergetime *.nc combined.nc')

    # temporary - things are written manually here
    if create_seasonal:
        os.system('cdo selmon,5/9 combined.nc JJA_ext.nc')
        os.system('ncap2 -s \'time+=61\' combined.nc combined_shifted.nc')
        os.system('cdo selmon,1/5 combined_shifted.nc DJF_ext.nc')
        os.system('rm combined_shifted.nc')