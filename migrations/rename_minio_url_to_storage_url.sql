-- Migration: rename minio_url to storage_url for users who already applied the MinIO migration.
-- Only run this if your cms_images table already has a minio_url column.

ALTER TABLE cms_images CHANGE minio_url storage_url VARCHAR(500) NULL;
