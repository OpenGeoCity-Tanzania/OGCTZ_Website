-- Migration: add minio_url column to cms_images table
-- Run this against your MariaDB database after pulling the code update.
-- Required for MinIO image uploads in the admin panel.

ALTER TABLE cms_images ADD COLUMN minio_url VARCHAR(500) NULL;
