import pyodbc, os, math
from cube import Cube
from jhtdblib import CutoutInfo
from jhtdb.models import Datafield

class GetData:

    #For now we are only doing 1 timestep and one datafield at a time for simplicity.  
    #We can loop and build up a file with multiple timesteps and fields outside of this function  
    def getrawdata(self, ci, timestep, datafield):        
        cubesize  = [ci.zlen, ci.ylen, ci.xlen]
        filterwidth = ci.filter
        corner = [ci.xstart, ci.ystart, ci.zstart]
        step = [ci.xstep, ci.ystep, ci.zstep]
        cube = Cube(corner, cubesize,step, filterwidth, 3 )        
        cube.getCubeData(ci, datafield, timestep)
        return cube.data

    def getcubedrawdata(self, ci, timestep, datafield):
        #We need to chunk the data first    
        #cubesize 16
        cubedimension = 256
        components = Datafield.objects.get(shortname=datafield).components
        fullcubesize  = [math.ceil(float(ci.xlen)/float(cubedimension))*cubedimension, math.ceil(float(ci.ylen)/float(cubedimension))*cubedimension, math.ceil(float(ci.zlen)/float(cubedimension))*cubedimension]
        print ("Full cube size is: ", fullcubesize)
        filterwidth = ci.filter
        corner = [ci.xstart, ci.ystart, ci.zstart]
        step = [ci.xstep, ci.ystep, ci.zstep]
        fullcube = Cube(corner, fullcubesize,step, filterwidth, components )        
        cubesize = [cubedimension, cubedimension, cubedimension]
        for xcorner in range (ci.xstart,ci.xstart + ci.xlen, cubedimension):
            for ycorner in range (ci.ystart,ci.ystart + ci.ylen, cubedimension):
                for zcorner in range (ci.zstart,ci.zstart + ci.zlen, cubedimension):
                    print("Gettting cube: ", xcorner, ycorner, zcorner)
                    corner = [xcorner, ycorner, zcorner]
                    step = [ci.xstep, ci.ystep, ci.zstep]
                    cube = Cube(corner, cubesize, step, filterwidth, components)
                    cube.getCubeData(ci, datafield, timestep)
                    fullcube.addData(cube)
        print fullcube.data
        fullcube.trim(ci)
        return fullcube.data
                    
