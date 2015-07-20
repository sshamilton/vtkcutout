from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext, loader
from django.core.files.temp import NamedTemporaryFile
import vtk
import tempfile
import h5py

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
    datafield = request.POST.get("datafield", "")
    filetype = request.POST.get("fileformat", "")
    url = "http://localhost:8000/cutout/getcutout/"+ token + "/" + dataset + "/" + datafield + "/" + ts + "," +te + "/" + xs + "," + xe +"/" + ys + "," + ye +"/" + zs + "," + ze + "/" + filetype

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
        writer.SetTimeStepRange(ts,te)
        writer.SetFileName(tmp.name)
        writer.SetCompressorTypeToZLib()
        writer.SetDataModeToBinary()
        #writer.Start()
        for timestep in range (ts,te):
            image = odbccutout.OdbcCutout().getvtkimage(webargs, timestep)
            writer.SetInputData(timestep, image)
            writer.SetTimeStep(timestep)
            
        #writer.Stop()
        result = writer.Write()
        writer.Stop()
        #f = open(tmp, 'r')
        #return HttpResponse(image)
        ct = 'xml/' + suffix
        response = HttpResponse(tmp, content_type=ct)
        response['Content-Disposition'] = 'attachment;filename=' +  outfile + '.' + suffix
    else: #for backward compatibility, we serve hdf5 if not specified
        #Create an HDF5 file here
        h5file = odbccutout.OdbcCutout().gethdf(webargs)
        response = HttpResponse(h5file, content_type='data/hdf5')
        attach = 'attachment;filename=' + w[1] + '.h5'
        response['Content-Disposition'] = attach

    return response
    #return HttpResponse(result)



