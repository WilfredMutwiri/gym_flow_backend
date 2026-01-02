from django.db import models
from shared.basemodel import BaseModel

class AttendanceRecord(BaseModel):
    member = models.ForeignKey('core.Member', on_delete=models.CASCADE, related_name='attendance')
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(db_index=True)
    method = models.CharField(max_length=20)  # manual, qr, id
