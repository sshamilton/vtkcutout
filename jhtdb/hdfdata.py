import tempfile
import h5py
import numpy as np
from jhtdb.models import Datafield
from getdata import GetData

class HDFData:

    def gethdf(self, ci):
        tmpfile = tempfile.NamedTemporaryFile()
        fh = h5py.File(tmpfile.name, driver='core', block_size=16, backing_store=True)

        try:
            contents = fh.create_dataset('_contents', (1,), dtype='int32')
            contents[0] = 1
            dataset = fh.create_dataset('_dataset', (1,), dtype='int32')
            dataset[0] = 4
            size = fh.create_dataset('_size', (4,), dtype='int32')
            size[...] = [ci.tlen,ci.xlen,ci.ylen,ci.zlen]
            start = fh.create_dataset('_start', (4,), dtype='int32')
            start[...] = [ci.tstart,ci.xstart, ci.ystart, ci.zstart]
            fieldlist = ci.datafields.split(",")
            print("Fields: %d" % len(fieldlist))
            for field in fieldlist:
                #We need to get the component size from the database.  
                print ("Field is: ", field)
                #import pdb;pdb.set_trace()   
                components = Datafield.objects.get(shortname=field).components
                for timestep in range(ci.tstart,ci.tstart+ci.tlen, ci.tstep):
                    #raw = GetData().getrawdata(ci, timestep, field)
                    #Cube up the data if it is this large.  Step gets messed up here, so don't cube if stepped.
                    if (ci.xlen > 255 and ci.ylen > 255 and ci.zlen > 255 and ci.xstep ==1 and ci.ystep ==1 and ci.zstep ==1):
                        #Do this if cutout is too large
                        data=GetData().getcubedrawdata(ci, timestep, field)
                    else:
                        data=GetData().getrawdata(ci, timestep, field)                        
                    # data = np.frombuffer(raw, dtype=np.float32)
                    dsetname = field + '{0:05d}'.format(timestep*10)
                    shape = [0]*3
                    shape[0] = (ci.zlen+ci.zstep-1)/ci.zstep                    
                    shape[1] = (ci.ylen+ci.ystep-1)/ci.ystep                    
                    shape[2] = (ci.xlen+ci.xstep-1)/ci.xstep                    
                    dset = fh.create_dataset(dsetname, (shape[0], shape[1], shape[2],components),
                        maxshape=(shape[0], shape[1], shape[2],components),compression='gzip')
                    print ("Data length is: %s" %len(data))                    
                    data = data.reshape(shape[0], shape[1], shape[2],components)
                    dset[...] = data
        except:
            fh.close()
            tmpfile.close()
            raise
        fh.close()
        tmpfile.seek(0)
        return tmpfile
