# models.py
from django.db import models


class VoteOption(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


class Vote(models.Model):
    option = models.ForeignKey(VoteOption, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"Vote for {self.option.text} from {self.ip_address}"
