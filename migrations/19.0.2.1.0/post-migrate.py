def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("SELECT to_regclass('wb_logistics_people_migration')")
    if not cr.fetchone()[0]:
        return

    cr.execute("SELECT DISTINCT btrim(driver_name) FROM wb_logistics_people_migration WHERE btrim(coalesce(driver_name, '')) != ''")
    driver_ids = {}
    for (name,) in cr.fetchall():
        driver_ids[name] = env['wb.logistics.driver'].create({'name': name}).id
    cr.execute("SELECT id, btrim(driver_name) FROM wb_logistics_people_migration WHERE btrim(coalesce(driver_name, '')) != ''")
    for record_id, name in cr.fetchall():
        env['wb.logistics.record'].browse(record_id).write({'driver_id': driver_ids[name]})

    cr.execute("SELECT DISTINCT btrim(technician_name) FROM wb_logistics_people_migration WHERE btrim(coalesce(technician_name, '')) != ''")
    technician_ids = {}
    for (name,) in cr.fetchall():
        technician_ids[name] = env['wb.logistics.technician'].create({'name': name}).id
    cr.execute("SELECT id, btrim(technician_name) FROM wb_logistics_people_migration WHERE btrim(coalesce(technician_name, '')) != ''")
    for record_id, name in cr.fetchall():
        env['wb.logistics.record'].browse(record_id).write({'technician_id': technician_ids[name]})
    cr.execute('DROP TABLE wb_logistics_people_migration')
