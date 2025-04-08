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

def run_composite(track_dir, data_dir, filetype='ff_trs_pos', hemisphere='NH'):

    ## get list of tracks

    time_grp=[]
    lat_grp=[]
    lon_grp=[]
    angle_grp=[]
    v_sys=[]
    u_sys=[]
    int_grp=[]

    fig = plt.figure(figsize=(12,5))
        
    ax = fig.add_subplot(111,projection=ccrs.PlateCarree(central_longitude=270))
    ax.coastlines()

    filelist=glob.glob(track_dir+'/'+hemisphere+'*')

    for f in filelist[:]:
        tracks=xr.open_dataset(f+'/'+filetype+'.nc')
        point_count=np.insert(np.cumsum(tracks['NUM_PTS'].values[:]),0,0)

        for i in range(len(point_count)-1):
        
            start=point_count[i]; end=point_count[i+1]
            time_tr=tracks['time'].values[start:end]
            lat_tr=tracks['latitude'].values[start:end]
            lon_tr=tracks['longitude'].values[start:end]
            int_tr=tracks['curvature_vorticity'].values[start:end]
            mx=(np.argmax(int_tr))
            mx_val=np.max(int_tr)
    
            if mx_val>15e-05 and len(time_tr)>16:
                int_grp.append(mx_val)
            
                lon_v=R*np.radians(lon_tr[1:]-lon_tr[:-1])*np.cos(np.radians(lat_tr[:-1]))/(6*3600)
                lat_v=R*np.radians(lat_tr[1:]-lat_tr[:-1])/(6*3600)
                
                angle=np.degrees(np.arctan2(lat_v, lon_v))
                
                angle=np.pad(angle, 1, mode='edge')[1:]
                lon_v=np.pad(lon_v, 1, mode='edge')[1:]
                lat_v=np.pad(lat_v, 1, mode='edge')[1:]
                
                time_grp.append(time_tr[mx])
                lat_grp.append(lat_tr[mx])
                lon_grp.append(lon_tr[mx])
                angle_grp.append(angle[mx])
                v_sys.append(lat_v[mx])
                u_sys.append(lon_v[mx])
    
                if np.min(lon_tr[1:]-lon_tr[:-1])<-180:
                    lon_tr=rewrap(lon_tr)
    
                plt.plot(lon_tr, lat_tr, transform=ccrs.PlateCarree(),color='black', linestyle='--', linewidth=0.7, zorder=0)
                plt.scatter(lon_tr[mx], lat_tr[mx], marker='x', s=25, transform=ccrs.PlateCarree(), color='black',zorder=1)
                plt.scatter(lon_tr[0], lat_tr[0], s=5, transform=ccrs.PlateCarree(), color='black',zorder=3)

    ax.set_extent([-179, 179, -60, 90], crs=ccrs.PlateCarree())
    plt.savefig('/home/users/as7424/curr/plot.png')


    ## collect data for scalar fields

    lons=np.linspace(0,360,360)
    lats=np.linspace(90,75,40)

    lon_list=[]
    lat_list=[]
    for i in lons:
        for j in lats:
            lon_list.append(i)
            lat_list.append(j)
        
    lonref, latref= rotate_coord(0 ,0, lon_list, lat_list)
    
    sc_arr=scalar_composite(data_dir, time_grp, lat_grp, lon_grp, angle_grp)
    
    fig = plt.figure(figsize=(7,5))
    plt.tricontourf(lonref, latref, np.mean(sc_arr[0],axis=0), cmap='Reds', levels=30)
    plt.colorbar()
    plt.axis('off')
    plt.savefig('/home/users/as7424/curr/temp.png')

    vmax=35
    fig = plt.figure(figsize=(7,5))
    plt.tricontourf(lonref, latref, np.mean(sc_arr[1],axis=0), cmap='RdBu_r', levels=30, vmin=-vmax, vmax=vmax)
    plt.colorbar()
    plt.axis('off')
    plt.savefig('/home/users/as7424/curr/lat_low.png')

    fig = plt.figure(figsize=(7,5))
    plt.tricontourf(lonref, latref, np.mean(sc_arr[2],axis=0), cmap='RdBu_r', levels=30, vmin=-vmax, vmax=vmax)
    plt.colorbar()
    plt.axis('off')
    plt.savefig('/home/users/as7424/curr/lat_mid.png')
    
    vec_arr=vector_composite(data_dir, time_grp, lat_grp, lon_grp, angle_grp, u_sys, v_sys)

