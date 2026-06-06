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
)
from aws_cdk.aws_ecr_assets import Platform
from constructs import Construct


class TradingAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
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
        # ElastiCache Redis
        # ============================================================
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self, "RedisSubnetGroup",
            description="Redis subnet group",
            subnet_ids=[s.subnet_id for s in vpc.private_subnets],
        )

        redis_cluster = elasticache.CfnCacheCluster(
            self, "RedisCluster",
            cache_node_type="cache.t3.micro",
            engine="redis",
            num_cache_nodes=1,
            vpc_security_group_ids=[redis_sg.security_group_id],
            cache_subnet_group_name=redis_subnet_group.ref,
        )

        # ============================================================
        # RDS PostgreSQL
        # ============================================================
        db_instance = rds.DatabaseInstance(
            self, "TradingDb",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[rds_sg],
            database_name="trading_app",
            credentials=rds.Credentials.from_password(
                username="postgres",
                password=SecretValue.unsafe_plain_text("TradingApp2026!"),
            ),
            allocated_storage=20,
            max_allocated_storage=50,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
            backup_retention=Duration.days(1),
        )

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
        )

        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # ============================================================
        # ECS Cluster
        # ============================================================
        cluster = ecs.Cluster(self, "TradingCluster", vpc=vpc)

        # Shared task execution role
        task_execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
            ],
        )

        # Shared task role with permissions
        task_role = iam.Role(
            self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        ticks_table.grant_read_write_data(task_role)
        historical_bucket.grant_read_write(task_role)

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
            health_check_path: str = "/health",
        ) -> ecs.FargateService:
            task_def = ecs.FargateTaskDefinition(
                self, f"{name}TaskDef",
                cpu=256,
                memory_limit_mib=512,
                execution_role=task_execution_role,
                task_role=task_role,
            )

            task_def.add_container(
                f"{name}Container",
                image=ecs.ContainerImage.from_asset(
                    directory="..",
                    file=f"services/{container_image}/Dockerfile",
                    platform=Platform.LINUX_AMD64,
                    exclude=["infra", "cdk.out", "aidlc-docs", ".kiro", ".git",
                             "node_modules", "frontend/node_modules", "frontend/dist"],
                ),
                port_mappings=[ecs.PortMapping(container_port=port)],
                environment=environment,
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

        # Redis and DB endpoints
        redis_url = f"redis://{redis_cluster.attr_redis_endpoint_address}:6379"
        db_host = db_instance.db_instance_endpoint_address
        # Use explicit password for workshop
        db_url = f"postgresql+asyncpg://postgres:TradingApp2026!@{db_host}:5432/trading_app"

        # Inter-service communication via ALB internal DNS
        alb_dns = f"http://{alb.load_balancer_dns_name}"

        # Common environment
        common_env = {
            "REDIS_URL": redis_url,
            "AWS_REGION": "us-east-1",
            "LOG_LEVEL": "INFO",
        }

        # ============================================================
        # Deploy Services
        # ============================================================

        # Market Data Service
        create_service(
            name="MarketData", port=8001, container_image="market-data",
            environment={
                **common_env,
                "PORT": "8001",
                "TICK_INTERVAL_MS": "1000",
                "DYNAMODB_TABLE": ticks_table.table_name,
                "S3_BUCKET": historical_bucket.bucket_name,
            },
            priority=10, path_patterns=["/api/symbols*", "/api/market*"],
        )

        # Order Service
        create_service(
            name="Order", port=8002, container_image="order",
            environment={
                **common_env,
                "PORT": "8002",
                "DATABASE_URL": db_url,
                "MARKET_DATA_URL": alb_dns,
                "PORTFOLIO_SERVICE_URL": alb_dns,
            },
            priority=20, path_patterns=["/api/orders*"],
        )

        # Portfolio Service
        create_service(
            name="Portfolio", port=8003, container_image="portfolio",
            environment={
                **common_env,
                "PORT": "8003",
                "DATABASE_URL": db_url,
                "MARKET_DATA_URL": alb_dns,
            },
            priority=30, path_patterns=["/api/portfolio*"],
        )

        # Alert Service
        create_service(
            name="Alert", port=8004, container_image="alert",
            environment={
                **common_env,
                "PORT": "8004",
            },
            priority=40, path_patterns=["/api/alerts*"],
        )

        # WebSocket Gateway
        create_service(
            name="WsGateway", port=8005, container_image="ws-gateway",
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
                  value=redis_cluster.attr_redis_endpoint_address,
                  description="Redis endpoint")
        CfnOutput(self, "RdsEndpoint",
                  value=db_instance.db_instance_endpoint_address,
                  description="RDS endpoint")
