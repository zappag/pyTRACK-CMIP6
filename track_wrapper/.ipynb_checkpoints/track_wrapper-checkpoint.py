import os
from cdo import *
from netCDF4 import Dataset
import cfgrib
from pathlib import Path
from math import ceil
import subprocess
import random

cdo = Cdo()

__all__ = ['cmip6_indat', 'regrid_cmip6', 'setup_files', 'calc_vorticity',
           'track_mslp', 'track_uv_vor850', 'setup_tr2nc',
           'tr2nc_mslp', 'tr2nc_vor','stats','steps_to_dates',
           'add_mean_field',]

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

def setup_files():
    """
    Configure template input files according to local machine setup 
    and copy into TRACK directory for use during preprocessing and tracking.
    """
    # check if TRACK is installed
    if os.path.isdir(str(Path.home()) + "/TRACK") == False:
        raise Exception("TRACK is not installed.")    
    
    # edit RUNDATIN files
    for var in ['MSLP', 'MSLP_A', 'VOR', 'VOR_A']:
        with open('track_wrapper/indat/template.' + var + '.in', 'r') as file:
            contents = file.read()
        contents = contents.replace('DIR', str(Path.home()))
        with open('track_wrapper/indat/RUNDATIN.' + var + '.in', "w") as file:
            file.write(contents)

    # copy files into local TRACK directory
    os.system("cp track_wrapper/trackdir/* " + str(Path.home()) +
                "/TRACK/") # calcvor and specfilt files
    os.system("cp track_wrapper/indat/RUNDATIN.* " + str(Path.home()) +
                "/TRACK/indat") # RUNDATIN files
    os.system("cp track_wrapper/indat/calcvor_onelev.in " + str(Path.home()) +
                "/TRACK/indat/.") # RUNDATIN files
    os.system("cp track_wrapper/data/* " + str(Path.home()) +
                "/TRACK/data") # initial and adapt.dat0, zone.dat0
    os.system("cp track_wrapper/tr2nc_new.tar " + str(Path.home()) +
                "/TRACK/utils") # for TR2NC setup
    return

def setup_tr2nc():
    """
    Set up and compile TR2NC for converting TRACK output to NetCDF.
    """
    # check if tr2nc_new.tar file exists
    if os.path.isfile(str(Path.home()) + "/TRACK/utils/tr2nc_new.tar") == False:
        raise Exception("Please run the track_wrapper.setup_files function first.")

    os.system("cp track_wrapper/tr2nc_mslp.meta.elinor " + str(Path.home()) +
                "/TRACK/utils")

    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK/utils")
    os.system("mv TR2NC OLD_TR2NC")
    os.system("tar xvf tr2nc_new.tar")
    os.system("mv tr2nc_mslp.meta.elinor TR2NC/tr2nc_mslp.meta.elinor")

    os.environ["CC"] = "gcc"
    os.environ["FC"] = "gfortran"

    os.chdir(str(Path.home()) + "/TRACK")
    os.system("make utils")

    os.chdir(cwd)
    return

def steps_to_dates(tr_fname, filename, hourshift=0, ERA5=False, track_mins=True):
    
    # read the the first date and time in the .nc file
    sdate = subprocess.check_output(f"cdo showdate {filename} | head -n 1 | awk '{{print $1}}'", shell=True)
    sdate = sdate.decode('utf-8').strip()
    
    # first hour
    stime1 = subprocess.check_output(f"cdo showtime {filename} | head -n 1 | awk '{{print $1}}'", shell=True)
    stime1 = stime1.decode('utf-8').strip()

    # second hour
    stime2 = subprocess.check_output(f"cdo showtime {filename} | head -n 1 | awk '{{print $2}}'", shell=True)
    stime2 = stime2.decode('utf-8').strip()

    # convert initial date to string for util/count, in format YYYYMMDDHH
    timestring=sdate[0:4]+sdate[5:7]+sdate[8:10]+stime1[0:2]
    timedelta=6
    
    # shift timestring by amount indicated in hourshift
    timestring = str(int(timestring) + hourshift).zfill(10)

    print(f"Time string of initial step is: {timestring}")

    # determine increment in hours
    if ERA5:
        timedelta=int(stime2[0:2])-int(stime1[0:2])
    else:
        timedelta=6
    print(f"Time incrment is {timedelta}h")

    # make subidrectories with dates
    track_output_dir=os.path.dirname(tr_fname)
    track_output_name=os.path.basename(tr_fname)
    os.system(f"mkdir -p {track_output_dir}/dates")

    # count command: [filname] [Lat.] [Lng.] [Rad.] [Genesis (0)/Lysis (1)/Passing(2)/Passing Time(3)/All Times(4)] [Negate (1)] [Start Time, YYYYMMDDHH] [tstep]
    if not os.path.exists(f"{tr_fname}") and os.path.exists(f"{tr_fname}.gz"):
        os.system("gzip -d " + tr_fname + ".gz")
    elif not os.path.exists(f"{tr_fname}") and not os.path.exists(f"{tr_fname}.gz"):
        raise Exception("missing track file for date conversione")

    count=str(Path.home()) + "/TRACK/utils/bin/count " + tr_fname + " 0 0 5 4 0 "  + timestring + " " + str(timedelta)
    os.system(f"{count} ")

    # move files to dates subdirectories
    os.system(f"mv {tr_fname}.new {track_output_dir}/dates/{track_output_name}")


    # if track_mins:
    #     print("converting mins (neg files) to dates")
    #     # count command: [filname] [Lat.] [Lng.] [Rad.] [Genesis (0)/Lysis (1)/Passing(2)/Passing Time(3)/All Times(4)] [Negate (1)] [Start Time, YYYYMMDDHH] [tstep]
    #     tr_fname=f"{track_output_dir}/tr_trs_neg"
    #     os.system("gzip -d " + tr_fname + ".gz")
    #     count=str(Path.home()) + "/TRACK/utils/bin/count " + tr_fname + " 0 0 5 4 0 "  + timestring + " " + str(timedelta)
    #     os.system(f"{count} ")

    #     ff_fname=f"{track_output_dir}/ff_trs_neg"
    #     os.system("gzip -d " + ff_fname + ".gz")
    #     count=str(Path.home()) + "/TRACK/utils/bin/count " + ff_fname + " 0 0 5 4 0 "  + timestring + " " + str(timedelta)
    #     os.system(f"{count} ")

    #     # move files to dates subdirectories
    #     os.system(f"mv {tr_fname}.new {track_output_dir}/dates/tr_trs_neg")
    #     os.system(f"mv {ff_fname}.new {track_output_dir}/dates/ff_trs_neg")
    # else:
    #     print("converting max (pos files) to dates")
    #     # count command: [filname] [Lat.] [Lng.] [Rad.] [Genesis (0)/Lysis (1)/Passing(2)/Passing Time(3)/All Times(4)] [Negate (1)] [Start Time, YYYYMMDDHH] [tstep]
    #     tr_fname=f"{track_output_dir}/tr_trs_pos"
    #     os.system("gzip -d " + tr_fname + ".gz")
    #     count=str(Path.home()) + "/TRACK/utils/bin/count " + tr_fname + " 0 0 5 4 0 "  + timestring + " " + str(timedelta)
    #     os.system(f"{count} ")

    #     ff_fname=f"{track_output_dir}/ff_trs_pos"
    #     os.system("gzip -d " + ff_fname + ".gz")
    #     count=str(Path.home()) + "/TRACK/utils/bin/count " + ff_fname + " 0 0 5 4 0 "  + timestring + " " + str(timedelta)
    #     os.system(f"{count} ")

    #     # move files to dates subdirectories
    #     os.system(f"mv {tr_fname}.new {track_output_dir}/dates/tr_trs_pos")
    #     os.system(f"mv {ff_fname}.new {track_output_dir}/dates/ff_trs_pos")

    return
