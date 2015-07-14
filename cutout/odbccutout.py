import vtk
from vtk.util import numpy_support
import pyodbc
import numpy as np
import django
import os

class OdbcCutout:
    def __init__(self):
        #initialize odbc
        self.db = None
        

    def getvtkimage(self, webargs):
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
        if ((w[2] == 'vo') or (w[2] == 'qc') or (w[2] == 'cvo') or (w[2] == 'qcc')):
            component = 'u'
        else:
            component = w[2]
        cursor.execute("{CALL turbdev.dbo.GetAnyCutout(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}",w[1], component, ts, xs, ys, zs, 1, 1,1,1,1,xe,ye,ze,1,1)
        row = cursor.fetchone()
        raw = row[0]
        data = np.frombuffer(raw, dtype=np.float32)
        vtkdata = numpy_support.numpy_to_vtk(data, deep=True, array_type=vtk.VTK_FLOAT)
        vtkdata.SetNumberOfComponents(3)
        vtkdata.SetName("Velocity")
        image = vtk.vtkImageData()
        image.SetExtent(xs, xs+xe-1, ys, ys+ye-1, zs, zs+ze-1)
        image.GetPointData().SetVectors(vtkdata)
        #See if we are doing anything extra
        computation = w[2]
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

    
