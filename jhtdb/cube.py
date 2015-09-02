import numpy as np
import pyodbc, os

class Cube:

    #  Express cubesize in [ x,y,z ]
    def __init__(self, cubecorner, cubesize, cubestep, filterwidth, components):
        """Create empty array of cubesize"""
        floatsize = 4
        # cubesize is in z,y,x 
        self.zlen, self.ylen, self.xlen = self.cubesize = [ cubesize[2],cubesize[1],cubesize[0] ] 
        self.xwidth, self.ywidth, self.zwidth = self.cubewidth = [cubesize[2], cubesize[1], cubesize[0]]
        self.xstart, self.ystart, self.zstart = self.corner = [ cubecorner[1], cubecorner[1], cubecorner[2]]
        self.xstep, self.ystep, self.zstep = self.step = [ cubestep[1], cubestep[1], cubestep[2]]
        self.filterwidth = 1 #default to one.
        # RB this next line is not typed and produces floats.  Cube needs to be created in the derived classes
        #    self.data = np.empty ( self.cubesize )
        self.data = np.empty (self.cubesize)
        self.data.reshape(self.xwidth,self.ywidth,self.zwidth,components)

    def getCubeData(self, ci, datafield, timestep):
        DBSTRING = os.environ['db_connection_string']
        conn = pyodbc.connect(DBSTRING, autocommit=True)
        cursor = conn.cursor()
        cursor.execute("{CALL turbdev.dbo.GetAnyCutout(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}",
            ci.dataset, datafield, timestep, self.xstart, self.ystart, self.zstart, self.xstep, self.ystep, self.zstep,1,1,self.xwidth,self.ywidth,self.zwidth,self.filterwidth,1)

        print (ci.dataset, datafield, timestep, self.xstart, self.ystart, self.zstart, self.xstep, self.ystep, self.zstep,1,1,self.xwidth,self.ywidth,self.zwidth,self.filterwidth,1)

        row = cursor.fetchone()
        raw = row[0]
        part=0
        while(cursor.nextset()):           
            row = cursor.fetchone()
            raw = raw + row[0]
            part = part +1
            print ("added part %d" % part)
            print ("Part size is %d" % len(row[0]))
        print ("Raw size is %d" % len(raw))
        self.data = np.frombuffer(raw, dtype=np.float32)
        self.data.reshape(self.zwidth/ci.zstep,self.ywidth/ci.ystep,self.xwidth/ci.xstep,3)


    def addData ( self, other ):
        """Add data to a larger cube from a smaller cube"""

        xoffset = other.xstart*other.xlen
        yoffset = other.ystart*other.ylen
        zoffset = other.zstart*other.zlen
        print ("Offsets: ", xoffset, yoffset, zoffset)
        print("size", other.zlen, other.ylen, other.xlen)
        #zoffset:zoffset+other.zlen,yoffset:yoffset+other.ylen,xoffset:xoffset+other.xlen
        import pdb;pdb.set_trace()
        np.copyto ( self.data[zoffset:zoffset+other.zlen,yoffset:yoffset+other.ylen,xoffset:xoffset+other.xlen:3], other.data[:,:,:,:] )
      
    def trim ( self, ci ):
        """Trim off the excess data"""
        self.data = self.data [ ci.zstart:ci.zstart+ci.zlen, ci.ystart:ci.ystart+ci.ylen, ci.xstart:ci.xstart+ci.xlen ]


