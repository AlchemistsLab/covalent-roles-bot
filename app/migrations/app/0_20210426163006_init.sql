-- upgrade --
CREATE TABLE IF NOT EXISTS "notification" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "text" VARCHAR(255) NOT NULL,
    "notification_type" VARCHAR(16) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "uid_notificatio_user_id_1f9a86" UNIQUE ("user_id", "channel_id", "notification_type")
);
COMMENT ON COLUMN "notification"."notification_type" IS 'GREET_APPRENTICE: greet_apprentice\nGREET_VALIANT: greet_valiant\nGREET_MASTER: greet_master';
COMMENT ON TABLE "notification" IS 'Notification table';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
