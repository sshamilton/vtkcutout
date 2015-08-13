import vtk
from vtk.util import numpy_support
import pyodbc
import numpy as np
import django
import os
import h5py
import tempfile

class OdbcCutout:
    def __init__(self):
        #initialize odbc
        self.db = None

    def gethdf(self, webargs):
        DBSTRING = os.environ['db_connection_string']
        conn = pyodbc.connect(DBSTRING, autocommit=True)
        cursor = conn.cursor()
        #url = "http://localhost:8000/cutout/getcutout/"+ token + "/" + dataset + "/" + datafield + "/" + ts + "," +te + "/" + xs + "," + xe +"/" + ys + "," + ye +"/" + zs + "," + ze
        w = webargs.split("/")
        ts = int(w[3].split(',')[0])
        te = int(w[3].split(',')[1])
        xs = int(w[4].split(',')[0])
        xe = int(w[4].split(',')[1])
        ys = int(w[5].split(',')[0])
        ye = int(w[5].split(',')[1])
        zs = int(w[6].split(',')[0])
        ze = int(w[6].split(',')[1])
        if ((w[2] == 'vo') or (w[2] == 'qc') or (w[2] == 'cvo') or (w[2] == 'qcc')):
            component = 'u'
        else:
            component = w[2]

        try:
            tmpfile = tempfile.NamedTemporaryFile()
            fh = h5py.File(tmpfile.name, driver='core', block_size=16, backing_store=True)
            contents = fh.create_dataset('_contents', (1,), dtype='int32')
            contents[0] = 1
            dataset = fh.create_dataset('_dataset', (1,), dtype='int32')
            dataset[0] = 4
            size = fh.create_dataset('_size', (4,), dtype='int32')
            size[...] = [te-ts,xe-xs,ye-ys,ze-zs]
            start = fh.create_dataset('_start', (4,), dtype='int32')
            start[...] = [ts,xs, ys, zs]
            fieldlist = list(component)
            for field in fieldlist:
                #Look for step parameters
                if (len(w) > 8):
                    step = True
                    s = w[8].split(",")
                    tstep = s[0]
                    xstep = float(s[1])
                    ystep = float(s[2])
                    zstep = float(s[3])
                    filterwidth = w[9]
		    print("Stepped: %s" %s[1])
		else:
                    print("len is %s" %len(w))
		    xstep = 1
		    ystep = 1
		    zstep = 1
		    tstep = 1
		    filterwidth = 1

                for timestep in range(ts,te, tstep):
                    cursor.execute("{CALL turbdev.dbo.GetAnyCutout(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}",w[1], field, timestep, xs, ys, zs, xstep, ystep, zstep,1,1,xe,ye,ze,filterwidth,1)
                    row = cursor.fetchone()
                    raw = row[0]
                    data = np.frombuffer(raw, dtype=np.float32)
                    dsetname = field + '{0:05d}'.format(timestep*10)
                    dset = fh.create_dataset(dsetname, ((ze-zs)/zstep,(ye-ys)/ystep,(xe-xs)/xstep,3), maxshape=((ze-zs)/zstep,(ye-ys)/ystep,(xe-xs)/xstep,3),compression='gzip')
		    print ("Data length is: %s" %len(data))
		    data = data.reshape((ze-zs)/zstep,(ye-ys)/ystep,(xe-xs)/xstep,3)
                    dset[...] = data
        except:
            fh.close()
            tmpfile.close()
            raise
        fh.close()
        tmpfile.seek(0)
        cursor.close()
        return tmpfile
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
        print ygrid
	return ygrid

    def numcomponents(self, component):
        #change this to get from DB in the future, using odbc connection
        if (component == 'u'):
            return 3
        elif (component == 'p'):
            return 1
        elif (component == 'b'):
            return 3 #check this
        elif (component == 'a'):
            return 1 #check this
        else:
            return 3

    def componentname(self, component):
        #change this to get from DB in the future, using odbc connection
        if (component == 'u'):
            return "Velocity"
        if (component == 'p'):
            return "Pressure"
        if (component == 'b'):
            return "Magnetic Field"
        if (component == 'a'):
            return "Vector Potential" 

    def getvtkimage(self, webargs, timestep):
        #Setup query
        DBSTRING = os.environ['db_connection_string']
        conn = pyodbc.connect(DBSTRING, autocommit=True)
        cursor = conn.cursor()
        #url = "http://localhost:8000/cutout/getcutout/"+ token + "/" + dataset + "/" + datafield + "/" + ts + "," +te + "/" + xs + "," + xe +"/" + ys + "," + ye +"/" + zs + "," + ze
        w = webargs.split("/")
        ts = int(w[3].split(',')[0])
        te = int(w[3].split(',')[1])
        xs = int(w[4].split(',')[0])
        xe = int(w[4].split(',')[1])
        ys = int(w[5].split(',')[0])
        ye = int(w[5].split(',')[1])
        zs = int(w[6].split(',')[0])
        ze = int(w[6].split(',')[1])
        #Look for step parameters
        if (len(w) > 8):
            step = True;
	    s = w[8].split(",")
            tstep = s[0]
            xstep = float(s[1])
            ystep = float(s[2])
            zstep = float(s[3])
            filterwidth = w[9]
        else:
            step = False;
	    xstep = 1
            ystep = 1
            zstep = 1
            filterwidth = 1
        if ((w[2] == 'vo') or (w[2] == 'qc') or (w[2] == 'cvo') or (w[2] == 'qcc')):
            component = 'u'
            computation = w[2] #We are doing a computation, so we need to know which one.
        else:
            component = w[2] #There could be multiple components, so we will have to loop
            computation = ''
        #Split component into list and add them to the image
        fieldlist = list(component)
        for field in fieldlist:
            cursor.execute("{CALL turbdev.dbo.GetAnyCutout(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}",w[1], field, timestep, xs, ys, zs, xstep, ystep, zstep, 1,1,xe,ye,ze,filterwidth,1)
            row = cursor.fetchone()
            raw = row[0]
            data = np.frombuffer(raw, dtype=np.float32)
            conn.close()
            vtkdata = numpy_support.numpy_to_vtk(data, deep=True, array_type=vtk.VTK_FLOAT)
            components = self.numcomponents(field)
            vtkdata.SetNumberOfComponents(components)
            vtkdata.SetName(self.componentname(field))
            image = vtk.vtkImageData()
            if (step):
                xes = int(xe)/int(xstep)-1
                yes = int(ye)/int(ystep)-1
                zes = int(ze)/int(zstep)-1
                image.SetExtent(xs, xs+xes, ys, ys+yes, zs, zs+zes)
                #image.SetExtent(ys, ys+yes, xs, xs+xes, zs, zs+zes)
		print("Step extent=" +str(xes))
		print("xs=" + str(xstep) + " ys = "+ str(ystep) +" zs = " + str(zstep))
            else:
                image.SetExtent(xs, xs+xe-1, ys, ys+ye-1, zs, zs+ze-1)
            image.GetPointData().SetVectors(vtkdata)

            if (step): #Magnify to original size
                image.SetSpacing(xstep,ystep,zstep)

        #Check if we need a rectilinear grid, and set it up if so.
        if (w[1] == 'channel'):
            ygrid = self.getygrid()
            print("Ygrid: ")
            print (ygrid)
            rg = vtk.vtkRectilinearGrid()
            rg.SetExtent(xs, xs+xe-1, ys, ys+ye-1, zs, zs+ze-1)
            rg.GetPointData().SetVectors(vtkdata)

            xg = np.arange(float(xs),float(xe))
            zg = np.arange(float(zs),float(ze))
            for x in xg:
                    xg[x] = 8*3.141592654/2048*x
            for z in zg:
                    zg[z] = 3*3.141592654/2048*z
            vtkxgrid=numpy_support.numpy_to_vtk(xg, deep=True,
                array_type=vtk.VTK_FLOAT)
            vtkzgrid=numpy_support.numpy_to_vtk(zg, deep=True,
                array_type=vtk.VTK_FLOAT)
            vtkygrid=numpy_support.numpy_to_vtk(ygrid,
                deep=True, array_type=vtk.VTK_FLOAT)
            rg.SetXCoordinates(vtkxgrid)
            rg.SetZCoordinates(vtkzgrid)
            rg.SetYCoordinates(vtkygrid)
            image = rg #we rewrite the image since we may be doing a
                       #computation below
        #See if we are doing a computation
        if (computation == 'vo'):
            vorticity = vtk.vtkCellDerivatives()
            vorticity.SetVectorModeToComputeVorticity()
            vorticity.SetTensorModeToPassTensors()
            vorticity.SetInputData(image)
            vorticity.Update()
            return vorticity.GetOutput()
        elif (computation == 'cvo'):
            vorticity = vtk.vtkCellDerivatives()
            vorticity.SetVectorModeToComputeVorticity()
            vorticity.SetTensorModeToPassTensors()
            vorticity.SetInputData(image)
            vorticity.Update()
            mag = vtk.vtkImageMagnitude()
            cp = vtk.vtkCellDataToPointData()
            cp.SetInputData(vorticity.GetOutput())
            cp.Update()
            image.GetPointData().SetScalars(cp.GetOutput().GetPointData().GetVectors())
            mag.SetInputData(image)
            mag.Update()
            c = vtk.vtkContourFilter()
            if (len(w) == 9):
                c.SetValue(0,float(w[8]))
            else:
                c.SetValue(0,.6)
            c.SetInputData(mag.GetOutput())
            c.Update()
            return c.GetOutput()
        elif (computation == 'qcc'):
            q = vtk.vtkGradientFilter()
            q.SetInputData(image)
            q.SetInputScalars(image.FIELD_ASSOCIATION_POINTS,"Velocity")
            q.ComputeQCriterionOn()
            if (len(w) == 9):
                q.SetComputeQCriterion(int(w[8]))
            else:
                q.SetComputeQCriterion(4.0)
            q.Update()

            mag = vtk.vtkImageMagnitude()
            cp = vtk.vtkCellDataToPointData()
            cp.SetInputData(q.GetOutput())
            cp.Update()
            image.GetPointData().SetScalars(cp.GetOutput().GetPointData().GetVectors())
            mag.SetInputData(image)
            mag.Update()
            c = vtk.vtkContourFilter()

            c.SetInputData(mag.GetOutput())
            c.Update()
            return c.GetOutput()

        else:
            return image

    
