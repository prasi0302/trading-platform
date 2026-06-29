"""AWS CDK Stack for the Trading Application.

Provisions: VPC, ECS Fargate cluster, RDS PostgreSQL, ElastiCache Redis,
DynamoDB, S3, CloudFront, ALB with path-based routing.
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    SecretValue,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticache as elasticache,
    aws_rds as rds,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_secretsmanager as secretsmanager,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
)
from aws_cdk.aws_ecr_assets import Platform
from constructs import Construct
import os


class TradingAppStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        devops_agent_webhook_url: str = "",
        devops_agent_webhook_secret: str = "",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ============================================================
        # VPC
        # ============================================================
        vpc = ec2.Vpc(
            self, "TradingVpc",
            max_azs=2,
            nat_gateways=1,
        )

        # ============================================================
        # Security Groups
        # ============================================================
        alb_sg = ec2.SecurityGroup(self, "AlbSg", vpc=vpc, description="ALB security group")
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP from anywhere")

        ecs_sg = ec2.SecurityGroup(self, "EcsSg", vpc=vpc, description="ECS tasks security group")
        ecs_sg.add_ingress_rule(alb_sg, ec2.Port.tcp_range(8000, 8005), "From ALB")
        ecs_sg.add_ingress_rule(ecs_sg, ec2.Port.tcp_range(8000, 8005), "Inter-service")

        redis_sg = ec2.SecurityGroup(self, "RedisSg", vpc=vpc, description="Redis security group")
        redis_sg.add_ingress_rule(ecs_sg, ec2.Port.tcp(6379), "From ECS tasks")

        rds_sg = ec2.SecurityGroup(self, "RdsSg", vpc=vpc, description="RDS security group")
        rds_sg.add_ingress_rule(ecs_sg, ec2.Port.tcp(5432), "From ECS tasks")

        # ============================================================
        # ElastiCache Redis (with encryption)
        # ============================================================
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self, "RedisSubnetGroup",
            description="Redis subnet group",
            subnet_ids=[s.subnet_id for s in vpc.private_subnets],
        )

        redis_cluster = elasticache.CfnReplicationGroup(
            self, "RedisCluster",
            replication_group_description="Trading app Redis cluster",
            engine="redis",
            cache_node_type="cache.t3.micro",
            num_cache_clusters=1,
            automatic_failover_enabled=False,
            cache_subnet_group_name=redis_subnet_group.ref,
            security_group_ids=[redis_sg.security_group_id],
            transit_encryption_enabled=True,
            at_rest_encryption_enabled=True,
        )

        # ============================================================
        # RDS PostgreSQL (with Secrets Manager + encryption)
        # ============================================================
        db_instance = rds.DatabaseInstance(
            self, "TradingDb",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[rds_sg],
            database_name="trading_app",
            credentials=rds.Credentials.from_generated_secret("postgres"),
            storage_encrypted=True,
            allocated_storage=20,
            max_allocated_storage=50,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
            backup_retention=Duration.days(1),
        )

        db_secret = db_instance.secret

        # ============================================================
        # DynamoDB Table
        # ============================================================
        ticks_table = dynamodb.Table(
            self, "MarketDataTicks",
            table_name="market-data-ticks",
            partition_key=dynamodb.Attribute(name="symbol", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ============================================================
        # S3 Buckets
        # ============================================================
        historical_bucket = s3.Bucket(
            self, "HistoricalBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # ============================================================
        # ECR Repositories (for CI/CD pipeline)
        # ============================================================
        from aws_cdk import aws_ecr as ecr

        service_names = ["trading-market-data", "trading-order", "trading-portfolio", "trading-alert", "trading-ws-gateway"]
        for repo_name in service_names:
            ecr.Repository(
                self, f"Ecr{repo_name.replace('-', '')}",
                repository_name=repo_name,
                removal_policy=RemovalPolicy.DESTROY,
                empty_on_delete=True,
            )

        # ============================================================
        # ECS Cluster
        # ============================================================
        cluster = ecs.Cluster(self, "TradingCluster", vpc=vpc)

        # Shared task execution role (needs Secrets Manager access for DB secret)
        task_execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
            ],
        )
        db_secret.grant_read(task_execution_role)

        # Per-service task roles (least privilege)
        market_data_task_role = iam.Role(
            self, "MarketDataTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        ticks_table.grant_read_write_data(market_data_task_role)
        historical_bucket.grant_read_write(market_data_task_role)

        # Order, Portfolio, Alert, WsGateway — no extra AWS permissions needed
        # (DB access is via connection string, not IAM)
        order_task_role = iam.Role(
            self, "OrderTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        portfolio_task_role = iam.Role(
            self, "PortfolioTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        alert_task_role = iam.Role(
            self, "AlertTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        ws_gateway_task_role = iam.Role(
            self, "WsGatewayTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # ============================================================
        # ALB
        # ============================================================
        alb = elbv2.ApplicationLoadBalancer(
            self, "TradingAlb",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_sg,
        )

        listener = alb.add_listener("HttpListener", port=80)

        # ============================================================
        # Helper: Create Fargate Service
        # ============================================================
        def create_service(
            name: str, port: int, container_image: str,
            environment: dict, priority: int, path_patterns: list[str],
            task_role: iam.Role = order_task_role,
            secrets: dict = None,
            health_check_path: str = "/health",
        ) -> ecs.FargateService:
            task_def = ecs.FargateTaskDefinition(
                self, f"{name}TaskDef",
                cpu=256,
                memory_limit_mib=512,
                execution_role=task_execution_role,
                task_role=task_role,
            )

            container_secrets = {}
            if secrets:
                container_secrets = secrets

            # Image source: from_asset by default (local docker build via CDK).
            # Set USE_PREBUILT_IMAGES=true in the environment to instead consume
            # images that have already been pushed to ECR with the tag
            # IMAGE_TAG. This avoids needing a privileged Docker daemon on the
            # CI runner — kaniko handles image building separately and the CDK
            # only references the resulting URIs.
            use_prebuilt = os.environ.get("USE_PREBUILT_IMAGES", "").lower() == "true"
            image_tag = os.environ.get("IMAGE_TAG", "latest")

            if use_prebuilt:
                from aws_cdk import aws_ecr as ecr
                ecr_repo = ecr.Repository.from_repository_name(
                    self, f"{name}EcrRepoLookup",
                    repository_name=f"trading-app/{container_image}",
                )
                container_image_obj = ecs.ContainerImage.from_ecr_repository(
                    ecr_repo, tag=image_tag
                )
            else:
                container_image_obj = ecs.ContainerImage.from_asset(
                    directory="..",
                    file=f"services/{container_image}/Dockerfile",
                    platform=Platform.LINUX_AMD64,
                    exclude=["infra", "cdk.out", "aidlc-docs", ".kiro", ".git",
                             "node_modules", "frontend/node_modules", "frontend/dist"],
                )

            task_def.add_container(
                f"{name}Container",
                image=container_image_obj,
                port_mappings=[ecs.PortMapping(container_port=port)],
                environment=environment,
                secrets=container_secrets,
                logging=ecs.LogDrivers.aws_logs(
                    stream_prefix=name,
                    log_retention=logs.RetentionDays.ONE_WEEK,
                ),
            )

            service = ecs.FargateService(
                self, f"{name}Service",
                cluster=cluster,
                task_definition=task_def,
                desired_count=1,
                security_groups=[ecs_sg],
                assign_public_ip=False,
                health_check_grace_period=Duration.seconds(120),
            )

            target_group = elbv2.ApplicationTargetGroup(
                self, f"{name}Tg",
                vpc=vpc,
                port=port,
                protocol=elbv2.ApplicationProtocol.HTTP,
                targets=[service],
                health_check=elbv2.HealthCheck(
                    path=health_check_path,
                    interval=Duration.seconds(60),
                    timeout=Duration.seconds(10),
                    healthy_threshold_count=2,
                    unhealthy_threshold_count=5,
                ),
            )

            listener.add_target_groups(
                f"{name}Rule",
                priority=priority,
                conditions=[elbv2.ListenerCondition.path_patterns(path_patterns)],
                target_groups=[target_group],
            )

            return service

        # Redis endpoint (TLS-enabled)
        redis_url = f"rediss://{redis_cluster.attr_primary_end_point_address}:{redis_cluster.attr_primary_end_point_port}"
        db_host = db_instance.db_instance_endpoint_address

        # Inter-service communication via ALB internal DNS
        alb_dns = f"http://{alb.load_balancer_dns_name}"

        # Common environment
        common_env = {
            "REDIS_URL": redis_url,
            "LOG_LEVEL": "INFO",
        }

        # DB connection URL injected as secret (password resolved at runtime)
        db_url_secret = ecs.Secret.from_secrets_manager(db_secret, field="password")

        # ============================================================
        # Deploy Services
        # ============================================================
        services_by_name: dict[str, ecs.FargateService] = {}

        # Market Data Service (needs DynamoDB + S3)
        services_by_name["MarketData"] = create_service(
            name="MarketData", port=8001, container_image="market-data",
            task_role=market_data_task_role,
            environment={
                **common_env,
                "PORT": "8001",
                "TICK_INTERVAL_MS": "1000",
                "DYNAMODB_TABLE": ticks_table.table_name,
                "S3_BUCKET": historical_bucket.bucket_name,
            },
            priority=10, path_patterns=["/api/symbols*", "/api/market*"],
        )

        # Order Service (needs DB access via secret)
        services_by_name["Order"] = create_service(
            name="Order", port=8002, container_image="order",
            task_role=order_task_role,
            environment={
                **common_env,
                "PORT": "8002",
                "DB_HOST": db_host,
                "DB_NAME": "trading_app",
                "DB_USER": "postgres",
                "MARKET_DATA_URL": alb_dns,
                "PORTFOLIO_SERVICE_URL": alb_dns,
            },
            secrets={"DB_PASSWORD": db_url_secret},
            priority=20, path_patterns=["/api/orders*"],
        )

        # Portfolio Service (needs DB access via secret)
        services_by_name["Portfolio"] = create_service(
            name="Portfolio", port=8003, container_image="portfolio",
            task_role=portfolio_task_role,
            environment={
                **common_env,
                "PORT": "8003",
                "DB_HOST": db_host,
                "DB_NAME": "trading_app",
                "DB_USER": "postgres",
                "MARKET_DATA_URL": alb_dns,
            },
            secrets={"DB_PASSWORD": db_url_secret},
            priority=30, path_patterns=["/api/portfolio*"],
        )

        # Alert Service (Redis only, no extra permissions)
        services_by_name["Alert"] = create_service(
            name="Alert", port=8004, container_image="alert",
            task_role=alert_task_role,
            environment={
                **common_env,
                "PORT": "8004",
            },
            priority=40, path_patterns=["/api/alerts*"],
        )

        # WebSocket Gateway (Redis only, no extra permissions)
        services_by_name["WsGateway"] = create_service(
            name="WsGateway", port=8005, container_image="ws-gateway",
            task_role=ws_gateway_task_role,
            environment={
                **common_env,
                "PORT": "8005",
            },
            priority=50, path_patterns=["/ws*"],
        )

        # Default action (catch-all returns 404)
        listener.add_action(
            "DefaultAction",
            action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="application/json",
                message_body='{"detail": "Not found"}',
            ),
        )

        # ============================================================
        # CloudFront Distribution
        # ============================================================
        oai = cloudfront.OriginAccessIdentity(self, "FrontendOAI")
        frontend_bucket.grant_read(oai)

        distribution = cloudfront.Distribution(
            self, "TradingDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(frontend_bucket, origin_access_identity=oai),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        alb.load_balancer_dns_name,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    ),
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
                "/ws*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        alb.load_balancer_dns_name,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    ),
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
            },
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
            ],
        )

        # ============================================================
        # GitHub OIDC Provider + Deploy Role
        # ============================================================
        github_oidc_provider = iam.OpenIdConnectProvider(
            self, "GitHubOIDC",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        # Trust pattern controlling which GitHub repositories may assume the
        # deploy role. The default is permissive so any participant fork can
        # use it during the workshop. For a tighter, per-fork trust override
        # at deploy time:
        #
        #   cdk deploy -c github_repo_pattern="repo:OWNER/REPO:ref:refs/heads/main"
        #
        # See README "Security" for guidance on production deployments.
        github_repo_pattern = self.node.try_get_context("github_repo_pattern") \
            or "repo:*:ref:refs/heads/main"

        github_deploy_role = iam.Role(
            self, "GitHubDeployRole",
            assumed_by=iam.FederatedPrincipal(
                github_oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": github_repo_pattern,
                    },
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="Role assumed by GitHub Actions for CI/CD",
        )

        # ECR permissions
        github_deploy_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:CreateRepository",
                "ecr:DescribeRepositories",
            ],
            resources=["*"],
        ))

        # ECS deploy permissions
        github_deploy_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "ecs:DescribeServices",
                "ecs:UpdateService",
                "ecs:DescribeTaskDefinition",
                "ecs:RegisterTaskDefinition",
                "ecs:ListServices",
            ],
            resources=["*"],
        ))

        # Pass role for task definitions
        github_deploy_role.add_to_policy(iam.PolicyStatement(
            actions=["iam:PassRole"],
            resources=[
                task_execution_role.role_arn,
                market_data_task_role.role_arn,
                order_task_role.role_arn,
                portfolio_task_role.role_arn,
                alert_task_role.role_arn,
                ws_gateway_task_role.role_arn,
            ],
        ))

        # S3 + CloudFront for frontend
        github_deploy_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
            resources=[
                frontend_bucket.bucket_arn,
                f"{frontend_bucket.bucket_arn}/*",
            ],
        ))
        github_deploy_role.add_to_policy(iam.PolicyStatement(
            actions=["cloudfront:CreateInvalidation"],
            resources=["*"],
        ))

        # ============================================================
        # Lab Infrastructure (CloudWatch + EventBridge + Lambda)
        # ============================================================

        # CloudWatch Log Groups (created by ECS, reference for metric filters)
        market_data_log_group = logs.LogGroup(
            self, "MarketDataLogGroup",
            log_group_name="/ecs/MarketData",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        order_log_group = logs.LogGroup(
            self, "OrderLogGroup",
            log_group_name="/ecs/Order",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Metric Filters
        market_data_log_group.add_metric_filter(
            "IAMAccessDenied",
            filter_pattern=logs.FilterPattern.literal("AccessDeniedException"),
            metric_namespace="TradingApp",
            metric_name="IAMAccessDeniedCount",
            metric_value="1",
        )

        order_log_group.add_metric_filter(
            "OrderServiceConnectTimeout",
            filter_pattern=logs.FilterPattern.any_term("ConnectError", "TimeoutException", "ConnectTimeout", "Name or service not known"),
            metric_namespace="TradingApp",
            metric_name="OrderServiceTimeoutErrors",
            metric_value="1",
        )

        # CloudWatch Alarms (kept on existing metric filters)

        iam_alarm = cloudwatch.Alarm(
            self, "IAMAccessDeniedAlarm",
            alarm_name="TradingApp-IAM-AccessDenied",
            alarm_description="IAM AccessDeniedException observed in market-data logs",
            metric=cloudwatch.Metric(
                namespace="TradingApp",
                metric_name="IAMAccessDeniedCount",
                statistic="Sum",
                period=Duration.seconds(60),
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        timeout_alarm = cloudwatch.Alarm(
            self, "OrderServiceTimeoutAlarm",
            alarm_name="TradingApp-Order-ServiceTimeout",
            alarm_description="Order service connection-timeout pattern observed in logs",
            metric=cloudwatch.Metric(
                namespace="TradingApp",
                metric_name="OrderServiceTimeoutErrors",
                statistic="Sum",
                period=Duration.seconds(60),
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )

        # ============================================================
        # SNS Topic for Alarm Notifications
        # ============================================================
        # Alarms route to a single SNS topic; the topic triggers the webhook
        # Lambda. This mirrors the ClaimFlow/PaymentPro pattern so workshop
        # Module 0 setup is identical across the three samples.
        alarm_topic = sns.Topic(
            self, "AlarmTopic",
            topic_name="TradingApp-Alarms",
            display_name="TradingApp CloudWatch Alarms",
        )

        iam_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))
        timeout_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # Per-service "no running tasks" alarms. These fire when an ECS
        # service's running-task count falls below 1, which is what happens
        # when a deployment fails to pull its container image (Lab 1 —
        # bad-deployment) or when a task crash-loops. The agent uses these
        # alarms as the primary signal for deployment-side incidents.
        for svc_name, svc in services_by_name.items():
            no_tasks_alarm = cloudwatch.Alarm(
                self, f"{svc_name}NoTasksAlarm",
                alarm_name=f"TradingApp-{svc_name}-NoRunningTasks",
                alarm_description=f"{svc_name} service has 0 running tasks",
                metric=cloudwatch.Metric(
                    namespace="ECS/ContainerInsights",
                    metric_name="RunningTaskCount",
                    dimensions_map={
                        "ClusterName": cluster.cluster_name,
                        "ServiceName": svc.service_name,
                    },
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
                threshold=1,
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            no_tasks_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # ============================================================
        # DevOps Agent Webhook Secret (Secrets Manager)
        # ============================================================
        # The webhook URL is configuration (env var); the HMAC shared secret
        # is a credential and lives in Secrets Manager. When the deployer does
        # not supply a value, no Secrets Manager resource is created and the
        # Lambda short-circuits at invocation time. Workshop Module 0 sets
        # the secret via:
        #   cdk deploy -c devops_agent_webhook_url=<url> \
        #              -c devops_agent_webhook_secret=<secret>
        webhook_secret_arn = ""
        if devops_agent_webhook_secret:
            webhook_secret = secretsmanager.Secret(
                self, "DevOpsAgentWebhookSecret",
                secret_name="trading-app/devops-agent-webhook-secret",
                description="HMAC-SHA256 shared secret used to sign DevOps Agent webhook payloads.",
                secret_string_value=SecretValue.unsafe_plain_text(devops_agent_webhook_secret),
            )
            webhook_secret_arn = webhook_secret.secret_arn

        # ============================================================
        # DevOps Agent Webhook Lambda
        # ============================================================
        webhook_fn = _lambda.Function(
            self, "DevOpsWebhookFn",
            function_name="TradingApp-DevOpsAgent-Webhook",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="devops_agent_webhook.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "WEBHOOK_URL": devops_agent_webhook_url,
                # Lambda reads the secret value at invocation time using this ARN.
                # Empty string ⇒ short-circuits without invoking the webhook.
                "WEBHOOK_SECRET_ARN": webhook_secret_arn,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Forwards CloudWatch Alarms to AWS DevOps Agent for auto-investigation",
        )

        # CloudWatch read access for the webhook payload enrichment
        webhook_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["cloudwatch:DescribeAlarms", "cloudwatch:DescribeAlarmHistory"],
            resources=["*"],
        ))

        # Grant Secrets Manager read on the single secret ARN (only when configured)
        if devops_agent_webhook_secret:
            webhook_secret.grant_read(webhook_fn)

        # SNS topic → Lambda subscription
        alarm_topic.add_subscription(sns_subs.LambdaSubscription(webhook_fn))

        # ============================================================
        # Outputs
        # ============================================================
        CfnOutput(self, "CloudFrontUrl",
                  value=f"https://{distribution.distribution_domain_name}",
                  description="Application URL (CloudFront)")
        CfnOutput(self, "AlbUrl",
                  value=f"http://{alb.load_balancer_dns_name}",
                  description="ALB URL (direct backend access)")
        CfnOutput(self, "FrontendBucketName",
                  value=frontend_bucket.bucket_name,
                  description="S3 bucket for frontend assets")
        CfnOutput(self, "RedisEndpoint",
                  value=redis_cluster.attr_primary_end_point_address,
                  description="Redis endpoint")
        CfnOutput(self, "RdsEndpoint",
                  value=db_instance.db_instance_endpoint_address,
                  description="RDS endpoint")
        CfnOutput(self, "DbSecretArn",
                  value=db_secret.secret_arn,
                  description="RDS credentials secret ARN")
        CfnOutput(self, "GitHubDeployRoleArn",
                  value=github_deploy_role.role_arn,
                  description="IAM role ARN for GitHub Actions OIDC")
        CfnOutput(self, "EcsClusterName",
                  value=cluster.cluster_name,
                  description="ECS cluster name")
        CfnOutput(self, "DistributionId",
                  value=distribution.distribution_id,
                  description="CloudFront distribution ID")
        CfnOutput(self, "WebhookLambdaName",
                  value=webhook_fn.function_name,
                  description="DevOps Agent webhook Lambda name")
        CfnOutput(self, "AlarmTopicArn",
                  value=alarm_topic.topic_arn,
                  description="SNS topic that fans out CloudWatch alarms to the webhook Lambda")
