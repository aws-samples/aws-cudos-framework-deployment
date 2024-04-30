import re
import logging

logger = logging.getLogger(__name__)

cur2to1mapping = {
    "concat(year, '-' ,month)": "billing_period",
    'year': "split_part(billing_period, '-', 1)",
    'month': "split_part(billing_period, '-', 2)",
    'identity_line_item_id': 'identity_line_item_id',
    'identity_time_interval': 'identity_time_interval',
    'bill_invoice_id': 'bill_invoice_id',
    'bill_invoicing_entity': 'bill_invoicing_entity',
    'bill_billing_entity': 'bill_billing_entity',
    'bill_bill_type': 'bill_bill_type',
    'bill_payer_account_id': 'bill_payer_account_id',
    'bill_billing_period_start_date': 'bill_billing_period_start_date',
    'bill_billing_period_end_date': 'bill_billing_period_end_date',
    'line_item_usage_account_id': 'line_item_usage_account_id',
    'line_item_line_item_type': 'line_item_line_item_type',
    'line_item_usage_start_date': 'line_item_usage_start_date',
    'line_item_usage_end_date': 'line_item_usage_end_date',
    'line_item_product_code': 'line_item_product_code',
    'line_item_usage_type': 'line_item_usage_type',
    'line_item_operation': 'line_item_operation',
    'line_item_availability_zone': 'line_item_availability_zone',
    'line_item_resource_id': 'line_item_resource_id',
    'line_item_usage_amount': 'line_item_usage_amount',
    'line_item_normalization_factor': 'line_item_normalization_factor',
    'line_item_normalized_usage_amount': 'line_item_normalized_usage_amount',
    'line_item_currency_code': 'line_item_currency_code',
    'line_item_unblended_rate': 'line_item_unblended_rate',
    'line_item_unblended_cost': 'line_item_unblended_cost',
    'line_item_blended_rate': 'line_item_blended_rate',
    'line_item_blended_cost': 'line_item_blended_cost',
    'line_item_line_item_description': 'line_item_line_item_description',
    'line_item_tax_type': 'line_item_tax_type',
    'line_item_legal_entity': 'line_item_legal_entity',
    'product_fee_code': 'product_fee_code',
    'product_fee_description': 'product_fee_description',
    'product_from_location': 'product_from_location',
    'product_from_location_type': 'product_from_location_type',
    'product_from_region_code': 'product_from_region_code',
    'product_instance_family': 'product_instance_family',
    'product_instance_type': 'product_instance_type',
    'product_location': 'product_location',
    'product_location_type': 'product_location_type',
    'product_operation': 'product_operation',
    'product_product_family': 'product_product_family',
    'product_region_code': 'product_region_code',
    'product_servicecode': 'product_servicecode',
    'product_sku': 'product_sku',
    'product_to_location': 'product_to_location',
    'product_to_location_type': 'product_to_location_type',
    'product_to_region_code': 'product_to_region_code',
    'product_usagetype': 'product_usagetype',
    'pricing_rate_code': 'pricing_rate_code',
    'pricing_rate_id': 'pricing_rate_id',
    'pricing_currency': 'pricing_currency',
    'pricing_public_on_demand_cost': 'pricing_public_on_demand_cost',
    'pricing_public_on_demand_rate': 'pricing_public_on_demand_rate',
    'pricing_term': 'pricing_term',
    'pricing_unit': 'pricing_unit',
    'reservation_amortized_upfront_cost_for_usage': 'reservation_amortized_upfront_cost_for_usage',
    'reservation_amortized_upfront_fee_for_billing_period': 'reservation_amortized_upfront_fee_for_billing_period',
    'reservation_effective_cost': 'reservation_effective_cost',
    'reservation_end_time': 'reservation_end_time',
    'reservation_modification_status': 'reservation_modification_status',
    'reservation_normalized_units_per_reservation': 'reservation_normalized_units_per_reservation',
    'reservation_number_of_reservations': 'reservation_number_of_reservations',
    'reservation_recurring_fee_for_usage': 'reservation_recurring_fee_for_usage',
    'reservation_start_time': 'reservation_start_time',
    'reservation_subscription_id': 'reservation_subscription_id',
    'reservation_total_reserved_normalized_units': 'reservation_total_reserved_normalized_units',
    'reservation_total_reserved_units': 'reservation_total_reserved_units',
    'reservation_units_per_reservation': 'reservation_units_per_reservation',
    'reservation_unused_amortized_upfront_fee_for_billing_period': 'reservation_unused_amortized_upfront_fee_for_billing_period',
    'reservation_unused_normalized_unit_quantity': 'reservation_unused_normalized_unit_quantity',
    'reservation_unused_quantity': 'reservation_unused_quantity',
    'reservation_unused_recurring_fee': 'reservation_unused_recurring_fee',
    'reservation_upfront_value': 'reservation_upfront_value',
    'savings_plan_total_commitment_to_date': 'savings_plan_total_commitment_to_date',
    'savings_plan_savings_plan_a_r_n': 'savings_plan_savings_plan_a_r_n',
    'savings_plan_savings_plan_rate': 'savings_plan_savings_plan_rate',
    'savings_plan_used_commitment': 'savings_plan_used_commitment',
    'savings_plan_savings_plan_effective_cost': 'savings_plan_savings_plan_effective_cost',
    'savings_plan_amortized_upfront_commitment_for_billing_period': 'savings_plan_amortized_upfront_commitment_for_billing_period',
    'savings_plan_recurring_commitment_for_billing_period': 'savings_plan_recurring_commitment_for_billing_period',
    'product_product_name': "product['product_name']",
    'product_alarm_type': "product['alarm_type']",
    'product_attachment_type': "product['attachment_type']",
    'product_availability': "product['availability']",
    'product_availability_zone': "product['availability_zone']",
    'product_capacitystatus': "product['capacitystatus']",
    'product_category': "product['category']",
    'product_ci_type': "product['ci_type']",
    'product_classicnetworkingsupport': "product['classicnetworkingsupport']",
    'product_clock_speed': "product['clock_speed']",
    'product_current_generation': "product['current_generation']",
    'product_database_engine': "product['database_engine']",
    'product_dedicated_ebs_throughput': "product['dedicated_ebs_throughput']",
    'product_deployment_option': "product['deployment_option']",
    'product_description': "product['description']",
    'product_durability': "product['durability']",
    'product_ecu': "product['ecu']",
    'product_engine_code': "product['engine_code']",
    'product_enhanced_networking_supported': "product['enhanced_networking_supported']",
    'product_event_type': "product['event_type']",
    'product_free_query_types': "product['free_query_types']",
    'product_group': "product['group']",
    'product_group_description': "product['group_description']",
    'product_instance_type_family': "product['instance_type_family']",
    'product_intel_avx2_available': "product['intel_avx2_available']",
    'product_intel_avx_available': "product['intel_avx_available']",
    'product_intel_turbo_available': "product['intel_turbo_available']",
    'product_license_model': "product['license_model']",
    'product_logs_destination': "product['logs_destination']",
    'product_marketoption': "product['marketoption']",
    'product_max_iops_burst_performance': "product['max_iops_burst_performance']",
    'product_max_iopsvolume': "product['max_iopsvolume']",
    'product_max_throughputvolume': "product['max_throughputvolume']",
    'product_max_volume_size': "product['max_volume_size']",
    'product_memory': "product['memory']",
    'product_message_delivery_frequency': "product['message_delivery_frequency']",
    'product_message_delivery_order': "product['message_delivery_order']",
    'product_min_volume_size': "product['min_volume_size']",
    'product_network_performance': "product['network_performance']",
    'product_normalization_size_factor': "product['normalization_size_factor']",
    'product_operating_system': "product['operating_system']",
    'product_physical_processor': "product['physical_processor']",
    'product_platopricingtype': "product['platopricingtype']",
    'product_platovolumetype': "product['platovolumetype']",
    'product_pre_installed_sw': "product['pre_installed_sw']",
    'product_processor_architecture': "product['processor_architecture']",
    'product_processor_features': "product['processor_features']",
    'product_queue_type': "product['queue_type']",
    'product_region': "product['region']",
    'product_request_type': "product['request_type']",
    'product_servicename': "product['servicename']",
    'product_storage': "product['storage']",
    'product_storage_class': "product['storage_class']",
    'product_storage_media': "product['storage_media']",
    'product_tenancy': "product['tenancy']",
    'product_transfer_type': "product['transfer_type']",
    'product_vcpu': "product['vcpu']",
    'product_version': "product['version']",
    'product_volume_api_name': "product['volume_api_name']",
    'product_volume_type': "product['volume_type']",
    'product_vpcnetworkingsupport': "product['vpcnetworkingsupport']",
    'product_edition': "product['edition']",
    'product_gpu_memory': "product['gpu_memory']",
    'product_pack_size': "product['pack_size']",
    'product_q_present': "product['q_present']",
    'product_subscription_type': "product['subscription_type']",
    'product_usage_group': "product['usage_group']",
    'product_cache_engine': "product['cache_engine']",
    'product_invocation': "product['invocation']",
    'product_memory_gib': "product['memory_gib']",
    'product_time_window': "product['time_window']",
    'product_finding_group': "product['finding_group']",
    'product_finding_source': "product['finding_source']",
    'product_finding_storage': "product['finding_storage']",
    'product_standard_group': "product['standard_group']",
    'product_standard_storage': "product['standard_storage']",
    'product_product_type': "product['product_type']",
    'product_pricingplan': "product['pricingplan']",
    'product_provider': "product['provider']",
    'product_subservice': "product['subservice']",
    'product_type': "product['type']",
    'product_tickettype': 'n/a',
    'product_memorytype': 'n/a',
    'product_platousagetype': 'n/a',
    'product_with_active_users': 'n/a',
    'product_abd_instance_class': 'n/a',
    'product_size_flex': 'n/a',
    'product_engine_major_version': 'n/a',
    'product_extended_support_pricing_year': 'n/a',
    "concat('name', bill_payer_account_id)": 'bill_payer_account_name',
    "concat('name', line_item_usage_account_id)": 'line_item_usage_account_name',
}

