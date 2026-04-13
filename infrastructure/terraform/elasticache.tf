# ── ElastiCache Redis ─────────────────────────────────────

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-subnet"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-${var.environment}-redis-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for ElastiCache Redis"

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
    description     = "Allow Redis from EKS nodes"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${var.project_name}-${var.environment}-redis"
  description          = "RegulatorAI Redis cluster"

  node_type            = var.redis_node_type
  num_cache_clusters   = var.redis_num_cache_nodes
  parameter_group_name = "default.redis7"
  port                 = 6379
  engine_version       = "7.0"

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = aws_kms_key.redis.arn

  # Maintenance
  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_retention_limit = 7
  snapshot_window          = "04:00-05:00"

  automatic_failover_enabled = var.redis_num_cache_nodes > 1

  tags = {
    Name = "${var.project_name}-${var.environment}-redis"
  }
}

resource "aws_kms_key" "redis" {
  description             = "KMS key for ElastiCache encryption at rest"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-kms"
  }
}
