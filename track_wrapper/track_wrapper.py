import os
from cdo import *
from netCDF4 import Dataset
import cfgrib
from pathlib import Path
from math import ceil
import subprocess

cdo = Cdo()

__all__ = ['cmip6_indat', 'regrid_cmip6', 'setup_files', 'calc_vorticity',
           'track_mslp', 'track_uv_vor850', 'setup_tr2nc', 'track_era5_mslp',
           'track_era5_vor850', 'tr2nc_mslp', 'tr2nc_vor','track_stats','steps_to_dates']

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

def setup_files():
    """
    Configure template input files according to local machine setup 
    and copy into TRACK directory for use during preprocessing and tracking.
    """
    # check if TRACK is installed
    if os.path.isdir(str(Path.home()) + "/track-master") == False:
        raise Exception("track-master is not installed.")    
    
    # edit RUNDATIN files
    for var in ['MSLP', 'MSLP_A', 'VOR', 'VOR_A']:
        with open('track_wrapper/indat/template.' + var + '.in', 'r') as file:
            contents = file.read()
        contents = contents.replace('DIR', str(Path.home()))
        with open('track_wrapper/indat/RUNDATIN.' + var + '.in', "w") as file:
            file.write(contents)

    # copy files into local TRACK directory
    os.system("cp track_wrapper/trackdir/* " + str(Path.home()) +
                "/track-master/") # calcvor and specfilt files
    os.system("cp track_wrapper/indat/RUNDATIN.* " + str(Path.home()) +
                "/track-master/indat") # RUNDATIN files
    os.system("cp track_wrapper/data/* " + str(Path.home()) +
                "/track-master/data") # initial and adapt.dat0, zone.dat0
    os.system("cp track_wrapper/tr2nc_new.tar " + str(Path.home()) +
                "/track-master/utils") # for TR2NC setup
    return

def setup_tr2nc():
    """
    Set up and compile TR2NC for converting TRACK output to NetCDF.
    """
    # check if tr2nc_new.tar file exists
    if os.path.isfile(str(Path.home()) + "/track-master/utils/tr2nc_new.tar") == False:
        raise Exception("Please run the track_wrapper.setup_files function first.")

    os.system("cp track_wrapper/tr2nc_mslp.meta.elinor " + str(Path.home()) +
                "/track-master/utils")

    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/track-master/utils")
    os.system("mv TR2NC OLD_TR2NC")
    os.system("tar xvf tr2nc_new.tar")
    os.system("mv tr2nc_mslp.meta.elinor TR2NC/tr2nc_mslp.meta.elinor")

    os.environ["CC"] = "gcc"
    os.environ["FC"] = "gfortran"

    os.chdir(str(Path.home()) + "/track-master")
    os.system("make utils")

    os.chdir(cwd)
    return

def steps_to_dates(track_output_dir, filename):
    
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
    print(f"Time string of initial step is: {timestring}")

    # determine increment in hours
    timedelta=int(stime2[0:2])-int(stime1[0:2])
    print(f"Time incrment is {timedelta}h")

    # make subidrectories with dates
    os.system(f"mkdir -p {track_output_dir}/dates")

    # count command: [filname] [Lat.] [Lng.] [Rad.] [Genesis (0)/Lysis (1)/Passing(2)/Passing Time(3)/All Times(4)] [Negate (1)] [Start Time, YYYYMMDDHH] [tstep]
    tr_fname=f"{track_output_dir}/tr_trs_pos"
    os.system("gzip -d " + tr_fname + ".gz")
    count=str(Path.home()) + "/track-master/utils/bin/count " + tr_fname + " 0 0 5 4 0 "  + timestring + " " + str(timedelta)
    os.system(f"{count} ")

    ff_fname=f"{track_output_dir}/ff_trs_pos"
    os.system("gzip -d " + ff_fname + ".gz")
    count=str(Path.home()) + "/track-master/utils/bin/count " + ff_fname + " 0 0 5 4 0 "  + timestring + " " + str(timedelta)
    os.system(f"{count} ")

    # move files to dates subdirectories
    os.system(f"mv {tr_fname}.new {track_output_dir}/dates/tr_trs_pos")
    os.system(f"mv {ff_fname}.new {track_output_dir}/dates/ff_trs_pos")

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
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(file1)), 'temp_uv')
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
        track-master/indat directory.

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
                            "will be found in the track-master/indat directory.")

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

    # if copy_file == True: # copy input data to TRACK/indat directory

    #     os.system("cp " + uv_file + " " + str(Path.home()) + 
    #                 "/track-master/indat/" + tempname)
    # else: # if uv_file is already in the track-master/indat directory

    #     os.system("ln -fs " + uv_file + " " + str(Path.home()) + "/track-master/indat/" + tempname)
        
    os.chdir(str(Path.home()) + "/track-master") # change to track-master directory

    # generate input file and calculate vorticity using TRACK
    os.system("sed -e \"s/VAR1/"+ u_name + "/;s/VAR2/" + v_name + "/;s/NX/" +
                nx + "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile +
                "/\" calcvor_onelev.in > calcvor.test")
    os.system("bin/track.linux -i " + tempname + " -f y" + year + " < calcvor.test")

    os.chdir(cwd) # change back to working directory

    return

