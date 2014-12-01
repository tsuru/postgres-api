--
-- Name: plan_enum; Type: TYPE; Schema: public
--

CREATE TYPE plan_enum AS ENUM (
    'shared',
    'dedicated'
);

--
-- Name: instance; Type: TABLE; Schema: public
--

ALTER TABLE instance
    DROP COLUMN shared,
    ADD COLUMN plan plan_enum NOT NULL DEFAULT 'shared',
    ADD COLUMN container_id varchar(255) NULL,
    ADD COLUMN host varchar(255) NULL,
    ADD COLUMN port integer NULL,
    ADD COLUMN admin_user varchar(255) NULL,
    ADD COLUMN admin_password varchar(255) NULL;