#
# =======================
# PREPROCESSING FUNCTIONS
# =======================
#

def merge_uv_CMIP6(file1, file2, outfile):
    """
    Merge CMIP6 U and V files into a UV file.

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

    if data1.get_variable_type() == 'ua':
        u_file = file1
        v_file = file2

    elif data1.get_variable_type() == 'va':
        u_file = file2
        v_file = file1

    else:
        raise Exception("Invalid input variable type. Please input CMIP6 \
                            ua or va file.")

    cdo.merge(input=" ".join((u_file, v_file)), output=outfile)
    print("Merged U and V files into UV file.")
    return

def merge_uv_ERA5(file1, file2, outfile):
    """
    Merge CMIP6 U and V files into a UV file.

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

    if data1.get_variable_type() == 'u':
        u_file = file1
        v_file = file2

    elif data1.get_variable_type() == 'v':
        u_file = file2
        v_file = file1

    else:
        raise Exception("Invalid input variable type. Please input ERA5 \
                            u or v file.")

    # Create temporary directory one folder back
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(file1))), "temp_uv")
    print("Temporary directory for merged U and V files: ", temp_dir)

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Set the output file path in the temporary directory
    outfile = os.path.join(temp_dir, os.path.basename(outfile))

    # Check if the merged file already exists
    if os.path.isfile(outfile):
        print("Merged U and V file already exists, found file: ", outfile)
        
    elif os.path.isfile(outfile[:-3] + "_filled.nc"):
        print("Merged U and V file already exists, found file: ", outfile[:-3] + "_filled.nc")
        outfile = outfile[:-3] + "_filled.nc"
        
    else:
        print("Merging u&v files")
        cdo.merge(input=" ".join((u_file, v_file)), output=outfile)
        print("Merged U and V files into UV file named: ", outfile)
        
    return outfile, temp_dir

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

    # Create temporary directory one folder back
    #temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(file1))), "temp_uv")
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(file1)), "temp_uv")
    print("Temporary directory for merged U and V files: ", temp_dir)

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Set the output file path in the temporary directory
    outfile = os.path.join(temp_dir, os.path.basename(outfile))

    # Check if the merged file already exists
    if os.path.isfile(outfile):
        print("Merged U and V file already exists, found file: ", outfile)
        
    elif os.path.isfile(outfile[:-3] + "_filled.nc"):
        print("Merged U and V file already exists, found file: ", outfile[:-3] + "_filled.nc")
        outfile = outfile[:-3] + "_filled.nc"
        
    else:
        print("Merging u&v files")
        cdo.merge(input=" ".join((u_file, v_file)), output=outfile)
        print("Merged U and V files into UV file named: ", outfile)
        
    return outfile, temp_dir

