environment = "prod"
aws_region  = "us-east-1"

# VPC
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# EKS
eks_cluster_version     = "1.29"
eks_node_instance_types = ["t3.xlarge"]
eks_node_desired_size   = 4
eks_node_min_size       = 3
eks_node_max_size       = 8

# RDS
rds_instance_class    = "db.r6g.xlarge"
rds_allocated_storage = 200
rds_db_name           = "regulatorai"

# ElastiCache
redis_node_type       = "cache.r6g.large"
redis_num_cache_nodes = 2

# OpenSearch
opensearch_instance_type  = "r6g.large.search"
opensearch_instance_count = 2
opensearch_volume_size    = 200
