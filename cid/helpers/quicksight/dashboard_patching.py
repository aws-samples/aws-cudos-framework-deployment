''' Patching dashboard definition
'''

import uuid

def add_filter_to_dashboard_definition(dashboard_definition, field_names):
    """ Add a filter on the specified fields to all datasets in a QuickSight definition

    param dashboard_definition (dict): The QuickSight definition JSON
    param field_names (list[str]): The list of field name to filter on
    returns: The modified QuickSight definition
    """
    # get the most used dataset
    dataset_identifiers = sorted([
            (str(dashboard_definition).count(d["Identifier"]), d["Identifier"])
            for d in dashboard_definition.get("DataSetIdentifierDeclarations", [])
        ]
    )
    dataset_identifier = dataset_identifiers[-1][1] #take the dataset, the most frequently used
    filter_ids = []
    # FIXME: try to do linked
    for field_name in field_names:
        filter_group_id = str(uuid.uuid4())
        filter_id = str(uuid.uuid4())
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
                            "Title": (field_name).replace('_', ' ').title() # FIXME: can be better for acronyms
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


def add_filter_control_to_sheets(dashboard_definition, filter_ids):
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
            control_id = str(uuid.uuid4())
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
        row = col = 0
        for element in sheet["SheetControlLayouts"][0]["Configuration"]["GridLayout"]["Elements"]:
            if col + element["ColumnSpan"] > 12:
                col = 0
                row = row + 1
            element["ColumnIndex"] = col
            element["RowIndex"] = row
            col = col + element["ColumnSpan"]