def regrid_cmip6(input, outfile):
    """
    Detect grid of input CMIP6 data and regrid to gaussian grid if necessary.

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

def calc_vorticity(uv_file, outfile, copy_file=True, cmip6=True):
    """
    Use TRACK to calculate vorticity at 850 hPa from horizontal wind velocities.

    Parameters
    ----------

    uv_file : string
        Path to .nc file containing combined U and V data

    outfile : string
        Desired base name of .dat vorticity file that will be output into the
        TRACK/indat directory.

    ext: extension to avoid overwriting files

    copy_file : boolean, optional
        Whether or not the uv_file will be copied into the TRACK directory. This
        is not needed within the tracking functions, but needed for manual use.

    cmip6 : boolean, optional
        Whether or not input file is from CMIP6.

    """
    cwd = os.getcwd()

    # check if outfile is base name
    if (os.path.basename(outfile) != outfile) or (outfile[-4:] != '.dat'):
        raise Exception("Please input .dat file basename only. The output file " +
                            "will be found in the TRACK/indat directory.")

    # gather information about data
    year = cdo.showyear(input=uv_file)[0]

    if cmip6 == True:
        uv = cmip6_indat(uv_file)
        nx, ny = uv.get_nx_ny()
        u_name = uv.vars[-2]
        v_name = uv.vars[-1]

    else:
        uv = Dataset(uv_file, 'r')
        vars = [var for var in uv.variables]
        nx = str(len(uv.variables['longitude'][:]))
        ny = str(len(uv.variables['latitude'][:]))
        u_name = vars[-2]
        v_name = vars[-1]
    

    #tempname = "temp_file.nc"
    tempname = os.path.basename(uv_file)

    # removing .dat to create extension
    ext=outfile[7:-4]
    print(ext)


    # if copy_file == True: # copy input data to TRACK/indat directory

    #     os.system("cp " + uv_file + " " + str(Path.home()) + 
    #                 "/TRACK/indat/" + tempname)
    # else: # if uv_file is already in the TRACK/indat directory

    #     os.system("ln -fs " + uv_file + " " + str(Path.home()) + "/TRACK/indat/" + tempname)
        
    os.chdir(str(Path.home()) + "/TRACK") # change to TRACK directory

    # generate input file and calculate vorticity using TRACK
    os.system("sed -e \"s/VAR1/"+ u_name + "/;s/VAR2/" + v_name + "/;s/NX/" +
                nx + "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile +
                "/\" indat/calcvor_onelev.in > indat/calcvor_onelev_" + ext + ".in")
    os.system("bin/track.linux -i " + tempname + " -f " + ext + " < indat/calcvor_onelev_" + ext + ".in")
    # raise Exception("STOP")
    os.chdir(cwd) # change back to working directory

    print('vorticity calculation complete!')

    return

#
# =============
# RUNNING TRACK
# =============
#

def track_mslp(input, outdirectory, NH=True, ysplit=False, cmip6=True):
    """
    Run TRACK on CMIP6 sea level pressure data.

    Parameters
    ----------

    input : string
        Path to .nc file containing CMIP6 psl data

    outdirectory : string
        Path of directory to output tracks to

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    ysplit : boolean, default is false
        If true, splits the years into separate files for tracking.

    """

    # set relevant file paths
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    input_basename = os.path.basename(input)

    # read data charactheristics
    if cmip6:
        data = data_indat(input,'cmip6')
        if ("psl" not in data.vars):
            raise Exception("Invalid input variable type.")
    else:
        data = data_indat(input,'era5')
        if ("msl" not in data.vars):
            raise Exception("Invalid input variable type.")
    nx, ny = data.get_nx_ny()


    print("Starting preprocessing.")
    # remove unnecessary variables
    print("Remove unnecessary variables.")
    input_e = input[:-3] + "_extr.nc"

    # remove input_e if exists
    if os.path.isfile(input_e):
        os.system("rm " + input_e)

    if "time_bnds" in data.vars:
        ncks = "time_bnds"
        if "lat_bnds" in data.vars:
            ncks += ",lat_bnds,lon_bnds"
        os.system("ncks -C -O -x -v " + ncks + " " + input + " " + input_e)
    elif "lat_bnds" in data.vars:
        os.system("ncks -C -O -x -v lat_bnds,lon_bnds " + input + " " + input_e)
    else:
        input_e = input

    # interpolate, if not gaussian
    gridtype = data.get_grid_type()
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")
        input_eg = input_e
    else:
    # regrid
        input_eg = input_e[:-3] + "_gaussian.nc"
        regrid_cmip6(input_e, input_eg)

    # fill missing values
    input_egf = input_eg[:-3] + "_filled.nc"
    if os.path.isfile(input_egf):
        print("File without fillValue and missing_value already exists.")
    else:
        os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + input_eg +
              " " + input_egf)
        print("Filled/missing attributes removed") 

    # clean up 
    if os.path.isfile(input_e):
        os.system("rm " + input_e)

    if os.path.isfile(input_eg):
        os.system("rm " + input_eg)

    # Link data to TRACK directory
    print('Linking data to TRACK/indat')
    filled=input_egf
    os.system("ln -fs '" + filled + "' " + str(Path.home()) + "/TRACK/indat/" + input_basename)

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK")

    # Years
    years = cdo.showyear(input=filled)[0].split()
    print("Years: ", years)

    if not ysplit:
        years = [years[-1]]
    
    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"
    
    ext=str(random.randint(0, 100000))

    # do tracking for one year at a time
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
        c_input = hemisphere + "_" + year + "_T63mslp"

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # spectral filtering
        # NOTE: NORTHERN HEMISPHERE; add SH option???
        fname = "T63filt_" + ext +  ".dat"
        
        
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                    "/;s/TRUNC/63/\" specfilt_nc.in > spec_T63_nx" + nx + "_ny" + ny + ".in"
        line_2 = "bin/track.linux -i " + year_file + " -f " + ext + \
                    " < spec_T63_nx" + nx + "_ny" + ny + ".in"
        line_3 = "mv outdat/specfil." + ext + "_band001 indat/" + fname
        line_4 = "rm outdat/specfil." + ext + "_band000 outdat/interp_th." + ext
        # NH
        line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                    fname + " -f=" + ext + \
                    " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
                    " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                    "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

       
        

        # setting environment variables
        os.environ["CC"] = "gcc"
        os.environ["FC"] = "gfortran"
        os.environ["ARFLAGS"] = ""
        os.environ["PATH"] += ":." 

        # executing the lines to run TRACK
        print("Spectral filtering...")
        os.system(line_1)
        os.system(line_2)
        print(year_file)
        os.system(line_3)

        print("Running TRACK...")
        os.system(line_5)

        print("Converting steps to dates")
        
        # set track mins to True to convert only the minimum of mslp
        print(outdir + "/" + c_input + "/ff_trs_neg")
        steps_to_dates(outdir + "/" + c_input + "/ff_trs_neg", "indat/"+year_file)
        steps_to_dates(outdir + "/" + c_input + "/tr_trs_neg", "indat/"+year_file)

        # move .nc output to outdir
        os.system("mv outdat/ff_trs." + ext + ".nc " + outdir + "/" + c_input + "/ff_trs_neg.nc")
        os.system("mv outdat/tr_trs." + ext + ".nc " + outdir + "/" + c_input + "/tr_trs_neg.nc")
        
        # cleanup
        os.system(line_4)    
        os.system("rm indat/"+year_file)
        os.system("rm indat/"+fname)
            
    os.chdir(cwd)

    return


## GZ implement
def track_uv_vor850(infile, outdirectory, infile2='none', NH=True, ysplit=False, cmip6=True):
    """
    Calculate 850 hPa vorticity from CMIP6 horizontal wind velocity data
    and run TRACK.

    Parameters
    ----------

    infile : string
        Path to .nc file containing combined CMIP6 UV data

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

    cmip6: boolean, optional
        if True, input files are from CMIP6. If False, input files are from ERA5.
    """
    
    # convert to full path the output track directory
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    
    # check if U and V are in the same file, if not merge them in "input"
    if infile2 == 'none':
        input = infile

    else: # if U and V separate, merge into UV file
        outfile_uv = infile[:-3] + "_merged.nc"
        outfile_uv = outfile_uv.replace("_ua_", "_uv_").replace("_u_", "_uv_")
        if cmip6:
            outfile_uv, tempdir = merge_uv(infile, infile2, outfile_uv,'ua','va')
        else:
            outfile_uv, tempdir = merge_uv(infile, infile2, outfile_uv,'u','v')
        input = os.path.join(tempdir, os.path.basename(outfile_uv))
    
    print("input file for wind is: ", input)
    input_basename = os.path.basename(input)

    # read data charactheristics
    if cmip6:
        data = data_indat(input,'cmip6')
        if ("va" not in data.vars) or ("ua" not in data.vars):
            raise Exception("Invalid input variable type. Please input either " +
                                "a combined uv file or both ua and va from CMIP6.")
    else:
        data = data_indat(input,'era5')
        if ("v" not in data.vars) or ("u" not in data.vars):
            raise Exception("Invalid input variable type. Please input either " +
                                "a combined uv file or both ua and va from CMIP6.")
    nx, ny = data.get_nx_ny()


    print("Starting preprocessing.")
    # remove unnecessary variables
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
        input_e = input
  

    # interpolate, if not gaussian
    gridtype = data.get_grid_type()
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")
        input_eg = input_e
    else:
    # regrid
        input_eg = input_e[:-3] + "_gaussian.nc"
        regrid_cmip6(input_e, input_eg)

    # fill missing values
    input_egf = input_eg[:-3] + "_filled.nc"
    if os.path.isfile(input_egf):
        print("Filled file already exists.")
    else:
        os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + input_eg +
              " " + input_egf)
        print("Filled missing values, if any.")    

    # get data info
    data = cmip6_indat(input_egf)
    nx, ny = data.get_nx_ny()

    # clean up 
    if input_e != input:
        os.system("rm " + input_e)

    if input_eg != input_e:
        os.system("rm " + input_eg)
    

    # Link data to TRACK directory
    print('Linking data to TRACK/indat')
    filled=input_egf
    os.system("ln -fs '" + filled + "' " + str(Path.home()) + "/TRACK/indat/" + input_basename)

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK")

    # Years
    years = cdo.showyear(input=filled)[0].split()
    print("Years: ", years)

    if not ysplit:
        years = [years[-1]]
    
    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    ext=str(random.randint(0, 100000))

    # do tracking for one year at a time
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
        c_input = hemisphere + "_" + year + "_T42vor850"

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # calculate vorticity from UV
        vor850_temp_name = "vor850_" + ext + ".dat"
        calc_vorticity("indat/"+year_file, vor850_temp_name, copy_file=False, cmip6=cmip6)

        fname = "T42filt_" + vor850_temp_name + ".dat"
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
            "/;s/TRUNC/42/\" specfilt.in > spec_T42_nx" + nx + "_ny" + ny + ".in"
        line_2 = "bin/track.linux -i " + vor850_temp_name + " -f " + ext + \
            " < spec_T42_nx" + nx + "_ny" + ny + ".in"
        line_3 = "mv outdat/specfil." + ext + "_band001 indat/" + fname
        line_4 = "rm outdat/specfil." + ext + "_band000 outdat/interp_th." + ext
        # NH
        line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
            fname + " -f=" + ext + \
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
        os.system(line_5)
        
        print("Converting steps to dates")
        if NH==True:
            steps_to_dates(outdir + "/" + c_input + "/ff_trs_pos", "indat/"+year_file)
            steps_to_dates(outdir + "/" + c_input + "/tr_trs_pos", "indat/"+year_file)
        else:
            steps_to_dates(outdir + "/" + c_input + "/ff_trs_neg", "indat/"+year_file)
            steps_to_dates(outdir + "/" + c_input + "/tr_trs_neg", "indat/"+year_file)

        # move .nc output to outdir

        if NH==True:
            os.system("mv outdat/ff_trs." + ext + ".nc " + outdir + "/" + c_input + "/NH_ff_trs_pos.nc")
            os.system("mv outdat/tr_trs." + ext + ".nc " + outdir + "/" + c_input + "/NH_tr_trs_pos.nc")
        else:
            os.system("mv outdat/ff_trs." + ext + ".nc " + outdir + "/" + c_input + "/SH_ff_trs_neg.nc")
            os.system("mv outdat/tr_trs." + ext + ".nc " + outdir + "/" + c_input + "/SH_tr_trs_neg.nc")

        # cleanup TRACK
        os.system("rm indat/"+year_file)
        os.system("rm indat/"+fname)
        os.system("rm indat/"+vor850_temp_name)
        os.system(line_4)
        #os.system("rm outdat/initial.vor850_" + ext)
        os.system("rm indat/calcvor_onelev_" + ext + ".in")
        
    # if input was merged, remove the merged and filled files
    if infile2 != 'none':
        os.system("rm " + input)
    os.system("rm " + filled)

    os.chdir(cwd)
    return

# def track_era5_mslp(input, outdirectory, NH=True, netcdf=True, ysplit=False):
#     """
#     Run TRACK on ERA5 mean sea level pressure data.

