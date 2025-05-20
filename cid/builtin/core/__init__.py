# This plugin implements Core dashboards

def provides():
    return {
        'views': {
            'account_map': {
                'name': 'Account Map',
                'providedBy': 'cid.builtin.core',
                'File': 'queries/shared/account_map.sql',
            },
            'cost_forecast': {
                'name': 'Cost Forecast View',
                'providedBy': 'cid.builtin.core',
                'File': 'queries/forecast/cost_forecast_view.sql',
                'parameters': {
                    'forecast_table_name': {
                        'description': 'Name of the table containing forecast data',
                        'default': 'cost_forecast_data'
                    }
                }
            },
        },
        'datasets': {
            'cost_forecast_dataset': {
                'name': 'Cost Forecast Dataset',
                'providedBy': 'cid.builtin.core',
                'File': 'datasets/forecast/cost_forecast_dataset.json',
                'dependsOn': {
                    'views': ['cost_forecast']
                }
            }
        }
    }
