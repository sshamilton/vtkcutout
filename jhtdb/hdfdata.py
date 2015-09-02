from getdata import GetData
import tempfile
import h5py
import numpy as np

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
            fieldlist = list(ci.datafields)
            print("Fields: %d" % len(fieldlist))
            for field in fieldlist:
                for timestep in range(ci.tstart,ci.tstart+ci.tlen, ci.tstep):
                    #raw = GetData().getrawdata(ci, timestep, field)
                    #Do this if cutout is too large
                    raw=GetData().getcubedrawdata(ci, timestep, field)
                    data = np.frombuffer(raw, dtype=np.float32)
                    dsetname = field + '{0:05d}'.format(timestep*10)
                    #We need to get the component size from the database.  Hardcoded for three--fix this!
                    dset = fh.create_dataset(dsetname, (ci.zlen/ci.zstep,ci.ylen/ci.ystep,ci.xlen/ci.xstep,3), 
                        maxshape=(ci.zlen/ci.zstep,ci.ylen/ci.ystep,ci.xlen/ci.xstep,3),compression='gzip')
                    print ("Data length is: %s" %len(data))
                    data = data.reshape(ci.zlen/ci.zstep,ci.ylen/ci.ystep,ci.xlen/ci.xstep,3)
                    dset[...] = data
        except:
            fh.close()
            tmpfile.close()
            raise
        fh.close()
        tmpfile.seek(0)
        return tmpfile