#     Parameters
#     ----------

#     input : string
#         Path to .nc file containing ERA5 mslp data.

#     outdirectory : string
#         Path of directory to output tracks to.

#     NH : boolean, optional
#         If true, tracks the Northern Hemisphere. If false, tracks Southern
#         Hemisphere.

#     netcdf : boolean, optional
#         If true, converts TRACK output to netCDF format using TR2NC utility.

#     """
#     outdir = os.path.abspath(os.path.expanduser(outdirectory))
#     input_basename = os.path.basename(input)
    
#     if input_basename[-3:] == ".nc":
#         data = Dataset(input, 'r')
#     elif input_basename[-4:] == ".grb":
#         data = cfgrib.open_dataset(input)
#     else:
#         raise Exception("Invalid input file type. Please input a .nc or .grb file.")
    
#     vars = [var for var in data.variables]
#     nx = str(len(data.variables['longitude'][:]))
#     ny = str(len(data.variables['latitude'][:]))

#     if vars[-1] != "msl":
#         raise Exception("Invalid input variable type. Please input ERA5 mslp file.")

#     years = cdo.showyear(input=input)[0].split()

#     # create link of data to TRACK indat directory
#     os.system("ln -fs '" + input + "' " + str(Path.home()) + "/TRACK/indat/" + input_basename)
#     print("Data linked into TRACK/indat directory.")

