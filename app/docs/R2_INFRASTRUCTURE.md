# Cloudflare R2 Infrastructure Documentation

## Overview

Beat Forge uses a two-bucket Cloudflare R2 storage architecture for audio file management:

- **audio-private**: Private bucket for original uploads, processed files, and stems (access controlled)
- **audio-public**: Public bucket for streaming files (publicly accessible with CORS)

## Current Bucket Configuration

### Environment Variables

```env
# R2 Authentication
R2_ACCESS_KEY_ID=your_access_key_id
R2_SECRET_ACCESS_KEY=your_secret_access_key

# Private Bucket (for original uploads, processed files, stems - access controlled)
R2_PRIVATE_BUCKET=audio-private
R2_PRIVATE_ENDPOINT=https://269eb01228379eea0a8b591aee2544f5.r2.cloudflarestorage.com

# Public Bucket (for streaming files - publicly accessible)
R2_PUBLIC_BUCKET=audio-public
R2_PUBLIC_ENDPOINT=https://269eb01228379eea0a8b591aee2544f5.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://pub-8a24a10ad9344723ab338aea65b02338.r2.dev

# Laravel Filesystem Configuration
FILESYSTEM_DISK=r2
```

### Directory Structure

#### audio-private Bucket
```
/
├── uploads/          # Original user uploads
│   └── {user_id}/
│       └── {Y/m/d}/
│           └── filename.ext
├── processed/        # Processed audio files
│   └── {user_id}/
│       └── {Y/m/d}/
│           └── filename.ext
└── stems/           # Audio stem separation files
    └── {user_id}/
        └── {Y/m/d}/
            └── filename.ext
```

#### audio-public Bucket
```
/
└── uploads/
    └── stream/      # Streaming-optimized files (OGG format)
        └── {user_id}/
            └── {Y/m/d}/
                └── filename.ogg
```

## CORS Configuration

The audio-public bucket has CORS configured to allow audio streaming from the web application.

### Current CORS Policy

```json
{
  "rules": [
    {
      "allowed": {
        "origins": ["http://localhost:8000", "http://localhost:3000"],
        "methods": ["GET", "HEAD"],
        "headers": ["*"]
      },
      "exposeHeaders": ["content-length", "content-type"],
      "maxAgeSeconds": 3600
    }
  ]
}
```

### Managing CORS with Wrangler

List current CORS configuration:
```bash
npx wrangler r2 bucket cors list audio-public
```

Update CORS configuration:
```bash
# Create cors-config.json with the above JSON structure
npx wrangler r2 bucket cors set audio-public --file cors-config.json
```

Clear CORS configuration:
```bash
npx wrangler r2 bucket cors delete audio-public
```

## Infrastructure as Code (Terraform)

### Prerequisites

1. Install Terraform
2. Configure Cloudflare API token with R2 permissions
3. Set up Terraform Cloud or local state management

### Terraform Configuration

Create a `terraform/` directory in your project with the following files:

#### `terraform/providers.tf`

```hcl
terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
```

#### `terraform/variables.tf`

```hcl
variable "cloudflare_api_token" {
  description = "Cloudflare API token with R2 permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., production, staging, development)"
  type        = string
  default     = "development"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "beat-forge"
}

variable "allowed_origins" {
  description = "Allowed origins for CORS policy"
  type        = list(string)
  default     = ["http://localhost:8000", "http://localhost:3000"]
}
```

#### `terraform/r2.tf`

```hcl
# Private bucket for uploads, processed files, and stems
resource "cloudflare_r2_bucket" "audio_private" {
  account_id = var.cloudflare_account_id
  name       = "${var.project_name}-audio-private-${var.environment}"
  location   = "auto"
}

# Public bucket for streaming files
resource "cloudflare_r2_bucket" "audio_public" {
  account_id = var.cloudflare_account_id
  name       = "${var.project_name}-audio-public-${var.environment}"
  location   = "auto"
}

# CORS configuration for public bucket
resource "cloudflare_r2_bucket_cors" "audio_public_cors" {
  account_id = var.cloudflare_account_id
  bucket     = cloudflare_r2_bucket.audio_public.name

  cors_rule {
    allowed_origins = var.allowed_origins
    allowed_methods = ["GET", "HEAD"]
    allowed_headers = ["*"]
    expose_headers  = ["content-length", "content-type"]
    max_age_seconds = 3600
  }
}

# Custom domain for public bucket (optional)
resource "cloudflare_r2_bucket_custom_domain" "audio_public_domain" {
  count      = var.custom_domain != null ? 1 : 0
  account_id = var.cloudflare_account_id
  bucket     = cloudflare_r2_bucket.audio_public.name
  domain     = var.custom_domain
}
```

#### `terraform/outputs.tf`

