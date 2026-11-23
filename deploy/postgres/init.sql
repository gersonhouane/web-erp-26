-- A aplicação liga-se com um utilizador SEM privilégios de superutilizador,
-- porque um superutilizador ignora as políticas de Row-Level Security.
CREATE ROLE weberp LOGIN PASSWORD 'weberp';
CREATE DATABASE weberp OWNER weberp;
