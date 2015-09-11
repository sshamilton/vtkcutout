import numpy as np
import pyodbc, os
from jhtdb.models import Datafield
import time

class Cube:

    #  Express cubesize in [ x,y,z ]
    def __init__(self, cubecorner, cubesize, cubestep, filterwidth, components):
        """Create empty array of cubesize"""
        floatsize = 4
        # cubesize is in z,y,x 
        self.zlen, self.ylen, self.xlen = self.cubesize = [ cubesize[2],cubesize[1],cubesize[0] ] 
        self.xwidth, self.ywidth, self.zwidth = self.cubewidth = [cubesize[2], cubesize[1], cubesize[0]]
        self.xstart, self.ystart, self.zstart = self.corner = [ cubecorner[0], cubecorner[1], cubecorner[2]]
        self.xstep, self.ystep, self.zstep = self.step = [ cubestep[0], cubestep[1], cubestep[2]]
        self.filterwidth = 1 #default to one.
        self.components = 3 #set this!
        # RB this next line is not typed and produces floats.  Cube needs to be created in the derived classes
        #    self.data = np.empty ( self.cubesize )
        self.data = np.empty ([self.zwidth,self.ywidth,self.xwidth,components])
        #self.data.reshape()

    def getCubeData(self, ci, datafield, timestep):
        #get this from field data in db
        components = Datafield.objects.get(shortname=datafield).components
        #print("Set componets to ", components)
        #import pdb;pdb.set_trace()
        DBSTRING = os.environ['db_connection_string']
        conn = pyodbc.connect(DBSTRING, autocommit=True)
        cursor = conn.cursor()
        start = time.time()
        cursor.execute("{CALL turbdev.dbo.GetAnyCutout(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}",
            ci.dataset, datafield, timestep, self.xstart, self.ystart, self.zstart, self.xstep, self.ystep, self.zstep,1,1,self.xwidth,self.ywidth,self.zwidth,self.filterwidth,1)
        end = time.time()
        extime = end - start
        print ("DB Execution time: " + str(extime) + " seconds")
        print (ci.dataset, datafield, timestep, self.xstart, self.ystart, self.zstart, self.xstep, self.ystep, self.zstep,1,1,self.xwidth,self.ywidth,self.zwidth,self.filterwidth,1)

        row = cursor.fetchone()
        raw = row[0]
        part=0
        while(cursor.nextset()):           
            row = cursor.fetchone()
            raw = raw + row[0]
            part = part +1
            #print ("added part %d" % part)
            #print ("Part size is %d" % len(row[0]))
        #print ("Raw size is %d" % len(raw))
        #print ("components is %d" % components)
        self.data = np.frombuffer(raw, dtype=np.float32).reshape([self.zwidth/ci.zstep,self.ywidth/ci.ystep,self.xwidth/ci.xstep,components])
        print("shape = ")
        print (self.data.shape)

    def addData ( self, other ):
        """Add data to a larger cube from a smaller cube"""

        xoffset = other.xstart#*other.xlen
        yoffset = other.ystart#*other.ylen
        zoffset = other.zstart#*other.zlen
        #print ("Offsets: ", xoffset, yoffset, zoffset)
        #print("size", other.xlen, other.ylen, other.zlen)
        #zoffset:zoffset+other.zlen,yoffset:yoffset+other.ylen,xoffset:xoffset+other.xlen
        
        np.copyto ( self.data[zoffset:zoffset+other.zlen,yoffset:yoffset+other.ylen,xoffset:xoffset+other.xlen,0:self.components], other.data[:,:,:,:] )
        #import pdb;pdb.set_trace()
    def trim ( self, ci ):
        """Trim off the excess data"""
        self.data = self.data [ ci.zstart:ci.zstart+ci.zlen, ci.ystart:ci.ystart+ci.ylen, ci.xstart:ci.xstart+ci.xlen ]


