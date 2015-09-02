from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.core.files.temp import NamedTemporaryFile
from django import forms
import vtk
import tempfile
import h5py
import zipfile

from .models import Dataset
from jhtdblib import JHTDBLib
from jhtdblib import CutoutInfo
from hdfdata import HDFData

# Create your views here.

class CutoutForm(forms.Form):
    token = forms.CharField(label = 'token', max_length=50)
    fileformat = forms.ChoiceField(choices=[('vtk', 'VTK'), ('hdf5', 'HDF5')])
    dataset = forms.ModelChoiceField(queryset=Dataset.objects.all().order_by('dataset_text'), to_field_name="dbname_text")
    datafields = forms.MultipleChoiceField(choices=[('u', 'Velocity'), ('p',
        'Pressure')])
    cdatafields = forms.ChoiceField(choices=[('', '---------'),
        ('vo', 'Vorticity'),
        ('qc', 'Q-Criterion'),
        ('cvo', 'Vorticity Contour'),
        ('qcc', 'Q-Criterion Contour')])
    timestart = forms.CharField(label =  'timestart', max_length=5)
    timeend = forms.CharField(label =  'timeend', max_length=5)
    x = forms.CharField(label =  'x', max_length=5)
    xEnd = forms.CharField(label =  'xEnd', max_length=5)
    y = forms.CharField(label =  'y', max_length=5)
    yEnd = forms.CharField(label =  'yEnd', max_length=5)
    z = forms.CharField(label =  'z', max_length=5)
    zEnd = forms.CharField(label =  'zEnd', max_length=5)
    tstep = forms.CharField(label =  'tstep', max_length=5, initial="1")
    xstep = forms.CharField(label =  'xstep', max_length=5, initial="1")
    ystep = forms.CharField(label =  'ystep', max_length=5, initial="1")
    zstep = forms.CharField(label =  'zstep', max_length=5, initial="1")
    filter = forms.CharField(label =  'filter', max_length=5, initial="1")
    threshold = forms.CharField(label =  'threshold', max_length=5)
    step_checkbox = forms.BooleanField(label = 'step_checkbox')
    
def index(request):
    dataset_list = Dataset.objects.order_by('dataset_text')
    #output = '<br /> '.join([p.dataset_text for p in dataset_list])
    #return HttpResponse(output)
    template = loader.get_template('jhtdb/index.html')

    if (request.method == "POST"):    
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
        datafield = request.POST.getlist("datafields", "")
        datafields = ''.join(datafield)
        if (len(datafield) == 0):
            if (request.POST.get("threshold", "") is None):
                datafields = request.POST.get("cdatafields", "")
            else:
                threshold = request.POST.get("threshold", "")
                datafields = request.POST.get("cdatafields", "") + "," + threshold

        filetype = request.POST.get("fileformat", "")
        server = request.META['HTTP_HOST']
        url = "http://" + server + "/jhtdb/getcutout/"+ token + "/" + dataset + "/" + datafields + "/" + ts + "," +te + "/" + xs + "," + xe +"/" + ys + "," + ye +"/" + zs + "," + ze + "/" + filetype + "/"
        if (request.POST.get("step_checkbox", "")):
            url = url + "/" + request.POST.get("tstep") + "," + request.POST.get("xstep") + "," + request.POST.get("ystep") + "," + request.POST.get("zstep") + "/" + request.POST.get("filter") 
        download_link = url
        dataset_list = Dataset.objects.order_by('dataset_text')
        form = CutoutForm(request.POST)
        context = RequestContext(request, { 'dataset_list': dataset_list, 'download_link': download_link, 'form': form}) 
    else:
        form = CutoutForm()
        download_link = "Link: " #placeholder until download link is generated
        context = RequestContext(request, { 'dataset_list': dataset_list, 'form': form}) 
    return HttpResponse(template.render(context))

def getcutout(request, webargs):
    ci = CutoutInfo()
    jhlib = JHTDBLib()
    #Parse web args into cutout info object
    ci=jhlib.parsewebargs(webargs)
    if (ci.filetype == "vtk"):
        vtkfile = vtkdata().getvtk(ci)
        #Set the filename to the dataset name, and the suffix to the suffix of the temp file
        response['Content-Disposition'] = 'attachment;filename=' +  ci.dataset +'.' + vtkfile.name.split('.').pop()
    else:
        #Serve up an HDF5 file
        h5file = HDFData().gethdf(ci)
        response = HttpResponse(h5file, content_type='data/hdf5')
        attach = 'attachment;filename=' + ci.dataset + '.h5'
        response['Content-Disposition'] = attach
    return response





