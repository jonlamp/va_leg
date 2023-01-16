from django.shortcuts import render
from django.http import HttpResponse
from core.models import Bill
from django import forms
from django.db.models import Q, IntegerField
from django.db.models.functions import Cast,Substr

class BasicSearch(forms.Form):
    query = forms.CharField(label='Search', max_length=100)

# Create your views here.
def index(request):
    search_form = BasicSearch()
    search_form.fields['query'].widget.attrs['placeholder'] = 'Search by bill, legislator, or keyword'
    context = {
        'search_form': search_form
    }
    return render(request, 'core/index.html',context)

def bill_view(request,bill_id):
    bill = Bill.objects.get(pk=bill_id)
    search_form = BasicSearch()
    search_form.fields['query'].widget.attrs['placeholder'] = 'Search'
    context = {
        'search_form':search_form,
        'title':bill.bill_number,
        'bill':bill
    }
    return render(request,'core/bill.html',context)

def search(request):
    search_form = BasicSearch()
    search_form.fields['query'].widget.attrs['placeholder'] = 'Search'
    q = request.GET['query']
    results = Bill.objects.filter(
        Q(bill_number__contains=q) |
        Q(title__contains=q)
    ).order_by(
        'session__year',
        Substr('bill_number',1,2),
        Cast(Substr('bill_number',pos=3),IntegerField())
    )
    
    context = {
        'title':'VAL - Search Results',
        'search_form':search_form,
        'query_string':q,
        'results':results
    }
    return render(request,'core/results.html',context)
