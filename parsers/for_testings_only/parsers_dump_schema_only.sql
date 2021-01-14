--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5 (Ubuntu 12.5-1.pgdg18.04+1)
-- Dumped by pg_dump version 12.5 (Ubuntu 12.5-1.pgdg18.04+1)

-- Started on 2021-01-14 14:16:25 +07

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP TRIGGER IF EXISTS user_agent_update_trg ON public.user_agent;
ALTER TABLE IF EXISTS ONLY public.user_agent DROP CONSTRAINT IF EXISTS user_agent_title_key;
ALTER TABLE IF EXISTS ONLY public.user_agent DROP CONSTRAINT IF EXISTS user_agent_pkey;
ALTER TABLE IF EXISTS public.user_agent ALTER COLUMN user_agent_id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.user_agent_user_agent_id_seq;
DROP TABLE IF EXISTS public.user_agent;
DROP FUNCTION IF EXISTS public.user_agent_update_func();
DROP FUNCTION IF EXISTS public.user_agent_insert_func(in_software text, in_title text, in_version text, in_os text, in_hardware text, in_popularity text);
--
-- TOC entry 205 (class 1255 OID 23779)
-- Name: user_agent_insert_func(text, text, text, text, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_agent_insert_func(in_software text, in_title text, in_version text, in_os text, in_hardware text, in_popularity text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    p_user_agent_id INTEGER;
BEGIN
    IF NOT EXISTS (SELECT title FROM user_agent WHERE title=in_title) THEN
        WITH cte AS (
            INSERT INTO user_agent (
                software,
                title,
                version,
                os,
                hardware,
                popularity
            ) VALUES (
                in_software,
                in_title,
                in_version,
                in_os,
                in_hardware,
                in_popularity
            ) RETURNING user_agent_id
        ) SELECT cte.user_agent_id INTO p_user_agent_id FROM cte;
    ELSE
        p_user_agent_id := 0;
    END IF;

    RETURN p_user_agent_id;
END;
$$;


--
-- TOC entry 204 (class 1255 OID 23646)
-- Name: user_agent_update_func(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_agent_update_func() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.update_tz = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 203 (class 1259 OID 23632)
-- Name: user_agent; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_agent (
    user_agent_id integer NOT NULL,
    software text NOT NULL,
    title text NOT NULL,
    version text,
    os text,
    hardware text,
    popularity text,
    successes integer DEFAULT 0 NOT NULL,
    errors integer DEFAULT 0 NOT NULL,
    insert_tz timestamp with time zone DEFAULT now() NOT NULL,
    update_tz timestamp with time zone
);


--
-- TOC entry 202 (class 1259 OID 23630)
-- Name: user_agent_user_agent_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_agent_user_agent_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 2948 (class 0 OID 0)
-- Dependencies: 202
-- Name: user_agent_user_agent_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_agent_user_agent_id_seq OWNED BY public.user_agent.user_agent_id;


--
-- TOC entry 2808 (class 2604 OID 23635)
-- Name: user_agent user_agent_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_agent ALTER COLUMN user_agent_id SET DEFAULT nextval('public.user_agent_user_agent_id_seq'::regclass);


--
-- TOC entry 2813 (class 2606 OID 23643)
-- Name: user_agent user_agent_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_agent
    ADD CONSTRAINT user_agent_pkey PRIMARY KEY (user_agent_id);


--
-- TOC entry 2815 (class 2606 OID 23645)
-- Name: user_agent user_agent_title_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_agent
    ADD CONSTRAINT user_agent_title_key UNIQUE (title);


--
-- TOC entry 2816 (class 2620 OID 23647)
-- Name: user_agent user_agent_update_trg; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER user_agent_update_trg BEFORE UPDATE ON public.user_agent FOR EACH ROW EXECUTE FUNCTION public.user_agent_update_func();


-- Completed on 2021-01-14 14:16:28 +07

--
-- PostgreSQL database dump complete
--

