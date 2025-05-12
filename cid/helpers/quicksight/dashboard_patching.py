''' Patching dashboard definition
'''
import re
import logging
from typing import Dict, List, Any
from uuid import uuid4


from cid.utils import CidCritical


logger = logging.getLogger(__name__)

MAX_GRID_WIDTH = 12 # QuickSight Span width for controls

def uuid() -> str:
    """Generate a CID-flavored UUID."""
    return 'c1d' + str(uuid4())[3:]

def get_most_used_dataset(dashboard_definition: Dict[str, Any]) -> str:
    """Get an identifier of a most used dataset."""
    dataset_identifiers = sorted([
        (str(dashboard_definition).count(d["Identifier"]), d["Identifier"])
        for d in dashboard_definition.get("DataSetIdentifierDeclarations", [])
    ])
    return dataset_identifiers[-1][1] if dataset_identifiers else None

def format_field_name(field_name: str) -> str:
    """Format field name for display in the filter title.
        assert format_field_name('account_name') == 'Account Name'
        assert format_field_name('a_c_r_o_n_y_m') == 'ACRONYM'
        assert format_field_name('tag_a_c_r_o_n_y_m') == 'Tag ACRONYM'
    """
    parts = field_name.split('_')
    result = []
    i = 0
    while i < len(parts):
        # Check if current part is the start of an acronym sequence
        if i < len(parts) and len(parts[i]) == 1:  # Collect all single-letter parts
            acronym_parts = []
            while i < len(parts) and len(parts[i]) == 1:
                acronym_parts.append(parts[i])
                i += 1
            if acronym_parts:  # If we found an acronym, add it to the result
                result.append(''.join(acronym_parts).upper())
        else: # Handle regular part
            result.append(parts[i].title())
            i += 1
    return ' '.join(result)

def align_grid_position(elements: List[Dict[str, Any]]) -> None:
    """Align grid positions for control layout elements."""
    row = col = 0
    for element in elements:
        if col + element["ColumnSpan"] > MAX_GRID_WIDTH:
            col = 0
            row += 1
        element["ColumnIndex"] = col
        element["RowIndex"] = row
        col += element["ColumnSpan"]

