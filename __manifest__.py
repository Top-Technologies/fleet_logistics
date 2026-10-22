{
    "name": "Fleet Logistics Customization",
    "version": "19.0.2.0.0",
    "summary": "Logistics records, calculations and regional reporting inside Fleet",
    "category": "Operations/Fleet",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["fleet", "hr", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/logistics_sequence.xml",
        "views/logistics_rate_views.xml",
        "views/logistics_record_views.xml",
        "views/logistics_report_views.xml",
        "views/logistics_menus.xml",
    ],
    "installable": True,
    "application": False,
}
