-- upgrade --
ALTER TABLE "notification" ALTER COLUMN "notification_type" TYPE VARCHAR(16) USING "notification_type"::VARCHAR(16);
-- downgrade --
ALTER TABLE "notification" ALTER COLUMN "notification_type" TYPE VARCHAR(16) USING "notification_type"::VARCHAR(16);
