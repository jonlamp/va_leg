from django.shortcuts import render
from django.http import HttpResponse
from core.models import Bill

# Create your views here.
def index(request):
    return render(request, 'core/index.html')

def bill_view(request,bill_id):
    bill = Bill.objects.get(pk=bill_id)
    context = {
        'title':bill.bill_number,
        'bill':bill
    }
    return render(request,'core/bill.html',context)