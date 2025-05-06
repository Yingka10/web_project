from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),  # 請根據實際依賴調整版本號
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE chat_conversation RENAME COLUMN participant1_id TO buyer_id;",
            reverse_sql="ALTER TABLE chat_conversation RENAME COLUMN buyer_id TO participant1_id;",
        ),
    ]