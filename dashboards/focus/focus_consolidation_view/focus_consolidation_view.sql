-- This is an example veiw for consolidation of AWS, Azure, GCP and OCI data. 
-- Choose only FOCUS tables that you have deployed. See more https://catalog.workshops.aws/awscid/en-US/dashboards/additional/focus#add-focus-data-from-other-cloud-providers-to-focus-dashboard
-- Please modify databases and table names as required.


CREATE OR REPLACE VIEW "focus_consolidation_view" AS 
SELECT
  AvailabilityZone
, BilledCost
, BillingAccountId
, BillingAccountName
, BillingCurrency
, BillingPeriodEnd
, BillingPeriodStart
, ChargeCategory
, ChargeClass
, ChargeDescription
, ChargeFrequency
, ChargePeriodEnd
, ChargePeriodStart
, CommitmentDiscountCategory
, CommitmentDiscountId
, CommitmentDiscountName
, CommitmentDiscountType
, CommitmentDiscountStatus
, ConsumedQuantity
, ConsumedUnit
, ContractedCost
, ContractedUnitPrice
, EffectiveCost
, InvoiceIssuerName
, ListCost
, ListUnitPrice
, PricingCategory
, PricingQuantity
, PricingUnit
, ProviderName
, PublisherName
, RegionId
, RegionName
, ResourceId
, ResourceName
, ResourceType
, ServiceCategory
, ServiceName
, SkuId
, SkuPriceId
, SubAccountId
, SubAccountName
, Tags
, billing_period
FROM
  "cid_data_export"."focus"

UNION ALL 

SELECT
  null AvailabilityZone
, BilledCost
, BillingAccountId
, BillingAccountName
, BillingCurrency
, BillingPeriodEnd
, BillingPeriodStart
, ChargeCategory
, ChargeClass
, ChargeDescription
, ChargeFrequency
, ChargePeriodEnd
, ChargePeriodStart
, CommitmentDiscountCategory
, CommitmentDiscountId
, CommitmentDiscountName
, CommitmentDiscountType
, CommitmentDiscountStatus
, ConsumedQuantity
, ConsumedUnit
, ContractedCost
, ContractedUnitPrice
, EffectiveCost
, InvoiceIssuerName
, ListCost
, ListUnitPrice
, PricingCategory
, PricingQuantity
, PricingUnit
, ProviderName
, PublisherName
, RegionId
, RegionName
, ResourceId
, ResourceName
, ResourceType
, ServiceCategory
, ServiceName
, SkuId
, SkuPriceId
, SubAccountId
, SubAccountName
, Tags
, billing_period
FROM
  "cidgldpdcidazure"."cidgltpdcidazure"

UNION ALL

SELECT
  AvailabilityZone
, BilledCost
, BillingAccountId
, BillingAccountName
, BillingCurrency
, BillingPeriodEnd
, BillingPeriodStart
, ChargeCategory
, null ChargeClass
, ChargeDescription
, ChargeFrequency
, ChargePeriodEnd
, ChargePeriodStart
, CommitmentDiscountCategory
, CommitmentDiscountId
, CommitmentDiscountName
, CommitmentDiscountType
, null CommitmentDiscountStatus
, null ConsumedQuantity
, null ConsumedUnit
, null ContractedCost
, null ContractedUnitPrice
, EffectiveCost
, invoiceissuer InvoiceIssuerName
, ListCost
, ListUnitPrice
, PricingCategory
, PricingQuantity
, PricingUnit
, provider ProviderName
, publisher PublisherName
, region RegionId
, region RegionName
, ResourceId
, ResourceName
, ResourceType
, ServiceCategory
, ServiceName
, SkuId
, SkuPriceId
, SubAccountId
, SubAccountName
, null Tags
, billing_period
FROM
  "cid_oci_focus_data_export_dv"."focus"

UNION ALL

SELECT
  AvailabilityZone
, BilledCost
, BillingAccountId
, null BillingAccountName
, BillingCurrency
, null BillingPeriodEnd
, CAST(BillingPeriodStart AS Date) BillingPeriodStart
, ChargeCategory
, ChargeClass
, ChargeDescription
, null ChargeFrequency
, null ChargePeriodEnd
, CAST(ChargePeriodStart AS date) ChargePeriodStart
, CommitmentDiscountCategory
, CommitmentDiscountId
, CommitmentDiscountName
, null CommitmentDiscountType
, null CommitmentDiscountStatus
, ConsumedQuantity
, ConsumedUnit
, ContractedCost
, ContractedUnitPrice
, EffectiveCost
, null InvoiceIssuerName
, ListCost
, ListUnitPrice
, PricingCategory
, PricingQuantity
, PricingUnit
, ProviderName
, PublisherName
, RegionId
, RegionName
, null ResourceId
, null ResourceName
, null ResourceType
, array_join(ServiceCategory, ',') ServiceCategory
, ServiceName
, SkuId
, SkuPriceId
, SubAccountId
, null SubAccountName
, null Tags
, date_format(CAST(BillingPeriodStart AS date), '%Y-%m') billing_period
FROM
  "gcpapp_db"."gcp_focus_export"