```hcl
output "audio_private_bucket_name" {
  description = "Name of the private audio bucket"
  value       = cloudflare_r2_bucket.audio_private.name
}

output "audio_public_bucket_name" {
  description = "Name of the public audio bucket"
  value       = cloudflare_r2_bucket.audio_public.name
}

output "audio_private_endpoint" {
  description = "Endpoint URL for the private audio bucket"
  value       = "https://${var.cloudflare_account_id}.r2.cloudflarestorage.com"
}

output "audio_public_endpoint" {
  description = "Endpoint URL for the public audio bucket"
  value       = "https://${var.cloudflare_account_id}.r2.cloudflarestorage.com"
}

output "audio_public_url" {
  description = "Public URL for the audio streaming bucket"
  value       = "https://${cloudflare_r2_bucket.audio_public.name}.r2.dev"
}

output "r2_credentials" {
  description = "R2 access credentials (sensitive)"
  value = {
    access_key_id     = cloudflare_r2_bucket.audio_private.access_key_id
    secret_access_key = cloudflare_r2_bucket.audio_private.secret_access_key
  }
  sensitive = true
}
```

#### `terraform/terraform.tfvars.example`

```hcl
cloudflare_api_token    = "your_api_token_here"
cloudflare_account_id   = "your_account_id_here"
environment            = "production"
project_name           = "beat-forge"
allowed_origins        = ["https://yourdomain.com", "https://www.yourdomain.com"]
custom_domain          = "cdn.yourdomain.com"  # Optional
```

### Deployment Commands

1. **Initialize Terraform:**
   ```bash
   cd terraform
   terraform init
   ```

2. **Plan deployment:**
   ```bash
   terraform plan -var-file="terraform.tfvars"
   ```

3. **Apply infrastructure:**
   ```bash
   terraform apply -var-file="terraform.tfvars"
   ```

4. **Update environment variables:**
   After deployment, update your `.env` file with the Terraform outputs:
   ```bash
   terraform output -json > terraform_outputs.json
   # Parse outputs and update .env file accordingly
   ```

### Multi-Environment Setup

For different environments (development, staging, production), create separate variable files:

- `terraform/environments/development.tfvars`
- `terraform/environments/staging.tfvars`
- `terraform/environments/production.tfvars`

Deploy specific environments:
```bash
terraform workspace new production
terraform apply -var-file="environments/production.tfvars"
```

## Bucket Management Commands

### Using Wrangler

List all buckets:
```bash
npx wrangler r2 bucket list
```

Create a bucket:
```bash
npx wrangler r2 bucket create <bucket-name>
```

Delete a bucket:
```bash
npx wrangler r2 bucket delete <bucket-name>
```

List objects in bucket:
```bash
npx wrangler r2 object list <bucket-name>
```

Enable/disable public access:
```bash
npx wrangler r2 bucket public <bucket-name> enable
npx wrangler r2 bucket public <bucket-name> disable
```

### Using Laravel Artisan

The application includes custom Artisan commands for R2 management:

Clear R2 buckets (complete reset):
```bash
php artisan migrate:fresh-with-microservice --seed
```

Check microservice integration:
```bash
php artisan audio:migrate --type=fresh --force
```

Clear upload storage only:
```bash
php artisan uploads:clear --force
```

## Security Considerations

1. **Private Bucket Access**: The audio-private bucket should never be publicly accessible. All access should be through signed URLs or application-controlled access.

2. **CORS Policy**: Keep CORS origins restrictive. Only add domains that need direct browser access to audio files.

3. **API Tokens**: Use API tokens with minimal required permissions for R2 operations.

4. **Environment Separation**: Use separate buckets for different environments to prevent data mixing.

5. **Backup Strategy**: Implement regular backups of critical audio files, especially user uploads.

## Monitoring and Alerting

Consider setting up:

1. **Cloudflare Analytics**: Monitor bucket usage, request patterns, and costs
2. **Storage Quotas**: Set up alerts for storage usage thresholds
3. **CORS Errors**: Monitor for CORS-related errors in application logs
4. **Upload Failures**: Track failed uploads and processing errors

## Cost Optimization

1. **Lifecycle Policies**: Implement policies to delete or archive old processed files
2. **Storage Classes**: Use appropriate storage classes for different file types
3. **CDN Integration**: Consider CDN for frequently accessed streaming files
4. **Compression**: Ensure audio files are properly compressed for streaming

## Troubleshooting

### Common Issues

1. **CORS Errors**: Verify CORS policy allows your domain and required methods
2. **Access Denied**: Check R2 credentials and bucket permissions
3. **File Not Found**: Verify file paths match the expected directory structure
4. **Upload Failures**: Check file size limits and bucket quotas

### Debug Commands

Check bucket CORS:
```bash
npx wrangler r2 bucket cors list <bucket-name>
```

Test file access:
```bash
curl -H "Origin: http://localhost:8000" -I "https://your-bucket.r2.dev/path/to/file"
```

Check bucket contents:
```bash
npx wrangler r2 object list <bucket-name> --prefix="uploads/"
```