#     # change working directory
#     cwd = os.getcwd()
#     os.chdir(str(Path.home()) + "/TRACK")

#     if NH == True:
#         hemisphere = "NH"
#     else:
#         hemisphere = "SH"

#     if not ysplit:
#         years=[years[-1]]

#     # do tracking for one year at a time
#     for year in years:
#         # select year from data
#         if ysplit:
#             print("Splitting: " + year)
#             year_file = input_basename[:-3] + "_" + year + ".nc"
#             cdo.selyear(year, input="indat/"+input_basename, output="indat/"+year_file)
#             c_input = year + "_" + hemisphere + "_" + input_basename[:-3]
#         else:
#             year_file=input_basename
#             c_input = hemisphere + "_" + input_basename[:-3]
        
#         # get number of timesteps and number of chunks for tracking
#         ntime = int(len(data.variables['time'][:]))
#         nchunks = ceil(ntime/62)

#         # spectral filtering
#         # NOTE: NORTHERN HEMISPHERE; add SH option???
#         fname = "T63filt_" + c_input +  ".dat"
#         ext=c_input
        
#         line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
#                     "/;s/TRUNC/63/\" specfilt_nc.in > spec.test"
#         line_3 = "mv outdat/specfil." + ext + "_band001 indat/" + fname
#         # NH
#         line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
#                     fname + " -f=" + ext + \
#                     " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
#                     " -n=1,62," + str(nchunks) + " -o='" + outdir + \
#                     "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

#         line_2 = "bin/track.linux -i " + year_file + " -f " + ext + \
#                     " < spec.test"
#         line_4 = "rm outdat/specfil." + ext + "_band000 outdat/interp_th." + ext

#         # setting environment variables
#         os.environ["CC"] = "gcc"
#         os.environ["FC"] = "gfortran"
#         os.environ["ARFLAGS"] = ""
#         os.environ["PATH"] += ":." 

#         # executing the lines to run TRACK
#         print("Spectral filtering...")
#         os.system(line_1)
#         os.system(line_2)
#         os.system(line_3)

#         print("Running TRACK...")
#         os.system(line_5)

#         print("Converting steps to dates")
        
#         # set track mins to True to convert only the minimum of mslp
#         steps_to_dates(outdir + "/" + c_input, "indat/"+year_file, track_mins=True)

#         # move .nc output to outdir
#         os.system("mv outdat/ff_trs." + ext + ".nc " + outdir + "/" + c_input + "/.")
#         os.system("mv outdat/tr_trs." + ext + ".nc " + outdir + "/" + c_input + "/.")
        
#         # cleanup
#         os.system(line_4)    
#         os.system("rm indat/"+year_file)
#         os.system("rm indat/"+fname)
        
#         # if netcdf == True:
#         #     print("Turning track output to netCDF...")
#         #     # tr2nc - turn tracks into netCDF files
#         #     os.system("gunzip '" + outdir + "/" + c_input + "/ff_trs_neg.gz'")
#         #     os.system("gunzip '" + outdir + "/" + c_input + "/tr_trs_neg.gz'")
#         #     tr2nc_mslp(outdir + "/" + c_input + "/ff_trs_neg")
#         #     tr2nc_mslp(outdir + "/" + c_input + "/tr_trs_neg")
#         #     print("mv outdat/ff_trs." + ext + ".nc " + outdir + "/" + c_input + "/.")

            
#     os.chdir(cwd)

#     return

# def track_era5_vor850(infile, outdirectory, infile2, NH=True, netcdf=True, ysplit=False):

#     """
#     Calculate 850 hPa vorticity from ERA5 horizontal wind velocity data
#     and run TRACK.

#     Parameters
#     ----------

#     input : string
#         Path to .nc file containing combined ERA5 UV data

#     outdirectory : string
#         Path of directory to output tracks to

#     NH : boolean, optional
#         If true, tracks the Northern Hemisphere. If false, tracks Southern
#         Hemisphere.

#     netcdf : boolean, optional
#         If true, converts TRACK output to netCDF format using TR2NC utility.
        
#     ysplit : boolean, default is false
#         If true, splits the years into separate files for tracking.

#     """
#     # convert to full path the output track directory
#     outdir = os.path.abspath(os.path.expanduser(outdirectory))
    
#     # check if U and V are in the same file, if not merge them
#     if infile2 == 'none':
#         input = infile
#     else:
#         outfile_uv = infile[:-3] + "_merged.nc"
#         outfile_uv = outfile_uv.replace("_u_", "_uv_").replace("_u_", "_uv_")
#         outfile_uv, tempdir = merge_uv_ERA5(infile, infile2, outfile_uv)
#         input = os.path.join(tempdir, os.path.basename(outfile_uv))
            
