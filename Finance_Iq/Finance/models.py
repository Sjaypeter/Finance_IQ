from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Expense(models.Model):
    """Model representing a user's expense transaction"""
    
    CATEGORY_CHOICES = [
        ("food", "Food"),
        ("transport", "Transport"),
        ("entertainment", "Entertainment"),
        ("shopping", "Shopping"),
        ("bills", "Bills"),
        ("other", "Other"),
    ]

    user_id = models.CharField(max_length=255,db_index=True,help_text="Telegram user ID")
    channel_id = models.CharField(max_length=255,db_index=True,help_text="Telegram channel ID")
    amount = models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))],help_text="Expense amount (must be positive)"
    )
    category = models.CharField(max_length=50,choices=CATEGORY_CHOICES,default="other",db_index=True)
    description = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Expenses"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user_id', 'date']),
            models.Index(fields=['user_id', 'category']),
        ]

    def __str__(self):
        return f"{self.user_id}: ₦{self.amount} ({self.category})"