import pyodbc, os
from cube import Cube
from jhtdblib import CutoutInfo

class GetData:

    #For now we are only doing 1 timestep and one datafield at a time for simplicity.  
    #We can loop and build up a file with multiple timesteps and fields outside of this function  
    def getrawdata(self, ci, timestep, datafield):
        print ("xlen = %d", ci.xlen)
        cubesize  = [ci.xlen, ci.ylen, ci.zlen]
        filterwidth = ci.filter
        corner = [ci.xstart, ci.ystart, ci.zstart]
        step = [ci.xstep, ci.ystep, ci.zstep]
        cube = Cube(corner, cubesize,step, filterwidth, 3 )        
        cube.getCubeData(ci, datafield, timestep)
        print ("Cube size is: %d" % len(cube.data))
        return cube.data
    def getcubedrawdata(self, ci, timestep, datafield):
        #We need to chunk the data first    
        #cubesize 16
        fullcubesize  = [ci.xlen, ci.ylen, ci.zlen]
        filterwidth = ci.filter
        corner = [ci.xstart, ci.ystart, ci.zstart]
        step = [ci.xstep, ci.ystep, ci.zstep]
        fullcube = Cube(corner, fullcubesize,step, filterwidth, 3 )        

        cubedimension = 16
        cubesize = [cubedimension, cubedimension, cubedimension]
        for xcorner in range (ci.xstart,ci.xstart + ci.xlen, cubedimension):
            for ycorner in range (ci.ystart,ci.ystart + ci.ylen, cubedimension):
                for zcorner in range (ci.zstart,ci.zstart + ci.zlen, cubedimension):
                    print("Gettting cube: %d, %d, %d", xcorner, ycorner, zcorner)
                    corner = [xcorner, ycorner, zcorner]
                    step = [ci.xstep, ci.ystep, ci.zstep]
                    cube = Cube(corner, cubesize, step, filterwidth, 3)
                    cube.getCubeData(ci, datafield, timestep)
                    fullcube.addData(cube)
        fullcube.trim(ci)
        return fullcube.data
                    
