from django.db import models

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    order = models.IntegerField(default=0) # For custom ordering

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['order']

    def __str__(self):
        return self.question[:50] + "..." if len(self.question) > 50 else self.question

class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    read_time_minutes = models.IntegerField(default=1)
    published_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return self.title

class Service(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    icon_class = models.CharField(max_length=100, help_text="e.g., bi bi-truck-flatbed")
    features = models.JSONField(default=list, blank=True, help_text="List of features as JSON array of strings")

    def __str__(self):
        return self.title