def scalar_composite(data_dir, time_grp, lat_grp, lon_grp, angle_grp, rotate=False):

    lons=np.linspace(0,360,360)
    lats=np.linspace(90,75,40)

    lon_list=[]
    lat_list=[]
    for i in lons:
        for j in lats:
            lon_list.append(i)
            lat_list.append(j)
        
    lonref, latref= rotate_coord(0 ,0, lon_list, lat_list)

    arr1=[]
    arr2=[]
    arr3=[]
    
    for ind in range(len(time_grp)):
        
        time=get_date(time_grp[ind])
    
        ## locate file
        os.chdir(data_dir)
        part1=str(time)[:7]
        part2=str(int(str(time)[5:7])-1)
        part3=str(int(str(time)[:4])-1)+'-12'
        if len(part2)==1:
            part2=part1[:5]+'0'+part2
        else:
            part2=part1[:5]+part2
            
        filelist = glob.glob('*'+part1+'*')+glob.glob('*'+part2+'*')+glob.glob('*'+part3+'*')
    
        for e in filelist:
            data=xr.open_dataset(e)
            if time in data['time']:
                break
        
        data_temp=data.sel({'time':time})
        
        lonr_list=[]
        lon_list=[]
        lat_list=[]
        for i in lons:
            for j in lats:
                lon_list.append(i)
                lonr_list.append(i+angle_grp[ind])
                lat_list.append(j)

        if rotate:
            rlonr,rlatr = rotate_coord(lon_grp[ind],lat_grp[ind], lonr_list, lat_list)
        else:
            rlonr,rlatr = rotate_coord(lon_grp[ind],lat_grp[ind], lon_list, lat_list)
    
        x = xr.DataArray(rlonr, dims="points")
        y = xr.DataArray(rlatr, dims="points")

        arr1.append(pad_data(data_temp['T']).sel({'plev':95000}).interp(lat=y, lon=x, method='linear').values[:])
        arr2.append(pad_data(data_temp['DTCOND']).sel({'plev':slice(94000,110000)}).interp(lat=y, lon=x, method='linear').mean(dim='plev').values[:]*86400)
        arr3.append(pad_data(data_temp['DTCOND']).sel({'plev':slice(50000,87000)}).interp(lat=y, lon=x, method='linear').mean(dim='plev').values[:]*86400)

        # print(data_temp['DTCOND'].plev)
        # print((pad_data(data_temp['DTCOND']).interp(lat=y, lon=x, method='linear')).mean('points')*86400)
        fig = plt.figure(figsize=(7,5))
        plt.plot((pad_data(data_temp['DTCOND']).interp(lat=y, lon=x, method='linear')).mean('points')*86400, data_temp['DTCOND'].plev)
        plt.gca().invert_yaxis()
        plt.xlabel('K/day')
        plt.xlabel('hPa')
        plt.savefig('/home/users/as7424/curr/'+str(ind)+'.png')
    
    return [arr1, arr2, arr3]

def vector_composite(data_dir, time_grp, lat_grp, lon_grp, angle_grp, u_sys, v_sys, rotate=False):

    lons=np.linspace(0,360,36)
    lats=np.linspace(90,75,10)

    lon_list=[]
    lat_list=[]
    for i in lons:
        for j in lats:
            lon_list.append(i)
            lat_list.append(j)
        
    lonref, latref= rotate_coord(0 ,0, lon_list, lat_list)

    arrx1=[]; arry1=[]

    for ind in range(len(time_grp)):
        
        time=get_date(time_grp[ind])
    
        ## locate file
        os.chdir(data_dir)
        part1=str(time)[:7]
        part2=str(int(str(time)[5:7])-1)
        part3=str(int(str(time)[:4])-1)+'-12'
        if len(part2)==1:
            part2=part1[:5]+'0'+part2
        else:
            part2=part1[:5]+part2
            
        filelist = glob.glob('*'+part1+'*')+glob.glob('*'+part2+'*')+glob.glob('*'+part3+'*')
    
        for e in filelist:
            data=xr.open_dataset(e)
            if time in data['time']:
                break
        
        data_temp=data.sel({'time':time})
        
        lonr_list=[]
        lon_list=[]
        lat_list=[]
        for i in lons:
            for j in lats:
                lon_list.append(i)
                lonr_list.append(i+angle_grp[ind])
                lat_list.append(j)

        if rotate:
            rlonr,rlatr = rotate_coord(lon_grp[ind],lat_grp[ind], lonr_list, lat_list)
        else:
            rlonr,rlatr = rotate_coord(lon_grp[ind],lat_grp[ind], lon_list, lat_list)
    
        x = xr.DataArray(rlonr, dims="points")
        y = xr.DataArray(rlatr, dims="points")

        ui=pad_data(data_temp['U']).sel({'plev':95000}).interp(lat=y, lon=x, method='linear')-u_sys[ind]
        vi=pad_data(data_temp['V']).sel({'plev':95000}).interp(lat=y, lon=x, method='linear')-v_sys[ind]
        angi=-angle_grp[ind]
        u_rot=ui*np.cos(np.radians(angi))-vi*np.sin(np.radians(angi))
        v_rot=ui*np.sin(np.radians(angi))+vi*np.cos(np.radians(angi))
        
        if rotate:
            arrx1.append(u_rot); arry1.append(v_rot)
        else:
            arrx1.append(ui); arry1.append(vi)

        # fig = plt.figure(figsize=(7,5))
        # plt.quiver(lonref, latref, arrx1[ind], arry1[ind])
        # plt.axis('off')
        # plt.savefig('/home/users/as7424/curr/'+str(ind)+'.png')
        
    return [arrx1, arry1]
        
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