#     print("input file for wind is: ", input)
#     input_basename = os.path.basename(input)

#     # Read data carachteristics (NOTE: test with cmip6_indat)
#     if input_basename[-3:] == ".nc":
#         data = Dataset(input, 'r')
#     else:
#         raise Exception("Invalid input file type. Please input a netCDF file.")
    
#     vars = [var for var in data.variables]
#     nx = str(len(data.variables['longitude'][:]))
#     ny = str(len(data.variables['latitude'][:]))

#     if (vars[-1] != "v") or (vars[-2] != "u"):
#         raise Exception("Invalid input variable type. Please input a UV file from ERA5.")

    
    
    
    
#     print("Starting preprocessing.")
#     print("Filling missing values.")
    
#     filled = input[:-3] + "_filled.nc"
#     print("Filled file is: ", filled)
#     if os.path.isfile(filled):
#         print("Filled file already exists.")
#     else:
#         os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + input +
#                 " " + filled)
#         print("Filled missing values, if any.")

#     # create link of data to TRACK indat directory
#     print('Linking data to TRACK/indat')
#     os.system("ln -fs '" + filled + "' " + str(Path.home()) + "/TRACK/indat/" + input_basename)

#     # change working directory
#     cwd = os.getcwd()
#     os.chdir(str(Path.home()) + "/TRACK")

#     years = cdo.showyear(input=filled)[0].split()
#     print("Years: ", years)
    
#     if not ysplit:
#         years = [years[-1]]
    
#     if NH == True:
#         hemisphere = "NH"
#     else:
#         hemisphere = "SH"

#     # do tracking for one year at a time
#     for year in years:
#         print("Running TRACK for year: " + year + "...")

#         # select year from data
#         if ysplit:
#             print("Splitting: " + year)
#             year_file = input_basename[:-3] + "_" + year + ".nc"
#             cdo.selyear(year, input="indat/"+input_basename, output="indat/"+year_file)
#             c_input = year + "_" + hemisphere + "_" + input_basename[:-3]
#         else:
#             year_file=input_basename
#             c_input = hemisphere + "_" + input_basename[:-3]
        
#         # get number of timesteps and number of chunks for tracking
#         data = cmip6_indat("indat/"+year_file)
#         ntime = data.get_timesteps()
#         nchunks = ceil(ntime/62)

#         # calculate vorticity from UV
#         vor850_temp_name = "vor850_" + c_input + ".dat"
#         calc_vorticity("indat/"+year_file, vor850_temp_name, copy_file=False, cmip6=False)

#         # extensions
#         ext=c_input
        
#         # spectral filtering (vorticity)
#         # GZ+:  Enforce vorticity tracking at T42 resolution
#         # if int(ny) >= 96: # T63
#         #     fname = "T63filt_" + year + ".dat"
#         #     line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
#         #                 "/;s/TRUNC/63/\" specfilt.in > spec.test"
#         #     line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
#         #     # NH
#         #     line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
#         #                 fname + " -f=y" + year + \
#         #                 " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
#         #                 " -n=1,62," + str(nchunks) + " -o='" + outdir + \
#         #                 "' -r=RUN_AT_ -s=RUNDATIN.VOR"
#         # else: # T42
#         # GZ-
        
#         fname = "T42filt_" + vor850_temp_name + ".dat"
#         line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
#             "/;s/TRUNC/42/\" specfilt.in > spec.test"
#         line_3 = "mv outdat/specfil." + ext + "_band001 indat/" + fname
#         # NH
#         line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
#             fname + " -f=" + ext + \
#             " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
#             " -n=1,62," + \
#             str(nchunks) + " -o='" + outdir + \
#             "' -r=RUN_AT_ -s=RUNDATIN.VOR"

#         line_2 = "bin/track.linux -i " + vor850_temp_name + " -f " + ext + \
#                     " < spec.test"
#         line_4 = "rm outdat/specfil." + ext + "_band000 outdat/interp_th." + ext

#         # setting environment variables
#         os.environ["CC"] = "gcc"
#         os.environ["FC"] = "gfortran"
#         os.environ["ARFLAGS"] = ""
#         os.environ["PATH"] += ":." 

#         # executing the lines to run TRACK
#         print("Spectral filtering...")

#         os.system(line_1)
#         os.system(line_2)
#         os.system(line_3)

#         print("Running TRACK...")
#         os.system(line_5)

#         print("Converting steps to dates")
#         steps_to_dates(outdir + "/" + c_input, "indat/"+year_file)

#         # move .nc output to outdir
#         os.system("mv outdat/ff_trs." + ext + ".nc " + outdir + "/" + c_input + "/.")
#         os.system("mv outdat/tr_trs." + ext + ".nc " + outdir + "/" + c_input + "/.")

#         # if netcdf == True:
#         #     print("Turning track output to netCDF...")
#         #     # tr2nc - turn tracks into netCDF files
#         #     os.system("gunzip '" + outdir + "'/" + c_input + "/ff_trs_*")
#         #     os.system("gunzip '" + outdir + "'/" + c_input + "/tr_trs_*")
#         #     tr2nc_vor(outdir + "/" + c_input + "/ff_trs_pos")
#         #     tr2nc_vor(outdir + "/" + c_input + "/ff_trs_neg")
#         #     tr2nc_vor(outdir + "/" + c_input + "/tr_trs_pos")
#         #     tr2nc_vor(outdir + "/" + c_input + "/tr_trs_neg")

#         # cleanup TRACK
#         os.system("rm indat/"+year_file)
#         os.system("rm indat/"+fname)
#         os.system("rm indat/"+vor850_temp_name)
#         os.system(line_4)
#         os.system("rm outdat/initial.vor850_" + c_input)
        
