import os
from cdo import *
import matplotlib.pyplot as plt
import glob
import xarray as xr
import cartopy.crs as ccrs
import numpy as np
import cftime

cdo = Cdo()
R=6378*1000

__all__ = ['run_composite']

def run_composite(track_dir, data_dir, cyclones=True, hemisphere='NH'):

    if (cyclones==True and hemisphere=='NH') or (cyclones==False and hemisphere=='SH'):
        filetype='ff_trs_pos'
    else:
        filetype='ff_trs_neg'
    ## get list of tracks

    max_all=[]
    max_arr=[]
    max_loc=[]
    len_arr=[]
    vor_arr=[]
    time_arr=[]
    lon_arr=[]
    lat_arr=[]
    lat_gen=[]
    lat_max=[]
    lat_lys=[]

    filelist=glob.glob(track_dir+'/'+hemisphere+'*')

    for f in filelist[:]:
        tracks=xr.open_dataset(f+'/'+filetype+'.nc')

        point_count=np.insert(np.cumsum(tracks['NUM_PTS'].values[:]),0,0)
        
        for i in range(len(point_count)-1):
        # for i in range(100,500):
            
            start=point_count[i]; end=point_count[i+1]
            time_tr=tracks['time'].values[start:end]
            lat_tr=tracks['latitude'].values[start:end]
            lon_tr=tracks['longitude'].values[start:end]
            int_tr=tracks['curvature_vorticity'].values[start:end]
            mx=(np.argmax(int_tr))
            mx_val=np.max(int_tr)
            mid=str(time_tr[int(len(time_tr)/2)])[5:7]

            if len(time_tr)>16 and np.all(abs(lat_tr)>30) and np.all(abs(lat_tr)<80):

                max_all.append(mx_val)

    thresh = np.quantile(max_all, [0, 1])
    
    for f in filelist[:]:
        tracks=xr.open_dataset(f+'/'+filetype+'.nc')

        point_count=np.insert(np.cumsum(tracks['NUM_PTS'].values[:]),0,0)
        
        for i in range(len(point_count)-1):
        # for i in range(100,500):
            
            start=point_count[i]; end=point_count[i+1]
            time_tr=tracks['time'].values[start:end]
            lat_tr=tracks['latitude'].values[start:end]
            lon_tr=tracks['longitude'].values[start:end]
            int_tr=tracks['curvature_vorticity'].values[start:end]
            mx=(np.argmax(int_tr))
            mx_val=np.max(int_tr)
            mid=str(time_tr[int(len(time_tr)/2)])[5:7]
            
            if mx_val>thresh[0] and mx_val<thresh[1] and len(time_tr)>16 and np.all(abs(lat_tr)>30) and np.all(abs(lat_tr)<80):   

                lat_gen.append(lat_tr[0])
                lat_lys.append(lat_tr[-1])
                lat_max.append(lat_tr[mx])
                max_arr.append(mx_val)
                len_arr.append(len(time_tr))
                    
                vor_arr.append(int_tr)
                time_arr.append(time_tr)
                max_loc.append(mx)
                lon_arr.append(lon_tr)
                lat_arr.append(lat_tr)
    
    grp_arr=[]
    grp_time=[]
    grp_lat=[]
    grp_lon=[]
    time_list=range(-10,11)
        
    for e in range(len(vor_arr[:])):
        arr_temp=[]
        time_temp=[]
        lat_temp=[]
        lon_temp=[]
        
        for i in time_list:
            if max_loc[e]+i>0 and max_loc[e]+i<len(vor_arr[e]):
                arr_temp.append(vor_arr[e][max_loc[e]+i]*1e5)
                time_temp.append(time_arr[e][max_loc[e]+i])
                lat_temp.append(lat_arr[e][max_loc[e]+i])
                lon_temp.append(lon_arr[e][max_loc[e]+i])
            else:
                arr_temp.append(np.nan)
                time_temp.append(np.nan)
                lat_temp.append(np.nan)
                lon_temp.append(np.nan)

        # plt.plot(np.array(time_list)*6, arr_temp, color="k", alpha=0.05)
        grp_arr.append(arr_temp)
        grp_time.append(time_temp)
        grp_lat.append(lat_temp)
        grp_lon.append(lon_temp)


    lons=np.linspace(0,360,36)
    lats=np.linspace(90,75,10)

    lon_list=[]
    lat_list=[]
    for i in lons:
        for j in lats:
            lon_list.append(i)
            lat_list.append(j)

    lonref, latref= rotate_coord(0 ,0, lon_list, lat_list)

    lat_grp=[]
    u_grp=[]
    v_grp=[]

    for e in range(len(grp_time)):
        # print(e)
        temp=[]
        tempu=[]
        tempv=[]
        for i in range(len(grp_time[e])):
            if i in [2, 6, 10, 14, 18]:
                if ~np.isnan(grp_time[e][i]):
                    temp.append(latent_prof(grp_time[e][i], grp_lon[e][i], grp_lat[e][i])[0])
                    tempu.append(latent_prof(grp_time[e][i], grp_lon[e][i], grp_lat[e][i])[1])
                    tempv.append(latent_prof(grp_time[e][i], grp_lon[e][i], grp_lat[e][i])[2])
                else:
                    temp.append(np.nan);tempu.append(np.nan);tempv.append(np.nan) 
        lat_grp.append(temp)
        u_grp.append(tempu)
        v_grp.append(tempv)

    time_list=[-48, -24, 0, 24, 48]
    lat_mean=[]
    u_mean=[]
    v_mean=[]
    for e in range(len(time_list)):
        temp_arr=[]
        tempu_arr=[]
        tempv_arr=[]
        for i in range(len(lat_grp)):
            if len(np.shape(lat_grp[i][e])):
                temp_arr.append(lat_grp[i][e])
                tempu_arr.append(u_grp[i][e])
                tempv_arr.append(v_grp[i][e])

        lat_mean.append(np.mean(temp_arr,axis=0))
        u_mean.append(np.mean(tempu_arr,axis=0))
        v_mean.append(np.mean(tempv_arr,axis=0))


    lat_mean=xr.DataArray(lat_mean,
                    dims=['time', 'points'])
    u_mean=xr.DataArray(u_mean,
                    dims=['time', 'points'])
    v_mean=xr.DataArray(v_mean,
                    dims=['time', 'points'])

    time_list=[-48, -24, 0, 24, 48]

    fig, axs = plt.subplots(2, 2)
    fig.set_size_inches(8, 6)

    for i, ax in enumerate(axs.flat):

        if i==1:
            im=ax.tricontourf(lonref, latref, lat_mean[i], levels=60, cmap='RdBu', vmax=0.5, vmin=-0.5)
            ax.quiver(lonref, latref, u_mean[i], v_mean[i])
        else:
            ax.tricontourf(lonref, latref, lat_mean[i], levels=60,cmap='RdBu', vmax=0.5, vmin=-0.5)
            ax.quiver(lonref, latref, u_mean[i], v_mean[i])
        
        ax.set_title('t = '+ str(time_list[i])+'h')
        # plt.colorbar()
        ax.axis('off')

    cbar=fig.colorbar(im, ax=axs.ravel().tolist())


