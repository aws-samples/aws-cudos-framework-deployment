''' Patching dashboard definition
'''
from typing import Dict, List, Any
from uuid import uuid4

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
    """Format field name for display in the filter title."""
    # FIXME: Add special handling for acronyms
    return field_name.replace('_', ' ').title()

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

def add_filter_to_dashboard_definition(dashboard_definition: Dict[str, Any], field_names: List[str]) -> Dict[str, Any]:
    """ Add a filter on the specified fields to all datasets in a QuickSight definition

    param dashboard_definition (dict): The QuickSight definition JSON
    param field_names (list[str]): The list of field name to filter on
    returns: The modified QuickSight definition
    """
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

    add_filter_control_to_sheets(dashboard_definition, filter_ids)
    return dashboard_definition


def add_filter_control_to_sheets(dashboard_definition: Dict[str, Any], filter_ids: List[str]):
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

        for filter_id in filter_ids:
            control_id = uuid()
            sheet["FilterControls"].insert(0, {
                'CrossSheet': {
                    "FilterControlId": control_id,
                    "SourceFilterId": filter_id,
                }
            })
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

