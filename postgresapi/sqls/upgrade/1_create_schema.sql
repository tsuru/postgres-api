--
-- Name: state_enum; Type: TYPE; Schema: public
--

CREATE TYPE state_enum AS ENUM (
    'pending',
    'running',
    'error'
);

--
-- Name: instance; Type: TABLE; Schema: public
--

CREATE TABLE instance (
    name character varying(256) NOT NULL,
    state state_enum NOT NULL,
    shared boolean NOT NULL
);

--
-- Name: instance_pkey; Type: CONSTRAINT; Schema: public
--

ALTER TABLE ONLY instance
    ADD CONSTRAINT instance_pkey PRIMARY KEY (name);