#
# =============
# RUNNING TRACK
# =============
#

def track_mslp(input, outdirectory, NH=True, netcdf=True, ysplit=False):
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

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.

    ysplit : boolean, default is false
        If true, splits the years into separate files for tracking.

    """
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    input_basename = os.path.basename(input)

    # files need to be moved to TRACK directory for TRACK to find them
    # copy data into TRACK indat directory
    tempname = "indat/temp_file.nc"
    os.system("ln -fs " + input + " " + str(Path.home()) + "/track-master/" +
              tempname)
    # os.system("rm " + filled)
    print("Data linked into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/track-master")

    data = cmip6_indat(tempname)

    if "psl" not in data.vars:
        raise Exception("Invalid input variable type. Please input CMIP6 psl file.")

    extr = tempname[:-3] + "_extr.nc"

    # remove unnecessary variables
    if "time_bnds" in data.vars:
        ncks = "time_bnds"
        if "lat_bnds" in data.vars:
            ncks += ",lat_bnds,lon_bnds"
        os.system("ncks -C -O -x -v " + ncks + " " + tempname + " " + extr)
    elif "lat_bnds" in data.vars:
        os.system("ncks -C -O -x -v lat_bnds,lon_bnds " + tempname + " " + extr)
    else:
        extr = tempname

    print("Starting preprocessing.")

    gridtype = data.get_grid_type()
    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")
        gridcheck = extr

    else:
    # regrid
        #gridcheck = tempname[:-3] + "_gaussian.nc"
        gridcheck = extr[:-3] + "_gaussian.nc"
        regrid_cmip6(extr, gridcheck)

    # fill missing values
    filled = gridcheck[:-3] + "_filled.nc"

    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + gridcheck +
              " " + filled)
    print("Filled missing values, if any.")

    # clean up if it was regridded and if variables were removed
    if gridtype != 'gridtype  = gaussian':
        #os.system("rm " + tempname[:-3] + "_gaussian.nc")
        os.system("rm " + extr[:-3] + "_gaussian.nc")
    if extr != tempname:
        os.system("rm " + extr)

    # get data info
    data = cmip6_indat(filled)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=filled)[0].split()

    ## GZ+
    if not ysplit:
        years = [years[-1]]
    ## GZ-
    print(years)
        
    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'

        # GZ+
        print(os.getcwd())
        if not ysplit:
            os.system("ln -fs " + str(Path.home()) + "/track-master/" + filled + " indat/" + year_file)
        else:
            cdo.selyear(year, input=filled, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)
        c_input = year + "_" + hemisphere + "_" + input_basename[:-3]

        # spectral filtering
        if int(ny) >= 96: # T63
            fname = "T63filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/63/\" specfilt_nc.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                        fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
                        " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                        "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

        else: # T42
            fname = "T42filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/42/\" specfilt_nc.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                        fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
                        " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                        "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

        line_2 = "bin/track.linux -i " + year_file + " -f y" + year + \
                    " < spec.test"
        line_4 = "rm outdat/specfil.y" + year + "_band000"

        # setting environment variables
        os.environ["CC"] = "gcc"
        os.environ["FC"] = "gfortran"
        os.environ["ARFLAGS"] = ""
        os.environ["PATH"] += ":." 

        # executing the lines to run TRACK
        print("Spectral filtering...")

        #print("line 1")
        os.system(line_1)
        #print("line 2")
        os.system(line_2)        
        #print("line 3")
        os.system(line_3)
        #print("line 4")
        os.system(line_4)

        print("Running TRACK...")

        os.system(line_5)


        print("Turning track output to netCDF...")
        if netcdf == True:
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "/" + c_input + "/ff_trs_neg.gz'")
            os.system("gunzip '" + outdir + "/" + c_input + "/tr_trs_neg.gz'")
            tr2nc_mslp(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_mslp(outdir + "/" + c_input + "/tr_trs_neg")

        # cleanup
        os.system("rm indat/" + year_file)        
        os.system("rm outdat/ff_trs.y" + year + ".nc")
        os.system("rm outdat/tr_trs.y" + year + ".nc")
        os.system("rm outdat/interp_th.y" + year)

    os.system("rm indat/" + fname)        
    os.system("rm " + filled)        
    os.system("rm " + tempname)
    os.chdir(cwd)

    return

def track_uv_vor850(infile, outdirectory, infile2='none', NH=True, netcdf=True, ysplit=False):
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

    """
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    if infile2 == 'none':
        input = infile

    else: # if U and V separate, merge into UV file
        merge_uv_CMIP6(infile, infile2, infile[:-3] + "_merged.nc")
        input = infile[:-3] + "_merged.nc"

    input_basename = os.path.basename(input)

    # copy data into TRACK indat directory
    ## files need to be moved to TRACK directory for TRACK to find them
    tempname = "indat/temp_file.nc"
    os.system("ln -fs " + input + " " + str(Path.home()) + "/track-master/" +
              tempname)

    print("Data linked into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/track-master")

    data = cmip6_indat(tempname)

    if ("va" not in data.vars) or ("ua" not in data.vars):
        raise Exception("Invalid input variable type. Please input either " +
                            "a combined uv file or both ua and va from CMIP6.")

    print("Starting preprocessing.")

    # remove unnecessary variables
    extr = tempname[:-3] + "_extr.nc"
    if "time_bnds" in data.vars:
        ncks = "time_bnds"
        if "lat_bnds" in data.vars:
            ncks += ",lat_bnds,lon_bnds"
        os.system("ncks -C -O -x -v " + ncks + " " + tempname + " " + extr)
    elif "lat_bnds" in data.vars:
        os.system("ncks -C -O -x -v lat_bnds,lon_bnds " + tempname + " " + extr)
    else:
        extr = tempname

    gridtype = data.get_grid_type()
    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")
        gridcheck = tempname

    else:
    # regrid
        gridcheck = tempname[:-3] + "_gaussian.nc"
        regrid_cmip6(tempname, gridcheck)

    # fill missing values
    filled = gridcheck[:-3] + "_filled.nc"
    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + gridcheck +
              " " + filled)
    print("Filled missing values, if any.")

    if gridtype != 'gridtype  = gaussian':
        os.system("rm " + tempname[:-3] + "_gaussian.nc")
    if extr != tempname:
        os.system("rm " + extr)

    # get data info
    data = cmip6_indat(filled)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=filled)[0].split()

    ## GZ+
    if ysplit:
        years = years[-1]
    ## GZ-
    
    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'
        # GZ+
        if ysplit:
            os.system("ln -fs " + filled + "indat/"+year_file)
        else:
            cdo.selyear(year, input=filled, output="indat/"+year_file)

            # cdo.selyear(year, input=filled, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # calculate vorticity from UV
        vor850name = "vor850_temp.dat"
        calc_vorticity("./indat/"+year_file, vor850name, copy_file=False)
        year_file = vor850name
        c_input = year + "_" + hemisphere + "_" + "_vor850_" + \
                    input_basename[:-3]

        # spectral filtering (vorticity)

        # GZ+:  Enforce vorticity tracking at T42 resolution
        
        # if int(ny) >= 96: # T63
        #     fname = "T63filt_" + year + ".dat"
        #     line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
        #                 "/;s/TRUNC/63/\" specfilt.in > spec.test"
        #     line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        #     # NH
        #     line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
        #                 fname + " -f=y" + year + \
        #                 " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
        #                 " -n=1,62," + str(nchunks) + " -o='" + outdir + \
        #                 "' -r=RUN_AT_ -s=RUNDATIN.VOR"
        # else: # T42
        # GZ-
        
        fname = "T42filt_" + year + ".dat"
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
            "/;s/TRUNC/42/\" specfilt.in > spec.test"
        line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        # NH
        line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
            fname + " -f=y" + year + \
            " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
            " -n=1,62," + \
            str(nchunks) + " -o='" + outdir + \
            "' -r=RUN_AT_ -s=RUNDATIN.VOR"

        line_2 = "bin/track.linux -i " + year_file + " -f y" + year + \
                    " < spec.test"
        line_4 = "rm outdat/specfil.y" + year + "_band000"

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
        os.system(line_4)

        print("Running TRACK...")

        os.system(line_5)

        # cleanup
        os.system("cp '" + filled + "' " + str(Path.home()) + "/track-master/" +
             tempname)
        os.system("rm '" + filled + "'")
        os.system("rm indat/"+year_file)

        if netcdf == True:
            print("Turning track output to netCDF...")
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "'/" + c_input + "/ff_trs_*")
            os.system("gunzip '" + outdir + "'/" + c_input + "/tr_trs_*")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_neg")

    os.system("rm " + tempname)
    os.chdir(cwd)
    return

