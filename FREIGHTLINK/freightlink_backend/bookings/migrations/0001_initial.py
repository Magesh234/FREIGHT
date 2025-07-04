# Generated by Django 5.2.1 on 2025-06-20 07:44

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('trucks', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking_reference', models.CharField(editable=False, max_length=20, unique=True)),
                ('pickup_date', models.DateTimeField()),
                ('expected_delivery_date', models.DateTimeField()),
                ('pickup_address', models.TextField()),
                ('delivery_address', models.TextField()),
                ('cargo_description', models.TextField(help_text="Describe what you're shipping")),
                ('cargo_type', models.CharField(choices=[('general', 'General Cargo'), ('fragile', 'Fragile Items'), ('perishable', 'Perishable Goods'), ('hazardous', 'Hazardous Materials'), ('electronics', 'Electronics'), ('furniture', 'Furniture'), ('construction', 'Construction Materials'), ('automotive', 'Automotive Parts'), ('textiles', 'Textiles'), ('other', 'Other')], default='general', max_length=20)),
                ('cargo_weight', models.DecimalField(blank=True, decimal_places=2, help_text='Weight in tons (optional)', max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.1'))])),
                ('cargo_volume', models.DecimalField(blank=True, decimal_places=2, help_text='Volume in cubic meters (optional)', max_digits=8, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.1'))])),
                ('quoted_price', models.DecimalField(blank=True, decimal_places=2, default=Decimal('15000.00'), max_digits=10, null=True)),
                ('final_price', models.DecimalField(blank=True, decimal_places=2, default=Decimal('15000.00'), max_digits=10, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('special_instructions', models.TextField(blank=True, help_text='Any special handling instructions')),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to=settings.AUTH_USER_MODEL)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='trucks.truck')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BookingDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('invoice', 'Invoice'), ('receipt', 'Receipt'), ('delivery_note', 'Delivery Note'), ('cargo_manifest', 'Cargo Manifest'), ('insurance', 'Insurance Document'), ('permit', 'Permit'), ('photo', 'Photo'), ('other', 'Other')], max_length=20)),
                ('title', models.CharField(max_length=100)),
                ('file', models.FileField(upload_to='booking_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='bookings.booking')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='BookingStatusUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], max_length=20)),
                ('new_status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_updates', to='bookings.booking')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['booking_reference'], name='bookings_bo_booking_8a7545_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['customer', 'status'], name='bookings_bo_custome_0cbf77_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['truck', 'status'], name='bookings_bo_truck_i_2ea34f_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['pickup_date'], name='bookings_bo_pickup__2a95b5_idx'),
        ),
    ]
