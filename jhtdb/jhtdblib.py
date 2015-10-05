#various definitions needed for the cutout service
import os
import pyodbc
import numpy as np

class CutoutInfo():
    def __init__(self):
        self.xstart = 0
        self.ystart = 0
        self.zstart = 0
        self.tstart = 0
        self.xlen = 1
        self.ylen = 1
        self.zlen = 1
        self.tlen = 1
        self.dataset = ""
        self.filetype = "hdf5" #can be vtk or hdf, default to hdf for now
        self.datafields = "" #list of datafields
        self.authtoken = "testing"
        self.xstep = 1
        self.ystep = 1
        self.zstep = 1
        self.tstep = 1
        self.filter = 1
        self.threshold = .5 #not a good default, but we need something here.  Should be overwritten by parsewebargs.


class JHTDBLib():
    
    def parsewebargs(self, webargs):
        cutout_info = CutoutInfo()
        w = webargs.split("/")
        cutout_info.dataset = w[1]
        cutout_info.authtoken= w[0]
        cutout_info.tstart = int(w[3].split(',')[0])
        cutout_info.tlen = int(w[3].split(',')[1])
        cutout_info.xstart = int(w[4].split(',')[0])
        cutout_info.xlen = int(w[4].split(',')[1])
        cutout_info.ystart = int(w[5].split(',')[0])
        cutout_info.ylen = int(w[5].split(',')[1])
        cutout_info.zstart = int(w[6].split(',')[0])
        cutout_info.zlen = int(w[6].split(',')[1])
        #For computed fields, set component to velocity.
        cfieldlist = w[2].split(",")
        if ((cfieldlist[0] == 'vo') or (cfieldlist[0] == 'qc') or (cfieldlist[0] == 'cvo') or (cfieldlist[0] == 'qcc')):
            cutout_info.datafields = w[2]
            
            if (len(cfieldlist) > 1):
                cutout_info.threshold = float(cfieldlist[1])
            else:
                print("Threshold not found, defaulting", cfieldlist)
                #Just in case the user didn't supply anything, we default to the values below.  These are unscientific--just a guess!
                if (w[2] == 'cvo'):
                    cutout_info.threshold = .6
                    cutout_info.filetype='vtk' #Might as well force this--we aren't doing contours with an HDF5 file.
                elif (w[2] =='qcc'):
                    cutout_info.filetype='vtk' #Might as well force this--we aren't doing contours with an HDF5 file.
                    cutout_info.threshold = .10
        else:
            cutout_info.datafields = w[2]
            print("Datafields: ", w[2])
        #Set file type
        if (len(w) >= (7)):
            cutout_info.filetype = w[7]
        #Look for step parameters
        if (len(w) > 9):
            s = w[8].split(",")
            cutout_info.tstep = s[0]
            cutout_info.xstep = float(s[1])
            cutout_info.ystep = float(s[2])
            cutout_info.zstep = float(s[3])
            cutout_info.filterwidth = w[9]
        
        return cutout_info

    def verify(self, authtoken):
        DBSTRING = os.environ['db_connection_string']
        conn = pyodbc.connect(DBSTRING, autocommit=True)
        cursor = conn.cursor()
        query = "SELECT uid, limit FROM turbinfo..users WHERE authkey = '" + str(authtoken) + "'"
        print ("Query: " + query)
        rows = cursor.execute(query).fetchall()
        if (len(rows) > 0):
            conn.close()
            return True
        else:
            conn.close()
            return False


    def getygrid(self):
        DBSTRING = os.environ['db_channel_string']
        conn = pyodbc.connect(DBSTRING, autocommit=True)
        cursor = conn.cursor()
        rows= cursor.execute("SELECT cell_index, value from grid_points_y ORDER BY cell_index").fetchall()
        length = len(rows)
        ygrid = np.zeros((length,1))
        for row in rows:
            ygrid[row.cell_index]=row.value
        conn.close()    
        return ygrid

    def createmortonindex(self, z,y,x):
        morton = 0
        mask = 0x001
        for i in range (0,20):
            morton += (x & mask) << (2*i)
            morton += (y & mask) << (2*i+1)
            morton += (z & mask) << (2*i+2)
            mask <<= 1
        return morton

