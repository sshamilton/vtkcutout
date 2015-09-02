#various definitions needed for the cutout service

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


class JHTDBLib():
    
    def parsewebargs(self, webargs):
        cutout_info = CutoutInfo()
        w = webargs.split("/")
        cutout_info.dataset = w[1]
        cutout_info.tstart = int(w[3].split(',')[0])
        cutout_info.tlen = int(w[3].split(',')[1])
        cutout_info.xstart = int(w[4].split(',')[0])
        cutout_info.xlen = int(w[4].split(',')[1])
        cutout_info.ystart = int(w[5].split(',')[0])
        cutout_info.ylen = int(w[5].split(',')[1])
        cutout_info.zstart = int(w[6].split(',')[0])
        cutout_info.zlen = int(w[6].split(',')[1])
        #For computed fields, set component to velocity.
        if ((w[2] == 'vo') or (w[2] == 'qc') or (w[2] == 'cvo') or (w[2] == 'qcc')):
            cutout_info.datafields = 'u'
        else:
            cutout_info.datafields = w[2]
        #Look for step parameters
        if (len(w) > 9):
            s = w[8].split(",")
            cutout_info.tstep = s[0]
            cutout_info.xstep = float(s[1])
            cutout_info.ystep = float(s[2])
            cutout_info.zstep = float(s[3])
            cutout_info.filterwidth = w[9]
        
        return cutout_info


    def createmortonindex(self, z,y,x):
        morton = 0
        mask = 0x001
        for i in range (0,20):
            morton += (x & mask) << (2*i)
            morton += (y & mask) << (2*i+1)
            morton += (z & mask) << (2*i+2)
            mask <<= 1
        return morton

