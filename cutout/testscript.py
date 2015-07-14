import vtk
from vtk.util import numpy_support
import pyodbc
import numpy as np

conn = pyodbc.connect('DSN=turbinfo;UID=turbquery;PWD=aa2465ways2k', autocommit=True)
cursor = conn.cursor()

ts = 0
te = 1
xs = 0
xe = 8
ys = 0
ye = 8
zs = 0
ze = 8

cursor.execute("{CALL mhddev_hamilton.dbo.GetAnyCutout(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)}",'isotropic1024coarse','u',ts,xs,ys,zs,1,1,1,1,te,xe,ye,ze,1,1)
row = cursor.fetchone()
raw = row[0]
data = np.frombuffer(raw, dtype=float32)
vtkdata = numpy_support.numpy_to_vtk(data, deep=True, array_type=vtk.VTK_FLOAT)
vtkdata.SetNumberOfComponents(3)
image = vtk.vtkImageData()
image.SetExtent(xs, xs+xe-1, ys, ys+ye-1, zs, zs+ze-1)
image.GetPointData().SetVectors(vtkdata)

writer = vtk.vtkXMLImageDataWriter()
writer.SetInputData(image)
writer.SetFileName('test.vti')
writer.Write()

