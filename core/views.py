from django.shortcuts import render
from django.http import HttpResponse
from core.models import Bill, BillSummaries
from django import forms
from django.db.models import Q, IntegerField,Min
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
    summaries = BillSummaries.objects.filter(bill=bill)
    actions = bill.actions.all()
    context = {
        'search_form':search_form,
        'title':bill.bill_number,
        'bill':bill,
        'summaries':summaries,
        'actions':actions,
    }
    return render(request,'core/bill.html',context)

def search(request):
    search_form = BasicSearch()
    search_form.fields['query'].widget.attrs['placeholder'] = 'Search'
    q = request.GET['query']
    results = Bill.objects.filter(
        Q(bill_number__contains=q) |
        Q(title__contains=q) |
        Q(summaries__content__contains=q)
    ).annotate( 
        min_year=Min('sessions__year')
    ).order_by(
        'min_year',
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