def delete_parameter_control(dashboard_definition: Dict[str, Any], parameter_name) -> Dict[str, Any]:
    ''' delete parameter controls
    '''
    def _delete_control_id(data, control_id):
        """Delete all elements that have a reference to control id
        warning: there no deletion of dependencies
        """
        if isinstance(data, dict):
            if control_id in data.values():
                return '<delete_me_from_list>'
            res = {}
            delete_detected = False
            for k, v in data.items():
                v2 = _delete_control_id(v, control_id)
                if v2 == '<delete_me_from_list>':
                    delete_detected = True
                else:
                    res[k] = v2
            if  delete_detected and not res: return '<delete_me_from_list>'
            return res
        elif isinstance(data, list):
            res = []
            delete_detected = False
            for v in data:
                v2 = _delete_control_id(v, control_id)
                if v2 == '<delete_me_from_list>':
                    delete_detected = True
                else:
                    res.append(v2)
            if  delete_detected and not res: return '<delete_me_from_list>'
            return res
        return data

    for sheet in dashboard_definition.get("Sheets", []):
        if sheet.get("Name") == "About":
            continue # Skip about
        for control in sheet.get('ParameterControls', []):
            control_params =  next(iter(control.values()), {})
            if control_params.get('Title', '').lower() == parameter_name.lower():
                control_id = control_params['ParameterControlId']
                logger.debug(f'deleting control {control_id}')
                dashboard_definition = _delete_control_id(dashboard_definition, control_id)

    # set default parameters to default
    def _set_default_parameters(data):
        """Recursively set currency_symbol"""
        if isinstance(data, dict):
            if "ValueWhenUnsetOption" in data:
                data['ValueWhenUnsetOption'] = 'RECOMMENDED_VALUE'
            return {k: _set_default_parameters(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [_set_default_parameters(item) for item in data]
        return data
    dashboard_definition = _set_default_parameters(dashboard_definition)

    return dashboard_definition

def add_filter_to_dashboard_definition(dashboard_definition: Dict[str, Any], field_names: List[str]) -> Dict[str, Any]:
    """ Add a filter on the specified fields to all datasets in a QuickSight definition

    param dashboard_definition (dict): The QuickSight definition JSON
    param field_names (list[str]): The list of field name to filter on
    returns: The modified QuickSight definition
    """
    # delete all old redundant controls
    mapping = {
        'payer_account_id': 'payer accounts',
        'parent_account_id': 'payer accounts',
        'account_id':  'Linked Account IDs',
        'linked_account_id': 'Linked Account IDs',
        'account_name': 'Account Names',
    }
    for field_name in field_names:
        if field_name in mapping:
           dashboard_definition = delete_parameter_control(dashboard_definition, mapping.get(field_name))

    dataset_identifier = get_most_used_dataset(dashboard_definition)
    filter_ids = []
    # FIXME: try to do linked filter controls
    for field_name in reversed(field_names):
        filter_group_id = uuid()
        filter_id = uuid()
        new_filter = {
            "CrossDataset": "ALL_DATASETS",
            "FilterGroupId": filter_group_id,
            "Filters": [
                {
                    "CategoryFilter": {
                        "Column": {
                            "ColumnName": field_name,
                            "DataSetIdentifier": dataset_identifier
                        },
                        "Configuration": {
                            "FilterListConfiguration": {
                                "MatchOperator": "CONTAINS",
                                "NullOption": "ALL_VALUES",
                                "SelectAllOptions": "FILTER_ALL_VALUES"
                            }
                        },
                        "DefaultFilterControlConfiguration": {
                            "ControlOptions": {
                                "DefaultDropdownOptions": {
                                    "DisplayOptions": {
                                        "SelectAllOptions": {
                                            "Visibility": "VISIBLE"
                                        },
                                        "TitleOptions": {
                                            "FontConfiguration": {},
                                            "Visibility": "VISIBLE"
                                        }
                                    },
                                    "Type": "MULTI_SELECT"
                                }
                            },
                            "Title": format_field_name(field_name)
                        },
                        "FilterId": filter_id
                    }
                }
            ],
            "ScopeConfiguration": {
                "AllSheets": {}
            },
            "Status": "ENABLED"
        }
        filter_ids.append(filter_id)
        dashboard_definition["FilterGroups"] = dashboard_definition.get("FilterGroups", []) + [new_filter]

    add_filter_control_to_sheets(dashboard_definition, filter_ids, field_names, dataset_identifier)
    return dashboard_definition


def add_filter_control_to_sheets(dashboard_definition: Dict[str, Any], filter_ids: List[str], field_names: List[str], dataset_identifier):
    """Add a filter control to each sheet except 'about'"""
    for sheet in dashboard_definition.get("Sheets", []):
        if sheet.get("Name") == "About":
            continue # Skip about

        sheet["FilterControls"] = sheet.get("FilterControls", [])
        if not sheet.get("SheetControlLayouts"):
            sheet["SheetControlLayouts"] = [{
                "Configuration": {
                    "GridLayout": {
                        "Elements": []
                    }
                }
            }]

        control_ids = [uuid() for _ in filter_ids]
        for filter_id, control_id in zip(filter_ids, control_ids):
            control = {
                'CrossSheet': {
                    "FilterControlId": control_id,
                    "SourceFilterId": filter_id,
                }
            }
            if len(filter_ids) > 0: # link values filtering with other controls
                control['CrossSheet']['CascadingControlConfiguration'] = {
                    "SourceControls": [
                        {
                            "SourceSheetControlId": control_id_,
                            "ColumnToMatch": {
                                "DataSetIdentifier": dataset_identifier,
                                "ColumnName": field_name_,
                            }
                        }
                        for filter_id_, control_id_, field_name_ in zip(filter_ids, control_ids, field_names)
                        if filter_id != filter_id_
                    ]
                }
            sheet["FilterControls"].insert(0, control)
            sheet["SheetControlLayouts"][0]["Configuration"]["GridLayout"]["Elements"].insert(0, {
                "ColumnIndex": 0, # just to start
                "ColumnSpan": 2, # can be a parameter?
                "ElementId": control_id,
                "ElementType": "FILTER_CONTROL",
                "RowIndex": 0,
                "RowSpan": 1 # always 1
            })

        #Align elements in the Control Layout
        align_grid_position(sheet["SheetControlLayouts"][0]["Configuration"]["GridLayout"]["Elements"])


def patch_currency(definition, currency_symbol):
    ''' patch dashboard by adding currency symbol where the currency is configured already.
    '''
    def _set_currency_symbol(data):
        """Recursively set currency_symbol"""
        if isinstance(data, dict):
            if 'CurrencyDisplayFormatConfiguration' in data:
                data['CurrencyDisplayFormatConfiguration']['Symbol'] = currency_symbol
            return {k: _set_currency_symbol(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [_set_currency_symbol(item) for item in data]
        return data

    currency_symbol = {
        '$': "USD", # US Dollar
        '£': "GBP", # British Pound
        '€': "EUR", # Euro
        '¥': "JPY", # Japanese Yen
        '₩': "KRW", # South Korean Won
        'kr': "DKK", # Danish Krone
        'NT': "TWD", # Taiwan Dollar
        '₹': "INR", # Indian Rupee
    }.get(currency_symbol, currency_symbol)

    if currency_symbol != 'USD' and currency_symbol:
        if currency_symbol not in "USD|GBP|EUR|JPY|KRW|DKK|TWD|INR".split('|'):
            raise CidCritical(f'Currency {currency_symbol} is not supported. USD|GBP|EUR|JPY|KRW|DKK|TWD|INR')
        logger.info(f'Setting currency_symbol = <BOLD>{currency_symbol}<END>')
        definition = _set_currency_symbol(definition)
    return definition


def patch_group_by(definition, fields):
    # Add new fields to the code of Calc functions
    managed_parameters = []
    for cf in definition['CalculatedFields']:
        param_name = 'GroupBy' # Can be dynamic?
        if f'// Add ${{{param_name}}}' in cf['Expression']:
            managed_parameters.append(param_name)
            for field in reversed(fields):
                new_line = f"${{{param_name}}}='{format_field_name(field)}', {{{field}}},"
                cf['Expression'] = re.sub('^(\s*)(// Add)', f'\\1{new_line}\n\\1\\2', cf['Expression'], flags=re.MULTILINE)
            logger.trace(f'Added {fields} to {cf}')
    # Add new field to all controls
    for parameter in set(managed_parameters):
        for sheet in definition['Sheets']:
            for control_dict in sheet.get('ParameterControls',[]):
                control = next(iter(control_dict.values()), {})
                if control.get('SourceParameterName') != parameter:
                    continue
                for field in reversed(fields):
                    control.get('SelectableValues', {}).get('Values',[]).insert(0, format_field_name(field))
                    logger.trace(f'added {field} to {sheet["Name"]} / {control["Title"]}')
    return definition


def _try():
    import yaml
    data = yaml.safe_load(open('./dashboards/cudos/CUDOS-v5.yaml'))
    definition = yaml.safe_load(data['dashboards']['CUDOSv5']['data'])