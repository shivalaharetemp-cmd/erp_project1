from django.db import migrations, models
import uuid


def forwards(apps, schema_editor):
    Unit = apps.get_model('masters', 'Unit')
    Item = apps.get_model('masters', 'Item')
    db_alias = schema_editor.connection.alias

    # mapping for human-friendly names for common unit codes
    name_map = {
        'MT': 'Metric Tonne',
        'KG': 'Kilogram',
        'LTR': 'Litre',
        'PCS': 'Pieces',
    }

    # create Unit rows for distinct existing Item.unit string values
    created = {}
    for item in Item.objects.using(db_alias).all():
        code = getattr(item, 'unit', None)
        if not code:
            continue
        if code in created:
            unit_obj = created[code]
        else:
            unit_obj = Unit.objects.using(db_alias).create(
                code=code,
                name=name_map.get(code, code),
            )
            created[code] = unit_obj
        # set the foreign key on the temporary unit_fk field (created in this migration)
        try:
            # use unit_fk_id to avoid ORM FK assignment overhead
            setattr(item, 'unit_fk_id', unit_obj.id)
            item.save()
        except Exception:
            # best-effort; skip problematic rows
            continue


def reverse(apps, schema_editor):
    # irreversible conversion (reverse would require recreating old string values)
    return


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('gst_uqc', models.CharField(max_length=10, blank=True, help_text='GST UQC code')),
                ('hsn_sac', models.CharField(max_length=20, blank=True, help_text='Optional HSN or SAC code mapping')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Unit',
                'ordering': ['code'],
            },
        ),
        migrations.AddField(
            model_name='item',
            name='unit_fk',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.PROTECT, related_name='items_tmp', to='masters.Unit'),
        ),
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='item',
            name='unit',
        ),
        migrations.RenameField(
            model_name='item',
            old_name='unit_fk',
            new_name='unit',
        ),
    ]
