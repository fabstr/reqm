CREATE TABLE requirement_sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    placement_order INTEGER NOT NULL
);

CREATE TABLE requirement_set_metadata (
    id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    placement_order INTEGER NOT NULL,
    PRIMARY KEY (
        id,
        key
    )
);

CREATE TABLE requirements (
    set_id TEXT NOT NULL,
    id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    placement_order INTEGER NOT NULL,
    PRIMARY KEY (set_id, id, key)
);

CREATE TABLE links (
    from_set_id TEXT NOT NULL,
    from_id TEXT NOT NULL,
    to_set_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    placement_order  INTEGER NOT NULL,
    PRIMARY KEY (
        from_set_id,
        from_id,
        to_set_id,
        to_id
    ),
    CONSTRAINT from_link_constraint FOREIGN KEY (from_set_id, to_set_id)
        REFERENCES requirements (set_id, id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT to_link_constraint FOREIGN KEY (to_set_id, to_set_id)
        REFERENCES requirements (set_id, id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

