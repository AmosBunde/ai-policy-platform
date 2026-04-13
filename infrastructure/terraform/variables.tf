variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "regulatorai"
}

# ── VPC ───────────────────────────────────────────────────

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# ── EKS ───────────────────────────────────────────────────

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_types" {
  description = "EC2 instance types for EKS managed node group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "eks_node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "eks_node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 2
}

variable "eks_node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 6
}

# ── RDS ───────────────────────────────────────────────────

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_db_name" {
  description = "Database name"
  type        = string
  default     = "regulatorai"
}

variable "rds_master_username" {
  description = "Master username for RDS"
  type        = string
  default     = "regulatorai_admin"
  sensitive   = true
}

variable "rds_master_password" {
  description = "Master password for RDS"
  type        = string
  sensitive   = true
}

# ── ElastiCache ───────────────────────────────────────────

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 2
}

# ── OpenSearch ────────────────────────────────────────────

variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "r6g.large.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch data nodes"
  type        = number
  default     = 2
}

variable "opensearch_volume_size" {
  description = "EBS volume size in GB per OpenSearch node"
  type        = number
  default     = 100
}
