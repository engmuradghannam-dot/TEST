terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  backend "s3" {
    bucket         = "nexus-terraform-state"
    key            = "multi-region/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "nexus-terraform-locks"
  }
}

# Provider configurations for each region
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
}

provider "aws" {
  alias  = "me_south_1"
  region = "me-south-1"
}

# EKS clusters per region
module "eks_us_east_1" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  providers = {
    aws = aws.us_east_1
  }

  cluster_name    = "nexus-us-east-1"
  cluster_version = "1.29"

  vpc_id     = module.vpc_us_east_1.vpc_id
  subnet_ids = module.vpc_us_east_1.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 10

      instance_types = ["m6i.xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        workload = "general"
      }

      taints = []

      update_config = {
        max_unavailable_percentage = 25
      }
    }

    spot = {
      desired_size = 2
      min_size     = 1
      max_size     = 5

      instance_types = ["m6i.large", "m5.large", "m5a.large"]
      capacity_type  = "SPOT"

      labels = {
        workload = "spot"
      }

      taints = [{
        key    = "spot"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  tags = {
    Region    = "us-east-1"
    Priority  = "primary"
    ManagedBy = "terraform"
  }
}

module "eks_eu_west_1" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  providers = {
    aws = aws.eu_west_1
  }

  cluster_name    = "nexus-eu-west-1"
  cluster_version = "1.29"

  vpc_id     = module.vpc_eu_west_1.vpc_id
  subnet_ids = module.vpc_eu_west_1.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 2
      min_size     = 1
      max_size     = 6
      instance_types = ["m6i.large"]
      capacity_type  = "ON_DEMAND"
    }
  }

  tags = {
    Region    = "eu-west-1"
    Priority  = "secondary"
    ManagedBy = "terraform"
  }
}

module "eks_me_south_1" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  providers = {
    aws = aws.me_south_1
  }

  cluster_name    = "nexus-me-south-1"
  cluster_version = "1.29"

  vpc_id     = module.vpc_me_south_1.vpc_id
  subnet_ids = module.vpc_me_south_1.private_subnets

  eks_managed_node_groups = {
    general = {
      desired_size = 2
      min_size     = 1
      max_size     = 6
      instance_types = ["m6i.large"]
      capacity_type  = "ON_DEMAND"
    }
  }

  tags = {
    Region    = "me-south-1"
    Priority  = "secondary"
    ManagedBy = "terraform"
  }
}

# Global Accelerator for multi-region routing
resource "aws_globalaccelerator_accelerator" "nexus" {
  provider        = aws.us_east_1
  name            = "nexus-global"
  ip_address_type = "DUAL_STACK"
  enabled         = true

  attributes {
    flow_logs_enabled   = true
    flow_logs_s3_bucket = aws_s3_bucket.flow_logs.id
    flow_logs_s3_prefix = "global-accelerator/"
  }
}

resource "aws_globalaccelerator_listener" "nexus_http" {
  provider        = aws.us_east_1
  accelerator_arn = aws_globalaccelerator_accelerator.nexus.id
  client_affinity = "SOURCE_IP"
  protocol        = "TCP"

  port_range {
    from_port = 80
    to_port   = 80
  }

  port_range {
    from_port = 443
    to_port   = 443
  }
}

resource "aws_globalaccelerator_endpoint_group" "nexus_us" {
  provider       = aws.us_east_1
  listener_arn   = aws_globalaccelerator_listener.nexus_http.id
  endpoint_group_region = "us-east-1"

  health_check_protocol = "HTTP"
  health_check_port     = 80
  health_check_path     = "/api/health/"
  threshold_count       = 3

  traffic_dial_percentage = 50

  endpoint_configuration {
    endpoint_id                    = module.eks_us_east_1.cluster_endpoint
    weight                         = 50
    client_ip_preservation_enabled = true
    health_check_port              = 80
  }
}

resource "aws_globalaccelerator_endpoint_group" "nexus_eu" {
  provider       = aws.us_east_1
  listener_arn   = aws_globalaccelerator_listener.nexus_http.id
  endpoint_group_region = "eu-west-1"

  health_check_protocol = "HTTP"
  health_check_port     = 80
  health_check_path     = "/api/health/"
  threshold_count       = 3

  traffic_dial_percentage = 30

  endpoint_configuration {
    endpoint_id                    = module.eks_eu_west_1.cluster_endpoint
    weight                         = 30
    client_ip_preservation_enabled = true
    health_check_port              = 80
  }
}