def get_date(time):

    time_str=str(time)
    return (cftime.DatetimeNoLeap(int(time_str[2:4]), int(time_str[5:7]), int(time_str[8:10]), int(time_str[11:13]),
                                int(time_str[14:16]), int(time_str[17:19]), has_year_zero=True))

def latent_prof(t, ln_ctr, lt_ctr):

    time=get_date(t)

    ## locate file
    os.chdir('/home/requiem/pyTRACK-CMIP6/examples')

    data=xr.open_dataset('uv_test.nc')


    data_temp=data.sel({'time':time})
    
    data_temp = data_temp.pad(lon=200, mode='wrap')

    
    data_temp['lon'] = np.linspace(-250, 608.75, 688)

    lons=np.linspace(0,360,36)
    lats=np.linspace(90,75,10)
    
    lon_list=[]
    lat_list=[]
    for ln in lons:
        for lt in lats:
            lon_list.append(ln)
            lat_list.append(lt)
    
    rlonr,rlatr = rotate_coord(ln_ctr,lt_ctr, lon_list, lat_list)

    x = xr.DataArray(rlonr, dims="points")
    y = xr.DataArray(rlatr, dims="points")
    
    data_slice=data_temp['OMEGA'].sel({'plev':slice(85000, 85000)}).interp(lat=y, lon=x, method='linear').mean(dim='plev')
    u_slice=data_temp['U'].sel({'plev':slice(85000, 85000)}).interp(lat=y, lon=x, method='linear').mean(dim='plev')
    v_slice=data_temp['V'].sel({'plev':slice(85000, 85000)}).interp(lat=y, lon=x, method='linear').mean(dim='plev')
    # data_slice=data_temp.sel({'plev':85000}).interp(lat=y, lon=x, method='linear')
    
    # plt.quiver(lonref, latref, data_slice['U'], data_slice['V'])
    # plt.tricontourf(lonref, latref, data_slice, levels=60, cmap='Reds')
    # plt.colorbar()
    # plt.show()
    
    return [data_slice, u_slice, v_slice]

def rotate_coord(lon_center, lat_center, lon, lat, direction="r2n"):

    # lon_center: lon of cyclone center
    # lat_center: lat of cyclone cetner
    # lon, lat: 1d arrays of lon/lat grid to be rotated

    lon = np.array(lon)
    lat = np.array(lat)

    pole_longitude = lon_center
    pole_latitude = lat_center

    rotatedgrid = ccrs.RotatedPole(
        pole_longitude=pole_longitude, pole_latitude=pole_latitude
    )
    
    standard_grid = ccrs.Geodetic()

    if direction == "n2r":
        rotated_points = rotatedgrid.transform_points(standard_grid, lon, lat)
    elif direction == "r2n":
        rotated_points = standard_grid.transform_points(rotatedgrid, lon, lat)

    rlon, rlat, _ = rotated_points.T # rotated lon/lat grid

    return rlon, rlat

def get_date(time):

    time_str=str(time)
    return (cftime.DatetimeNoLeap(int(time_str[2:4]), int(time_str[5:7]), int(time_str[8:10]), int(time_str[11:13]),
                                int(time_str[14:16]), int(time_str[17:19]), has_year_zero=True))
    
def rewrap(x):
    return (x+180) % 360 - 180

### function might break depending on the data dimesions - ASh
def pad_data(dat):
    dat=dat.pad(lon=200, mode='wrap')
    dat['lon'] = np.linspace(-250, 608.75, 688)
    return dat