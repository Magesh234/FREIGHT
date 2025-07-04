# Generated by Django 5.2.1 on 2025-06-20 07:44

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Truck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('truck_type', models.CharField(choices=[('pickup', 'Pickup Truck'), ('cargo_van', 'Cargo Van'), ('closed_body', 'Closed Body Truck'), ('flatbed', 'Flatbed Truck'), ('refrigerated', 'Refrigerated Truck'), ('tipper', 'Tipper Truck'), ('tanker', 'Tanker Truck'), ('low_loader', 'Low Loader'), ('semi_trailer', 'Semi-Trailer'), ('other', 'Other')], max_length=20)),
                ('capacity_tons', models.DecimalField(blank=True, decimal_places=2, help_text='Maximum load capacity in tons (e.g., 1.5 for 1.5 tons)', max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(0.1)])),
                ('make_model', models.CharField(blank=True, help_text="Make and model of the truck (e.g., 'Ford F-150')", max_length=100, null=True)),
                ('year', models.IntegerField(blank=True, help_text='Year of manufacture (e.g., 2020)', null=True, validators=[django.core.validators.MinValueValidator(1950), django.core.validators.MaxValueValidator(2026)])),
                ('current_location', models.CharField(max_length=200)),
                ('available_from', models.DateField()),
                ('available_to', models.DateField(blank=True, null=True)),
                ('preferred_routes', models.TextField(blank=True)),
                ('rate_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('rate_type', models.CharField(choices=[('per_km', 'Per Kilometer'), ('per_trip', 'Per Trip'), ('per_hour', 'Per Hour'), ('per_day', 'Per Day')], default='per_km', max_length=10)),
                ('additional_notes', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trucks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TruckImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='truck_images/')),
                ('caption', models.CharField(blank=True, max_length=100)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='trucks.truck')),
            ],
            options={
                'ordering': ['uploaded_at'],
            },
        ),
    ]
