# Generated by Django 4.2.4 on 2023-09-08 15:51

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0007_remove_student_birthday'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='firstName',
            field=models.CharField(max_length=50, validators=[django.core.validators.RegexValidator(message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.", regex='^[0-9a-zA-Z \\-\\_]*$')], verbose_name='First name'),
        ),
        migrations.AlterField(
            model_name='student',
            name='lastName',
            field=models.CharField(max_length=50, validators=[django.core.validators.RegexValidator(message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.", regex='^[0-9a-zA-Z \\-\\_]*$')], verbose_name='Last name'),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=50, validators=[django.core.validators.RegexValidator(message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.", regex='^[0-9a-zA-Z \\-\\_]*$')], verbose_name='Name'),
        ),
    ]