#         # if input was merged, remove the merged and filled files
#         if infile2 != 'none':
#             os.system("rm " + outfile_uv)
#         os.system("rm " + filled)


#     os.chdir(cwd)
#     return


#
# ========================
# POSTPROCESSING FUNCTIONS
# ========================
#

def tr2nc_mslp(input):
    """
    Convert MSLP tracks from ASCII to NetCDF using TR2NC utility

    Parameters
    ----------

    input : string
        Path to ASCII file containing tracks

    """
    fullpath = os.path.abspath(input)
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK/utils/bin")
    os.system("tr2nc '" + fullpath + "' s ../TR2NC/tr2nc_mslp.meta.elinor")
    os.chdir(cwd)
    return

def tr2nc_vor(input):
    """
    Convert vorticity tracks from ASCII to NetCDF using TR2NC utility

    Parameters
    ----------

    input : string
        Path to ASCII file containing tracks

    """
    fullpath = os.path.abspath(input)
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK/utils/bin")
    os.system("tr2nc '" + fullpath + "' s ../TR2NC/tr2nc.meta.elinor")
    os.chdir(cwd)
    return

def find_directories_with_file(root_dir, file_name):
    matching_directories = []

    # Iterate over all subdirectories and files in the root directory
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if file_name in filenames:
            matching_directories.append(dirpath)

    return matching_directories

# Specify the root directory where you want to start the search
root_directory = '/path/to/root_directory'

# Specify the file name you are looking for
file_to_find = 'example.txt'

# Find directories containing the file
result = find_directories_with_file(root_directory, file_to_find)


## GZ+
def stats(dirname,tracksname,statstype="std",sy=None,ly=None,ext=None):
    """
    dirname : string
        Path to directory of tracking analysis (not individual years)
    tracksname : string
        Name of files to be used for tracking, e.g. tr_trs_pos/tr_trs_neg/ff_trs_pos_TP5mean/..
    statstype : string referring to the type of stats to be calculated. 
                - std:  track density/genesys/lysys....
                - addX: produce mean intensity of added field #X.
    sy : int
        Starting year (optional, take all years until ly if not specified)
    ly : int
        Last year (optional, take all years from sy if not specified)
    """
    
    # NOTE CHANGE NOMENCLATURE OF OUTPUT FILE TO INTENSITY (FOLLOWED BY NAME ADD FIELD)

    trackmaster=(str(Path.home()) + "/TRACK/")
    utils=(str(Path.home()) + "/TRACK/utils/")
    indat=(str(Path.home()) + "/TRACK/indat/")
    outdat=(str(Path.home()) + "/TRACK/outdat/")
    stats=dirname + "/stats/"

    if not os.path.exists(stats):
        Path(stats).mkdir(parents=True, exist_ok=True)

    # set stat file type depending on options (test)
    if statstype == "std":
        stat_file=f"{Path.home()}/pyTRACK_dev/track_wrapper/indat/STATS_standard_template.in"
    elif statstype[0:3] == "add":
        stat_file=f"{Path.home()}/pyTRACK_dev/track_wrapper/indat/STATS_addfld_template.in"
        fldnum=statstype[3]
    stat_file_name=os.path.basename(stat_file)

    # list available track files
    years_set = set()  # This will store unique years
    file_list = []
    for path in Path(dirname).glob(f"*/{tracksname}"):
        # extract year
        year=path.parts[-2].split('_')[-2]
        years_set.add(year)
        if sy is not None and int(year) < sy:
            continue
        if ly is not None and int(year) > ly:
            continue        
        file_list.append(path)
    file_list.sort()
    ny=len(file_list)
    
    if sy is  None:
        sy=int(min(years_set))
    if ly is None:
        ly=int(max(years_set))
    
    # sanity check all years are available
    if ly-sy+1 != ny:
        print("Missing years in directory for stats calculation")
        return

    # define extension
    ext=f"{statstype}_{sy}-{ly}"

    # create combine file
    os.chdir(dirname)
    cfile="combine_" + str(sy) + "-" + str(ly) + ".in"
    if os.path.exists(cfile):
        os.remove(cfile)

    cfile_obj=open(cfile,'w')
    cfile_obj.write(str(ny) + "\n")
    cfile_obj.write('2\n')
    cfile_obj.write('3\n')
    for path in file_list:
        cfile_obj.write(str(path) + "\n")
    cfile_obj.close()

    # run combine utility
    os.chdir(stats)
    command=utils + "bin/combine < " + dirname + "/" + cfile
    os.system(command)
    tr_combined=stats+'/'+'combined_tr_trs'
    tr_combined1=f"{stats}/combined_{tracksname}_{sy}-{ly}"
    os.system(f"mv {tr_combined} {tr_combined1}")

    # update stats file replacing string
    stat_file1=stat_file_name.replace("template",f"{tracksname}_{sy}-{ly}")
    stat_out=f"{indat}/{stat_file1}"
    with open(stat_out,'w') as outfile:
        if statstype == "std":
            subprocess.run(["sed","s:tr_trs:"+tr_combined1+":", stat_file],stdout=outfile)
        elif statstype == "add"+fldnum:
            subprocess.run(["sed","-e","s:tr_trs:"+tr_combined1+":","-e","s:fldnum:"+str(fldnum)+":", stat_file],stdout=outfile)

    
    # copy gridT63 file
    os.system(f"cp {Path.home()}/pyTRACK_dev/track_wrapper/indat/gridT63.dat {indat}")

    # # update all_pr_in
    # allpr_out=stats+"all_pr_in"
    # with open(allpr_out,'w') as outfile:
    #     subprocess.run(["sed","s:STAT_FILE:"+str(stat_file1)+":", indat + "all_pr_in"],stdout=outfile)
    # os.system("chmod u+x " + stats + "all_pr_in")

    # run stats
    os.chdir(trackmaster)
    os.system("bin/track.linux " + " -f " + ext + " < " + stat_out)

    # standard output files
    sstat="stat_trs." + ext
    sstat_nc="stat_trs." + ext + "_1.nc"
    sstat_scl="stat_trs_scl." + ext
    sstat_scl_nc="stat_trs_scl." + ext + "_1.nc"
    # renamed output files
    sstat1=sstat.replace("stat_trs",f"{tracksname}")
    sstat_nc1=sstat_nc.replace("stat_trs",f"{tracksname}")
    sstat_scl1=sstat_scl.replace("stat_trs",f"{tracksname}")
    sstat_scl_nc1=sstat_scl_nc.replace("stat_trs",f"{tracksname}")

    subprocess.run(["mv", outdat + sstat_nc , stats + sstat_nc1])
    subprocess.run(["mv", outdat + sstat_scl_nc , stats + sstat_scl_nc1])
    subprocess.run(["mv", dirname + "/" + cfile, stats + "/" + cfile])
    subprocess.run(["mv", stat_out, stats + "/" + stat_file1]) 


    subprocess.run(["rm", outdat + sstat])
    subprocess.run(["rm", outdat + sstat_scl])
    subprocess.run(["rm", outdat + "initial." + ext])
    subprocess.run(["rm", outdat + "init_trs." + ext])
    subprocess.run(["rm", outdat + "disp_trs." + ext])
    subprocess.run(["rm", outdat + "ff_trs." + ext])
    subprocess.run(["rm", outdat + "ff_trs." + ext + '.nc'])


