## Federated Authentication
QuickSight dashboard authentication and authorization can use Entra ID (formerly Azure Active Directory).

1. Set up Entra ID integration with QuickSight:

    - This is a manual process that requires configuration in both the Entra ID portal and QuickSight.

1. Configure QuickSight Enterprise edition:

    - Can be partially automated using CloudFormation.
    - Use the AWS::QuickSight::AccountSubscription resource to set up QuickSight Enterprise.

1. Set up Identity Provider (IdP) in QuickSight:

    - Partially automatable using CloudFormation.
    - Use AWS::QuickSight::IdentityProvider resource to configure the IdP.

1. Create and configure QuickSight users and groups:

    - Can be automated using CloudFormation.
    - Use AWS::QuickSight::User and AWS::QuickSight::Group resources.

1. Configure dashboard permissions:

    - Can be automated using CloudFormation.
    - Use AWS::QuickSight::DashboardPermissions resource.