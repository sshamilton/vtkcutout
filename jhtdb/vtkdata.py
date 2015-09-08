import getdata
import jhtdblib
from django.http import HttpResponse
from jhtdb.models import Datafield
from jhtdb.models import Dataset
from getdata import GetData
from django.core.files.temp import NamedTemporaryFile
import vtk
from vtk.util import numpy_support
import copy 
import zipfile

class VTKData:

    def expandcutout(self, ci, overlap):
        if (ci.xstart-overlap >=0):
            ci.xstart = ci.xstart-overlap
            ci.xlen = ci.xlen + overlap
        if (ci.ystart-overlap >=0):
            ci.ystart = ci.ystart-overlap
            ci.ylen = ci.ylen + overlap
        if (ci.zstart-overlap >=0):
            ci.zstart = ci.zstart-overlap
            ci.zlen = ci.zlen + overlap
        ds = Dataset.objects.get(dbname_text=ci.dataset)
        if (ds.xend > (ci.xstart+ci.xlen+overlap)):
            ci.xlen = ci.xlen + overlap
        if (ds.yend > (ci.ystart+ci.ylen+overlap)):
            ci.ylen = ci.ylen + overlap
        if (ds.zend > (ci.zstart+ci.zlen+overlap)):
            ci.zlen = ci.zlen + overlap
        else:
            print ("zend ztart zlen overlap: ", ds.zend, ci.zstart, ci.zlen, overlap)
        print ("z is", ci.zlen)
        return ci
    def getvtk(self, ci):
        
        firstval = ci.datafields.split(',')[0]
        if ((firstval == 'cvo') or (firstval == 'qcc')): #we may need to return a vtp file
            tmp = NamedTemporaryFile(suffix='.vtp')
            suffix = 'vtp'
            writer = vtk.vtkXMLPolyDataWriter()                         
            outfile = ci.filetype + '-contour'
        elif (ci.dataset == "channel"):
            tmp = NamedTemporaryFile(suffix='.vtr')
            suffix = 'vtr'
            writer = vtk.vtkXMLRectilinearGridWriter()
            outfile = 'cutout' + ci.filetype
        else:
            tmp = NamedTemporaryFile(suffix='.vti')
            suffix = 'vti'
            writer = vtk.vtkXMLImageDataWriter()                        
            outfile = 'cutout' + ci.filetype        
        writer.SetFileName(tmp.name)
        writer.SetCompressorTypeToZLib()
        writer.SetDataModeToBinary()
        #if multiple timesteps, zip the file.
        if (ci.tlen > 1):
            #Write each timestep to file and read it back in.  Seems to be the only way I know how to put all timesteps in one file for now
            #Create a timestep for each file and then send the user a zip file
            ziptmp = NamedTemporaryFile(suffix='.zip')
            z = zipfile.ZipFile(ziptmp.name, 'w')
            for timestep in range (ci.tstart,ci.tstart+ci.tlen, ci.tstep ):            
                image = self.getvtkdata(ci, timestep)
                writer.SetInputData(image)
                writer.SetFileName(tmp.name)                        
                writer.Write()
                #Now add this file to the zipfile
                z.write(tmp.name, 'cutout' + str(timestep) + '.' + suffix)
            z.close()
            ct = 'application/zip'
            suffix = 'zip'
            response = HttpResponse(ziptmp, content_type=ct)
            print("Zipping!")
        else:
            print("Single Timestep")
            image = self.getvtkdata(ci, ci.tstart)
            writer.SetInputData(image)
            writer.SetFileName(tmp.name)                        
            writer.Write()
            ct = 'data/vtk'
            response = HttpResponse(tmp, content_type=ct)
        response['Content-Disposition'] = 'attachment;filename=' +  outfile +'.' + suffix
        return response

    def getvtkdata(self, ci, timestep):
        firstval = ci.datafields.split(',')[0]
        overlap = 2
        print ("First: ", firstval)
        #import pdb;pdb.set_trace()
        if ((firstval == 'vo') or (firstval == 'qc') or (firstval == 'cvo') or (firstval == 'qcc')):
            datafields = 'u'
            
            computation = firstval #We are doing a computation, so we need to know which one.
            if ((firstval == 'cvo') or (firstval == 'qcc')):
                overlap = 2 #This appears to be what we need.  We need to verify this.
                #Save a copy of the original request
                oci = copy.deepcopy(ci)
                ci = self.expandcutout(oci, overlap) #Expand the cutout by the overlap
                print ("z is overlap:", ci.zlen)
                contour = True #We aren't using this yet.               
        else:
            datafields = ci.datafields #There could be multiple components, so we will have to loop
            computation = ''
        #Split component into list and add them to the image

        #Check to see if we have a value for vorticity or q contour
        fieldlist = list(datafields)
        image = vtk.vtkImageData()
        for field in fieldlist:
            if (ci.xlen > 255 and ci.ylen > 255 and ci.zlen > 255):
                #Do this if cutout is too large
                data=GetData().getcubedrawdata(ci, timestep, field)
            else:
                data=GetData().getrawdata(ci, timestep, field)        
            #This no longer works since we have a formatted numpy array.
            #vtkdata = numpy_support.numpy_to_vtk(data, deep=True, array_type=vtk.VTK_FLOAT)
            vtkdata = numpy_support.numpy_to_vtk(data.flat, deep=True, array_type=vtk.VTK_FLOAT)

            components = Datafield.objects.get(shortname=field).components
            vtkdata.SetNumberOfComponents(components)
            vtkdata.SetName(Datafield.objects.get(shortname=field).longname)
            image = vtk.vtkImageData()
                #We need to see if we need to subtract one on end of extent edges.
            image.SetExtent(ci.xstart, ci.xstart+ci.xlen-1, ci.ystart, ci.ystart+ci.ylen-1, ci.zstart, ci.zstart+ci.zlen-1)
            if (components == 3):
                image.GetPointData().SetVectors(vtkdata)
            else:
                image.GetPointData().SetScalars(vtkdata)
            image.SetSpacing(ci.xstep,ci.ystep,ci.zstep)

        #Check if we need a rectilinear grid, and set it up if so.
        if (ci.dataset == 'channel'):
            ygrid = jhtdblib.JHTDBLib().getygrid()
            #print("Ygrid: ")
            #print (ygrid)
            rg = vtk.vtkRectilinearGrid()
            #Not sure about contouring channel yet, so we are going back to original variables at this point.
            rg.SetExtent(ci.xstart, ci.xstart+ci.xlen-1, ci.ystart, ci.ystart+ci.ylen-1, ci.zstart, ci.zstart+ci.zlen-1)
            rg.GetPointData().SetVectors(vtkdata)

            xg = np.arange(float(ci.xstart),float(ci.xlen))
            zg = np.arange(float(ci.zstart),float(ci.zlen))
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
            print("Computing Vorticity")
            vorticity.Update()
        elif (computation == 'cvo'):
            vorticity = vtk.vtkCellDerivatives()
            vorticity.SetVectorModeToComputeVorticity()
            vorticity.SetTensorModeToPassTensors()
            vorticity.SetInputData(image)
            print("Computing Voricity")
            vorticity.Update()
            mag = vtk.vtkImageMagnitude()
            cp = vtk.vtkCellDataToPointData()
            cp.SetInputData(vorticity.GetOutput())
            print("Computing magnitude")
            cp.Update()
            image.GetPointData().SetScalars(cp.GetOutput().GetPointData().GetVectors())
            mag.SetInputData(image)
            mag.Update()
            c = vtk.vtkContourFilter()
            c.SetValue(0,ci.threshold)
            c.SetInputData(mag.GetOutput())
            print("Computing Contour with threshold", ci.threshold)
            c.Update()
            #Now we need to clip out the overlap
            box = vtk.vtkBox()    
            #set box to requested size
            box.SetBounds(oci.xstart, oci.xstart+oci.xlen-1, oci.ystart, oci.ystart+oci.ylen-1, oci.zstart,oci.zstart+oci.zlen-1)
            clip = vtk.vtkClipPolyData()       
            clip.SetClipFunction(box)
            clip.GenerateClippedOutputOn()
            clip.SetInputData(c.GetOutput())
            clip.InsideOutOn()
            clip.Update()
            cropdata = clip.GetOutput()
            return cropdata

        elif (computation == 'qcc'):
            q = vtk.vtkGradientFilter()
            q.SetInputData(image)
            q.SetInputScalars(image.FIELD_ASSOCIATION_POINTS,"Velocity")
            q.ComputeQCriterionOn()
            q.Update()
            image.GetPointData().SetScalars(q.GetOutput().GetPointData().GetVectors("Q-criterion"))
            mag = vtk.vtkImageMagnitude()
            mag.SetInputData(image)
            mag.Update()
            c = vtk.vtkContourFilter()
            c.SetValue(0,ci.threshold)
            c.SetInputData(mag.GetOutput())
            print("Computing Contour with threshold", ci.threshold)
            c.Update()
            #clip out the overlap here
            box = vtk.vtkBox()    
            #set box to requested size
            box.SetBounds(oci.xstart, oci.xstart+oci.xlen-1, oci.ystart, oci.ystart+oci.ylen-1, oci.zstart,oci.zstart+oci.zlen-1)
            clip = vtk.vtkClipPolyData()       
            clip.SetClipFunction(box)
            clip.GenerateClippedOutputOn()
            clip.SetInputData(c.GetOutput())
            clip.InsideOutOn()
            clip.Update()
            cropdata = clip.GetOutput()
            return cropdata
        else:
            return image