def add_mean_field(infile, trackfile, radius, fieldname, scaling=1,hourshift=0, cmip6=True):
    # infile: precipitation or other field (.nc) to be associated to the tracks
    # trackfile: full path to track file to be used
    # fieldname: name of the field to be added in the input file (as in the .nc file)
    # radius: radius of the area in which the field is avaraged
    # scaling: scaling factor for the field to be added
    # hourshift: controls the time of the tracks dates/. They will normally take the time as in infile.nc, but you may want to check for consistency with previous track file, and shift accordingly. 
    # cmip6: True if input file is from CMIP6, False if from ERA5
     
    # check infile exists
    if not os.path.exists(infile):
        raise Exception("Input file does not exist.")
  
    # read data charactheristics
    if cmip6==True:
        data = data_indat(infile,'cmip6')
    else:
        data = data_indat(infile,'era5')

    if fieldname not in data.vars:
        raise Exception("Invalid input variable type. Please input a file with the desired field.")
    nx, ny = data.get_nx_ny()

    print("Starting preprocessing add field.")
    print("Remove unnecessary variables.")
    infile_e = infile[:-3] + "_extr.nc"

    if not os.path.exists(infile_e):
        if "time_bnds" in data.vars:
            ncks = "time_bnds"
            if "lat_bnds" in data.vars:
                ncks += ",lat_bnds,lon_bnds"
            os.system("ncks -C -O -x -v " + ncks + " " + infile + " " + infile_e)
        elif "lat_bnds" in data.vars:
            os.system("ncks -C -O -x -v lat_bnds,lon_bnds " + infile + " " + infile_e)
        else:
            infile_e = infile 

    # setup input file
    inputfile_template=f"{Path.home()}/pyTRACK_dev/track_wrapper/indat/template_addmean.in"
    
    # revise NY
    nx, ny = data.get_nx_ny()
    if data.has_nh_pole():
        # remove one latitude grid point from ny (string)
        ny = str(int(ny)-1)
        sed_nh_string="-e 's:NH:n:' "
    else:
        sed_nh_string="-e 's:NH:d:' "

    if data.has_sh_pole():
        ny = str(int(ny)-1)
        sed_sh_string="-e 's:SH:n:' "
    else:
        sed_sh_string="-e 's:SH:d:' "

    if data.has_equator():
        sed_eq_string="-e 's:equator:n:' "
        ny = str(int(ny)-1)
    else:
        sed_eq_string="-e ':equator:d:' "
    
    # prepare adapt input file
    radiusp=str(int(radius)+1)+".0"
    line1 = (
        f"sed -e 's:NX:{nx}:' "
        f"-e 's:NY:{ny}:' "
        f"-e 's:scaling:{scaling}:' "
        f"-e 's:radius:{radiusp} {radius}:' "
        f"{sed_nh_string}"
        f"{sed_sh_string}"
        f"{sed_eq_string}"
        f"-e 's:trackfilefullpath:{trackfile}:' "
        f"-e 's:ncfiletobeadded:{infile_e}:' "
        f"{inputfile_template} > addprec.in"
    )
    print(line1)

    ext=str(random.randint(0, 100000))
    line2=f"bin/track.linux -f {ext} < addprec.in"

    # run adapt input file
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK")

    os.system(line1)
    os.system(line2)

    # filenames
    # input track filename
    trackfilename=os.path.basename(trackfile)

    # manage output
    trackfileout=f"{trackfile}.{fieldname}{str(radius)[0]}mean"
    os.system(f"mv outdat/ff_trs.{ext}_addfld {trackfileout}")

     # output track filename and directory
    trackfileoutdir=os.path.dirname(trackfileout)
    trackfileoutname=os.path.basename(trackfileout)

    # steps to dates
    steps_to_dates(trackfileout, infile, hourshift=hourshift)

    # check dates consistency
    command = f"sed -n '6p' {trackfileoutdir}/dates/{trackfilename} | awk '{{print $1}}'"
    old_date=subprocess.check_output(command, shell=True, text=True).strip()
    command = f"sed -n '6p' {trackfileoutdir}/dates/{trackfileoutname} | awk '{{print $1}}'"
    new_date=subprocess.check_output(command, shell=True, text=True).strip()
    if old_date != new_date:
        print("WARNING: Dates in the track file and in the added field file do not match. Please check. Consider using the hourshift option.")

    # cleanup
    os.system(f"rm outdat/initial.{ext}")
    os.system(f"rm outdat/ff_trs.{ext}")
    os.system(f"rm outdat/ff_trs.{ext}.nc")

    return
    
    
