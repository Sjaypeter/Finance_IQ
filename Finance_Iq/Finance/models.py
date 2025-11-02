from django.db import models

# Create your models here.

class Expense(models.Model):

    CATEGORY_CHOICES = [
        ("Food", "food"),
        ("Transport", "transport"),
        ("Entertainment", "entertainment"),
        ("Shopping", "shopping"),
        ("Bills", "bills"),
        ("Other", "other"),
    ]

    user_id = models.CharField(max_length=255)  # from Telex `from.id`
    channel_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    description = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id}: {self.amount} ({self.category})"