resource "aws_globalaccelerator_endpoint_group" "nexus_me" {
  provider       = aws.us_east_1
  listener_arn   = aws_globalaccelerator_listener.nexus_http.id
  endpoint_group_region = "me-south-1"

  health_check_protocol = "HTTP"
  health_check_port     = 80
  health_check_path     = "/api/health/"
  threshold_count       = 3

  traffic_dial_percentage = 20

  endpoint_configuration {
    endpoint_id                    = module.eks_me_south_1.cluster_endpoint
    weight                         = 20
    client_ip_preservation_enabled = true
    health_check_port              = 80
  }
}

# Cross-region RDS Aurora Global Database
resource "aws_rds_global_cluster" "nexus" {
  provider              = aws.us_east_1
  global_cluster_identifier = "nexus-global-db"
  engine                = "aurora-postgresql"
  engine_version        = "15.4"
  database_name         = "nexus"
  storage_encrypted     = true
}

resource "aws_rds_cluster" "nexus_primary" {
  provider              = aws.us_east_1
  cluster_identifier    = "nexus-primary"
  global_cluster_identifier = aws_rds_global_cluster.nexus.id
  engine                = "aurora-postgresql"
  engine_version        = "15.4"
  engine_mode           = "provisioned"

  database_name         = "nexus"
  master_username       = "nexus_admin"
  master_password       = var.db_master_password

  db_subnet_group_name   = module.vpc_us_east_1.database_subnet_group_name
  vpc_security_group_ids   = [aws_security_group.rds_us_east_1.id]

  backup_retention_period = 35
  preferred_backup_window = "03:00-04:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "nexus-final-snapshot"

  serverlessv2_scaling_configuration {
    min_capacity = 2
    max_capacity = 64
  }
}

resource "aws_rds_cluster_instance" "nexus_primary" {
  provider           = aws.us_east_1
  identifier         = "nexus-primary-instance"
  cluster_identifier = aws_rds_cluster.nexus_primary.id
  instance_class     = "db.serverless"
  engine             = "aurora-postgresql"
}

resource "aws_rds_cluster" "nexus_secondary_eu" {
  provider              = aws.eu_west_1
  cluster_identifier    = "nexus-secondary-eu"
  global_cluster_identifier = aws_rds_global_cluster.nexus.id
  engine                = "aurora-postgresql"
  engine_version        = "15.4"
  engine_mode           = "provisioned"

  db_subnet_group_name   = module.vpc_eu_west_1.database_subnet_group_name
  vpc_security_group_ids   = [aws_security_group.rds_eu_west_1.id]

  backup_retention_period = 35

  serverlessv2_scaling_configuration {
    min_capacity = 1
    max_capacity = 32
  }
}

resource "aws_rds_cluster_instance" "nexus_secondary_eu" {
  provider           = aws.eu_west_1
  identifier         = "nexus-secondary-eu-instance"
  cluster_identifier = aws_rds_cluster.nexus_secondary_eu.id
  instance_class     = "db.serverless"
  engine             = "aurora-postgresql"
}

# ElastiCache Global Datastore
resource "aws_elasticache_global_replication_group" "nexus" {
  provider = aws.us_east_1

  global_replication_group_id_suffix = "nexus-cache"
  primary_replication_group_id       = aws_elasticache_replication_group.nexus_us.id

  automatic_failover_enabled = true
}

resource "aws_elasticache_replication_group" "nexus_us" {
  provider = aws.us_east_1

  replication_group_id = "nexus-cache-us"
  description          = "Nexus cache cluster US East"

  node_type            = "cache.r6g.xlarge"
  num_cache_clusters   = 2

  automatic_failover_enabled = true
  multi_az_enabled          = true

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  snapshot_retention_limit = 7
  snapshot_window         = "05:00-06:00"
}

resource "aws_elasticache_replication_group" "nexus_eu" {
  provider = aws.eu_west_1

  replication_group_id = "nexus-cache-eu"
  description          = "Nexus cache cluster EU West"

  global_replication_group_id = aws_elasticache_global_replication_group.nexus.id

  num_cache_clusters = 2

  automatic_failover_enabled = true
}

# S3 Cross-Region Replication
resource "aws_s3_bucket" "nexus_assets" {
  provider = aws.us_east_1
  bucket   = "nexus-assets-global"
}

resource "aws_s3_bucket_versioning" "nexus_assets" {
  provider = aws.us_east_1
  bucket   = aws_s3_bucket.nexus_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_replication_configuration" "nexus_assets" {
  provider = aws.us_east_1
  role   = aws_iam_role.replication.arn
  bucket = aws_s3_bucket.nexus_assets.id

  rule {
    id     = "replicate-to-eu"
    status = "Enabled"
    priority = 1

    destination {
      bucket        = aws_s3_bucket.nexus_assets_eu.arn
      storage_class = "STANDARD"

      replication_time {
        status  = "Enabled"
        minutes = 15
      }

      metrics {
        status  = "Enabled"
        minutes = 15
      }
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }
}
