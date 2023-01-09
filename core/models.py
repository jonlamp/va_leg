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
    
    def __str__(self)->str:
        return self.name

class Session(models.Model):
    title = models.CharField(max_length=100)
    lis_id = models.CharField(max_length=3, verbose_name="LIS ID")
    year = models.IntegerField()

    def __str__(self)->str:
        return f"{self.lis_id} {self.title}"