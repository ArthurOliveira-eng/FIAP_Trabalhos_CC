-- script_banco.sql
-- SCPRA - Aurora Siger
-- Banco: SQLite (equivalente ao Oracle)
-- No Oracle: troque AUTOINCREMENT por GENERATED ALWAYS AS IDENTITY,
-- REAL por NUMBER e TEXT por VARCHAR2

-- Tabela de modulos
CREATE TABLE IF NOT EXISTS modulos (
    id_modulo        TEXT PRIMARY KEY,
    nome             TEXT NOT NULL,
    tipo             TEXT NOT NULL,
    capacidade_kwh   REAL NOT NULL CHECK (capacidade_kwh > 0),
    consumo_medio_kw REAL NOT NULL CHECK (consumo_medio_kw >= 0),
    geracao_pico_kw  REAL NOT NULL CHECK (geracao_pico_kw >= 0)
);

-- Tabela de leituras dos sensores
CREATE TABLE IF NOT EXISTS leituras (
    id_leitura    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_modulo     TEXT NOT NULL REFERENCES modulos(id_modulo),
    data_hora     TEXT NOT NULL,
    consumo_kw    REAL NOT NULL CHECK (consumo_kw >= 0),
    geracao_kw    REAL NOT NULL CHECK (geracao_kw >= 0),
    temperatura_c REAL NOT NULL,
    o2_pct        REAL NOT NULL CHECK (o2_pct BETWEEN 0 AND 100),
    bateria_pct   REAL NOT NULL CHECK (bateria_pct BETWEEN 0 AND 100)
);

-- Dados iniciais dos modulos
INSERT OR IGNORE INTO modulos VALUES ('HAB-01', 'Habitat Principal',      'habitacao', 400, 9, 12);
INSERT OR IGNORE INTO modulos VALUES ('EST-01', 'Estufa Hidroponica',     'alimentos', 500, 12, 12);
INSERT OR IGNORE INTO modulos VALUES ('ENR-01', 'Usina Solar e Baterias', 'energia',   900, 3, 70);
INSERT OR IGNORE INTO modulos VALUES ('REC-01', 'Reciclagem de Agua e Ar','suporte',   350, 7, 12);