def track_era5_mslp(input, outdirectory, NH=True, netcdf=True, ysplit=False):
    """
    Run TRACK on ERA5 mean sea level pressure data.

    Parameters
    ----------

    input : string
        Path to .nc file containing ERA5 mslp data.

    outdirectory : string
        Path of directory to output tracks to.

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.

    """
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    input_basename = os.path.basename(input)
    
    if input_basename[-3:] == ".nc":
        data = Dataset(input, 'r')
    elif input_basename[-4:] == ".grb":
        data = cfgrib.open_dataset(input)
    else:
        raise Exception("Invalid input file type. Please input a .nc or .grb file.")
    
    vars = [var for var in data.variables]
    nx = str(len(data.variables['longitude'][:]))
    ny = str(len(data.variables['latitude'][:]))

    if vars[-1] != "msl":
        raise Exception("Invalid input variable type. Please input ERA5 mslp file.")

    years = cdo.showyear(input=input)[0].split()

    # create link of data to TRACK indat directory
    os.system("ln -fs '" + input + "' " + str(Path.home()) + "/track-master/indat/" + input_basename)
    print("Data linked into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/track-master")

    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    if not ysplit:
        years=[years[-1]]

    # do tracking for one year at a time
    for year in years:
        # select year from data
        if ysplit:
            print("Splitting: " + year)
            year_file = input_basename[:-3] + "_" + year + ".nc"
            cdo.selyear(year, input="indat/"+input_basename, output="indat/"+year_file)
            c_input = year + "_" + hemisphere + "_" + input_basename[:-3]
        else:
            year_file=input_basename
            c_input = hemisphere + "_" + input_basename[:-3]
        
        # get number of timesteps and number of chunks for tracking
        ntime = int(len(data.variables['time'][:]))
        nchunks = ceil(ntime/62)

        # spectral filtering
        # NOTE: NORTHERN HEMISPHERE; add SH option???
        fname = "T63filt_" + c_input +  ".dat"
        
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                    "/;s/TRUNC/63/\" specfilt_nc.in > spec.test"
        line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        # NH
        line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                    fname + " -f=y" + year + \
                    " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
                    " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                    "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

        line_2 = "bin/track.linux -i " + year_file + " -f y" + year + \
                    " < spec.test"
        line_4 = "rm outdat/specfil.y" + year + "_band000"

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
        os.system(line_4)

        print("Running TRACK...")
        os.system(line_5)

        print("Converting steps to dates")
        steps_to_dates(outdir + "/" + c_input, "indat/"+year_file )

        # cleanup
        os.system("rm indat/"+year_file)
        os.system("rm indat/"+fname)

        if netcdf == True:
            print("Turning track output to netCDF...")
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "/" + c_input + "/ff_trs_neg.gz'")
            os.system("gunzip '" + outdir + "/" + c_input + "/tr_trs_neg.gz'")
            tr2nc_mslp(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_mslp(outdir + "/" + c_input + "/tr_trs_neg")

    os.chdir(cwd)

    return

def track_era5_vor850(input, outdirectory, infile2, NH=True, netcdf=True, ysplit=False):

    """
    Calculate 850 hPa vorticity from ERA5 horizontal wind velocity data
    and run TRACK.

    Parameters
    ----------

    input : string
        Path to .nc file containing combined ERA5 UV data

    outdirectory : string
        Path of directory to output tracks to

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.
        
    ysplit : boolean, default is false
        If true, splits the years into separate files for tracking.

    """
    outdir = os.path.abspath(outdirectory)
    

    if infile2 is not 'none':
        outfile_uv = input[:-3] + "_merged.nc"
        outfile_uv = outfile_uv.replace("_u_", "_uv_")
        outfile_uv, tempdir = merge_uv_ERA5(input, infile2, outfile_uv)
        input = os.path.join(tempdir, os.path.basename(outfile_uv))
            
    print("input file for wind is: ", input)
            
    input_basename = os.path.basename(input)

    if input_basename[-3:] == ".nc":
        data = Dataset(input, 'r')
    else:
        raise Exception("Invalid input file type. Please input a netCDF file.")
    
    vars = [var for var in data.variables]
    nx = str(len(data.variables['longitude'][:]))
    ny = str(len(data.variables['latitude'][:]))

    if (vars[-1] != "v") or (vars[-2] != "u"):
        raise Exception("Invalid input variable type. Please input a UV file from ERA5.")

    print("Starting preprocessing.")
    print("Filling missing values.")
    
    filled = input[:-3] + "_filled.nc"
    print("Filled file is: ", filled)
    if os.path.isfile(filled):
        print("Filled file already exists.")
    else:
        os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + input +
                " " + filled)
        print("Filled missing values, if any.")

    # create link of data to TRACK indat directory
    print('Linking data to TRACK/indat')
    os.system("ln -fs '" + filled + "' " + str(Path.home()) + "/track-master/indat/" + input_basename)

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/track-master")

    years = cdo.showyear(input=filled)[0].split()
    print("Years: ", years)
    
    if not ysplit:
        years = [years[-1]]
    
    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    for year in years:
        print("Running TRACK for year: " + year + "...")

        # select year from data
        if ysplit:
            print("Splitting: " + year)
            year_file = input_basename[:-3] + "_" + year + ".nc"
            cdo.selyear(year, input="indat/"+input_basename, output="indat/"+year_file)
            c_input = year + "_" + hemisphere + "_" + input_basename[:-3]
        else:
            year_file=input_basename
            c_input = hemisphere + "_" + input_basename[:-3]
        
        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # calculate vorticity from UV
        vor850_temp_name = "vor850_" + c_input + ".dat"
        calc_vorticity("indat/"+year_file, vor850_temp_name, copy_file=False, cmip6=False)
        
        # spectral filtering (vorticity)
        # GZ+:  Enforce vorticity tracking at T42 resolution
        # if int(ny) >= 96: # T63
        #     fname = "T63filt_" + year + ".dat"
        #     line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
        #                 "/;s/TRUNC/63/\" specfilt.in > spec.test"
        #     line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        #     # NH
        #     line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
        #                 fname + " -f=y" + year + \
        #                 " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
        #                 " -n=1,62," + str(nchunks) + " -o='" + outdir + \
        #                 "' -r=RUN_AT_ -s=RUNDATIN.VOR"
        # else: # T42
        # GZ-
        
        fname = "T42filt_" + vor850_temp_name + ".dat"
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
            "/;s/TRUNC/42/\" specfilt.in > spec.test"
        line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        # NH
        line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
            fname + " -f=y" + year + \
            " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
            " -n=1,62," + \
            str(nchunks) + " -o='" + outdir + \
            "' -r=RUN_AT_ -s=RUNDATIN.VOR"

        line_2 = "bin/track.linux -i " + vor850_temp_name + " -f y" + year + \
                    " < spec.test"
        line_4 = "rm outdat/specfil.y" + year + "_band000"

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
        os.system(line_4)

        print("Running TRACK...")
        os.system(line_5)

        print("Converting steps to dates")
        steps_to_dates(outdir + "/" + c_input, "indat/"+year_file)

        if netcdf == True:
            print("Turning track output to netCDF...")
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "'/" + c_input + "/ff_trs_*")
            os.system("gunzip '" + outdir + "'/" + c_input + "/tr_trs_*")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_neg")

        # cleanup
        os.system("rm indat/"+year_file)
        os.system("rm indat/"+fname)
        os.system("rm indat/"+vor850_temp_name)

    os.chdir(cwd)
    return


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
    os.chdir(str(Path.home()) + "/track-master/utils/bin")
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
    os.chdir(str(Path.home()) + "/track-master/utils/bin")
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
def track_stats(dirname,tracksname,ext):
    """
    dirname : string
        Path to directory containing years to be analysed
    tracksname : string
        Name of files to be used for tracking, e.g. tr_trs_pos
    """

    
    trackmaster=(str(Path.home()) + "/track-master/")
    utils=(str(Path.home()) + "/track-master/utils/")
    indat=(str(Path.home()) + "/track-master/indat/")
    outdat=(str(Path.home()) + "/track-master/outdat/")
    total=dirname + "/total/"

    if not os.path.exists(total):
        Path(total).mkdir(parents=True, exist_ok=True)

    # set stat file type depending on options (to be done)
    stat_file="STATS_LWA.in"
    
    # list available track files
    file_list = []
    for path in Path(dirname).rglob(tracksname):
        file_list.append(path)
    file_list.sort()
    ny=len(file_list)
    
    # create combine file
    os.chdir(dirname)
    cfile="combine_" + ext + ".in"
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
    os.chdir(total)
    command=utils + "bin/combine < " + dirname + "/" + cfile
    os.system(command)
    tr_combined=total+'/'+'combined_tr_trs'

    # update stats file
    stat_file1=stat_file+"_"+ext
    stat_out=indat+stat_file1
    with open(stat_out,'w') as outfile:
        subprocess.run(["sed","s:tr_trs:"+str(tr_combined)+":", indat + stat_file],stdout=outfile)

    # # update all_pr_in
    # allpr_out=total+"all_pr_in"
    # with open(allpr_out,'w') as outfile:
    #     subprocess.run(["sed","s:STAT_FILE:"+str(stat_file1)+":", indat + "all_pr_in"],stdout=outfile)
    # os.system("chmod u+x " + total + "all_pr_in")
    
    # run stats
    EXT="provaprova"
    os.chdir(trackmaster)
    os.system("bin/track.linux " + " -f" + ext + " < " + stat_out + " > prova ")
    #pstat="phase_trs." + ext  # phase speeds
    sstat="stat_trs." + ext
    sstat_nc="stat_trs." + ext + "_1.nc"
    sstat_scl="stat_trs_scl." + ext
    sstat_scl_nc="stat_trs_scl." + ext + "_1.nc"
    #sstatBIG="STATS_VOR850_EXT"

    #subprocess.run(["mv", outdat + pstat , total + pstat])
    subprocess.run(["mv", outdat + sstat , total + sstat])
    subprocess.run(["mv", outdat + sstat_nc , total + sstat_nc])
    subprocess.run(["mv", outdat + sstat_scl , total + sstat_scl])
    subprocess.run(["mv", outdat + sstat_scl_nc , total + sstat_scl_nc])
    #subprocess.run(["mv", outdat + sstatBIG , total + sstatBIG])
    subprocess.run(["rm", outdat + "initial." + ext])
    subprocess.run(["rm", outdat + "init_trs." + ext])
    subprocess.run(["rm", outdat + "disp_trs." + ext])
    subprocess.run(["rm", outdat + "ff_trs." + ext])
    subprocess.run(["rm", outdat + "ff_trs." + ext + '.nc'])
    
    return
    
    
