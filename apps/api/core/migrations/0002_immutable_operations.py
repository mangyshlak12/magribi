from django.db import migrations
class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunSQL(
        sql="""CREATE FUNCTION magribi_immutable_operation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'Loyalty operations are immutable; append a reversal'; END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER magribi_operation_immutable BEFORE UPDATE OR DELETE ON core_operation
FOR EACH ROW EXECUTE FUNCTION magribi_immutable_operation();""",
        reverse_sql="DROP TRIGGER IF EXISTS magribi_operation_immutable ON core_operation; DROP FUNCTION IF EXISTS magribi_immutable_operation();"
    )]
