from django.shortcuts import render, redirect
from django.http import HttpResponse
from core.models import Bill, BillSummaries, Patron, Session, Action, TrackedBills
from core.forms import NewUserForm
from django import forms
from django.db.models import Q, IntegerField,Min, Max
from django.db.models.functions import Cast,Substr
from django.forms import ModelChoiceField
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

class CustomModelChoice(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.title

class BasicSearch(forms.Form):
    query = forms.CharField(label='Search', max_length=100)

class AdvancedSearch(forms.Form):
    title = forms.CharField(label="Title Contains:", max_length=100,required=False)
    introduced = forms.IntegerField(
        label="Year the bill introduced",
        max_value=Bill.objects.latest('d_introduced').d_introduced.year,
        min_value=Bill.objects.earliest('d_introduced').d_introduced.year,
        error_messages={
            'max_value':'Sorry, our database does not contain that year yet.',
            'min_value':'Sorry, our database does not contain that year yet.'
        },
        required=False
    )
    legislator = forms.CharField(label="Legislator name contains:", max_length=40, required=False)
    summary = forms.CharField(label="Summary contains:", max_length="100",required=False)
    session = CustomModelChoice(
        Session.objects.all(),
        required=False
    )

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
    patrons = Patron.objects.filter(bill=bill)
    if request.user.is_authenticated:
        tracked = TrackedBills.objects.filter(bill__pk = bill.pk, user__pk = request.user.pk).exists()
    else:
        tracked=False
    context = {
        'search_form':search_form,
        'title':bill.bill_number,
        'bill':bill,
        'summaries':summaries,
        'actions':actions,
        'patrons':patrons,
        'tracked':tracked
    }
    return render(request,'core/bill.html',context)

def search(request):
    search_form = BasicSearch()
    search_form.fields['query'].widget.attrs['placeholder'] = 'Search'
    if request.method == "GET":
        if 'query' in request.GET:
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
                'results':results,
                'advanced_search_form':AdvancedSearch()
            }
        else:
            context={
                'title':'VAL - Search Results',
                'search_form':search_form,
                'advanced_search_form':AdvancedSearch()
            }
    elif request.method == "POST":
        data = request.POST
        results = Bill.objects.all()
        q = ""
        if len(data['title'])>0:
            results = results.filter(title__contains=data['title'])
            q += f"titles containing \"{data['title']}\"; "
        if len(data['introduced'])>0:
            results = results.filter(d_introduced__year=data['introduced'])
            q += f"bills introduced in \"{data['introduced']}\"; "
        if len(data['legislator'])>0:
            results = results.filter(patrons__name__contains=data['legislator'])
            q += f"bills where legislators whose names contain \"{data['legislator']}\" are a patron; "
        if len(data['summary'])>0:
            results = results.filter(summaries__content__contains=data['summary'])
            q += f"bills whose summaries contain \"{data['summary']}\"; "
        if len(data['session'])>0:
            results = results.filter(sessions__pk=data['session'])
            q += f"bills with actions during the {Session.objects.get(pk=data['session']).title}; "
        context={
            'title':'VAL - Search Results',
            'search_form':search_form,
            'query_string':q,
            'results':results[:100],
            'advanced_search_form':AdvancedSearch()
        }
    return render(request,'core/results.html',context)

def browse(request):
    search_form = BasicSearch()
    search_form.fields['query'].widget.attrs['placeholder'] = 'Search'
    days = list(Action.objects.values('d_action').order_by('-d_action').distinct()[:5])
    bill_list = Bill.objects.all().annotate(
        latest_action = Max('actions__d_action')
    )
    for day in days:
        day['bills'] = list(bill_list.filter(latest_action=day['d_action']).order_by('bill_number').values())
    context = {
        'title':'VAL - Browse',
        'search_form':search_form,
        'days':days
    }
    return render(request,'core/browse.html',context)

def about(request):
    search_form = BasicSearch()
    search_form.fields['query'].widget.attrs['placeholder'] = 'Search'
    context = {
        'title':'About VAL',
        'search_form':search_form
    }
    return render(request,'core/about.html',context)

def register(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            messages.success(request,'Registration successful.')
            return redirect('index')
        else:
            messages.error(request,'Could not register new user. Please try again.')
    else:
        form = NewUserForm()
        context = {
            'title':'VAL - New User',
            'form': form
        }
        return render(request,'registration/register.html',context)

@login_required
def track(request):
    if request.method == 'POST':
        bill_pk = request.POST.get('bill_pk')
        bill = Bill.objects.get(pk=bill_pk)
        tb = TrackedBills(bill=bill,user=request.user)
        tb.save()
        return redirect(f'bill/{bill_pk}')