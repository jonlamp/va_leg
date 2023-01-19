from django.db import models

# Create your models here.
class Legislator(models.Model):
    name = models.CharField(max_length=100)
    # place will come later 
    place = models.CharField(max_length=30, null=True)
    party = models.CharField(max_length=1)
    district = models.IntegerField()
    lis_id = models.CharField(max_length=5, verbose_name="LIS Member ID")
    lis_no = models.CharField(max_length=5, verbose_name="LIS Member Number")
    d_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self)->str:
        return self.name

class Session(models.Model):
    title = models.CharField(max_length=100)
    lis_id = models.CharField(max_length=3, verbose_name="LIS ID")
    year = models.IntegerField()
    d_added = models.DateTimeField(auto_now_add=True)

    def __str__(self)->str:
        return f"{self.lis_id} {self.title}"

class Bill(models.Model):
    bill_number = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    text = models.TextField()
    d_introduced = models.DateField(verbose_name="Date Introduced")
    emergency = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    d_added = models.DateTimeField(auto_now_add=True)
    introduced_by = models.ForeignKey(
        Legislator,
        on_delete=models.PROTECT,
        related_name="introduced"
    )
    sessions = models.ManyToManyField(
        Session
    )
    patrons = models.ManyToManyField(
        Legislator,
        through='Patron'
    )

    def __str__(self)->str:
        return f"{self.bill_number} {self.title}"

class BillSummaries(models.Model):
    doc_id = models.CharField(max_length=10)
    category = models.CharField(max_length=50)
    content = models.TextField()
    d_added = models.DateTimeField(auto_now_add=True)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="summaries"
    )

    def __str__(self)->str:
        return f"{self.bill.bill_number} - {self.category}"


class Action(models.Model):
    d_action = models.DateTimeField()
    description = models.CharField(max_length=300)
    refid = models.CharField(max_length=40,null=True)
    d_added = models.DateTimeField(auto_now_add=True)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="actions"
    )
    def __str__(self) ->str:
        return f"({self.bill.bill_number}) {self.d_action.strftime('mm/dd/yyyy')}: {self.description}"

class Patron(models.Model):
    patron_type = models.CharField(max_length=40)
    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
    )
    legislator = models.ForeignKey(
        Legislator,
        on_delete=models.CASCADE,
    )