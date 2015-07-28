from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext, loader
from django.core.files.temp import NamedTemporaryFile
import vtk
import tempfile
import h5py
import zipfile

from .models import Dataset
import odbccutout
# Create your views here.

def index(request):
    dataset_list = Dataset.objects.order_by('dataset_text')
    #output = '<br /> '.join([p.dataset_text for p in dataset_list])
    #return HttpResponse(output)
    template = loader.get_template('cutout/index.html')
    context = RequestContext(request, { 'dataset_list': dataset_list,}) 
    return HttpResponse(template.render(context))

def geturl(request):
    
    token = request.POST.get("token", "")
    ts = request.POST.get("timestart", "")
    te = request.POST.get("timeend", "")
    xs = request.POST.get("x", "")
    xe = request.POST.get("xEnd", "")
    ys = request.POST.get("y", "")
    ye = request.POST.get("yEnd", "")
    zs = request.POST.get("z", "")
    ze = request.POST.get("zEnd", "")
    dataset = request.POST.get("dataset", "")
    datafield = request.POST.getlist("datafield", "")
    datafields = ''.join(datafield)
    if (len(datafield) == 0):
        datafields = request.POST.get("cdatafield", "")
    filetype = request.POST.get("fileformat", "")
    url = "http://localhost:8000/cutout/getcutout/"+ token + "/" + dataset + "/" + datafields + "/" + ts + "," +te + "/" + xs + "," + xe +"/" + ys + "," + ye +"/" + zs + "," + ze + "/" + filetype

    return HttpResponse("Your download URL is <br /><a href='{0}'>{0}</a>".format(url))

def getcutout(request, webargs):
    params = "parameters=%s" % webargs
    w = webargs.split("/")
    ts = int(w[3].split(',')[0])
    te = int(w[3].split(',')[1])
    #o = odbccutout.OdbcCutout()
    if ((len(w) >= 8) and (w[7] == 'vtk')):    
        #Setup temporary file (would prefer an in-memory buffer, but this will have to do for now)

        if ((w[2] == 'cvo') or (w[2] == 'qcc')): #we may need to return a vtp file
            tmp = NamedTemporaryFile(suffix='.vtp')
            suffix = 'vtp'
            writer = vtk.vtkXMLPolyDataWriter()                         
            outfile = w[7] + '-contour'
        else:
            tmp = NamedTemporaryFile(suffix='.vti')
            suffix = 'vti'
            writer = vtk.vtkXMLImageDataWriter()                        
            outfile = 'cutout' + w[7]        
        writer.SetFileName(tmp.name)
        writer.SetCompressorTypeToZLib()
        writer.SetDataModeToBinary()
        #if multiple timesteps, zip the file.
        if ((te-ts) > 1):
            #Write each timestep to file and read it back in.  Seems to be the only way I know how to put all timesteps in one file for now
            #Create a timestep for each file and then send the user a zip file
            ziptmp = NamedTemporaryFile(suffix='.zip')
            z = zipfile.ZipFile(ziptmp.name, 'w')
            for timestep in range (ts,te):            
                image = odbccutout.OdbcCutout().getvtkimage(webargs, timestep)
                writer.SetInputData(image)
                writer.SetFileName(tmp.name)                        
                writer.Write()
                #Now add this file to the zipfile
                z.write(tmp.name, 'cutout' + str(timestep) + '.' + suffix)
            z.close()
            ct = 'application/zip'
            suffix = 'zip'
            response = HttpResponse(ziptmp, content_type=ct)
        else:
            image = odbccutout.OdbcCutout().getvtkimage(webargs, ts)
            writer.SetInputData(image)
            writer.SetFileName(tmp.name)                        
            writer.Write()
            ct = 'data/vtk'
            response = HttpResponse(tmp, content_type=ct)
        response['Content-Disposition'] = 'attachment;filename=' +  outfile +'.' + suffix
    else: #for backward compatibility, we serve hdf5 if not specified
        #Create an HDF5 file here
        h5file = odbccutout.OdbcCutout().gethdf(webargs)
        response = HttpResponse(h5file, content_type='data/hdf5')
        attach = 'attachment;filename=' + w[1] + '.h5'
        response['Content-Disposition'] = attach

    return response
    #return HttpResponse(result)



