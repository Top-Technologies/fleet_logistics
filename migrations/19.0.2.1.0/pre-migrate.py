def migrate(cr, version):
    """Keep existing free-text names available while the fields become relations."""
    cr.execute("""
        CREATE TABLE IF NOT EXISTS wb_logistics_people_migration AS
        SELECT id, driver_name AS driver_name, technician AS technician_name
          FROM wb_logistics_record
    """)
