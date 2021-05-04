-- upgrade --
ALTER TABLE "notification" ADD "is_sent" BOOL NOT NULL  DEFAULT True;
-- downgrade --
ALTER TABLE "notification" DROP COLUMN "is_sent";
