# Generated by Django 5.2 on 2025-05-13 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_alter_conversation_options_conversation_updated_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conversation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="最後更新"),
        ),
    ]