# various types require various empty
empty = {
    'string': 'cast (null as varchar)',
    'varchar': 'cast (null as varchar)',
    'double': 'cast (null as double)',
    'timestamp(3)': 'cast (null as timestamp)',
}


class ProxyView():
    """ Proxy for CUR

    creates a proxy view for CUR
    """
    def __init__(self, cur, target_cur_version, fields_to_expose=None):
        self.cur = cur
        self.target_cur_version = target_cur_version
        self.current_cur_version = self.cur.version
        logger.debug(f'CUR proxy from {self.current_cur_version } to {self.target_cur_version }')
        self.fields_to_expose = fields_to_expose or []
        self.athena = self.cur.athena
        self.name = 'cur1_proxy'
        self.exposed_fields = []

    def read_from_athena(self):
        view_name = self.name
        _mapping = {
            'timestamp(3)': 'datetime',
            'varchar': 'string',
        }
        self.exposed_fields = dict(self.athena.query(f'''
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = '{self.athena.DatabaseName}'
            AND table_name = '{view_name}';
        '''))
        logger.debug(self.exposed_fields)

    def get_sql_expression(self, field, field_type):
        if self.current_cur_version.startswith('2') and self.target_cur_version.startswith('2'):
            return field
        if self.current_cur_version.startswith('1') and self.target_cur_version.startswith('1'):
            return field
        if self.current_cur_version.startswith('1') and self.target_cur_version.startswith('2'):
            if field_type.startswith('map'):
                map_mapping = {}
                for cur1_field in self.cur.fields:
                    if cur1_field.startswith(field + '_'):
                        map_mapping[cur1_field[len(field + '_'):]] = cur1_field
                if not map_mapping:
                    return 'cast(NULL AS MAP<VARCHAR, VARCHAR>)'
                return f'''
                    MAP(
                        ARRAY[{', '.join(["'" + key + "'" for key in map_mapping.keys()])}],
                        ARRAY[{', '.join([cur1_field for cur1_field in map_mapping.values()])}]
                    )
                '''
            cur1to2mapping = {value: key for key, value in cur2to1mapping.items()}
            if field in cur1to2mapping:
                return f'{cur1to2mapping[field]}'
            else:
                raise NotImplementedError(f'WARNING: {field} has not known equivalent')

        if self.current_cur_version.startswith('2') and self.target_cur_version.startswith('1'):
            if field.startswith('resource_tags_'):
                return f"resource_tags['{field[len('resource_tags_'):]}']"
            if field.startswith('cost_category_'):
                return f"cost_category['{field[len('cost_category_'):]}']"
            return cur2to1mapping[field]

    def create_or_update_view(self):
        self.read_from_athena()
        all_fields  = dict(self.exposed_fields)
        for field in self.fields_to_expose:
            if field not in all_fields:
                all_fields[field] = self.fields_to_expose[field]
        lines = []
        for field, field_type in all_fields.items():

            mapped_expression = self.get_sql_expression(field, field_type)
            requirement = mapped_expression.split('[')[0]
            if not re.match(r'^[a-zA-Z0-9_]+$', requirement) or self.cur.column_exists(requirement):
                expression = mapped_expression
            else:
                expression = empty.get(field_type, 'null')
            lines.append(f'{expression} {field}')
        select_block = '\n                ,'.join(lines)
        query = (f'''
            CREATE OR REPLACE VIEW "{self.name}" AS
            SELECT
                {select_block}
            FROM
                "{self.cur.table_name}"
        ''')

        logging.debug(query)
        res = self.athena.query(query)
        logging.debug(res)

    def get_table_metadata(self):
        return self.athena.get_table_metadata(self.name)


if __name__ == '__main__':

    import boto3
    from cid.helpers.athena import Athena
    from cid.helpers.glue import Glue
    from cid.helpers.cur import CUR

    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.DEBUG)
    athena = Athena(session=boto3.Session())
    glue = Glue(session=boto3.Session())
    cur = CUR(athena=athena, glue=glue)
    proxy = ProxyView(
        cur=cur,
        target_cur_version='2',
        fields_to_expose = {
            'billing_period': 'string',
            'line_item_usage_account_name': 'string',
            'identity_time_interval': 'string',
            'product': 'map',
            'resource_tags': 'map',
            'cost_category': 'map',
            'discount': 'map',
            'line_item_unblended_cost': 'double',
        },
    )
    proxy.create_or_update_view()
