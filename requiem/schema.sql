CREATE TABLE requirement_sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    filename TEXT NOT NULL
);

CREATE TABLE requirement_set_metadata (
    requirement_set_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    placement_order INTEGER NOT NULL,
    PRIMARY KEY (
        requirement_set_id,
        key
    )
);

CREATE TABLE requirements (
    requirement_set_id TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    placement_order INTEGER NOT NULL,
    PRIMARY KEY (
        requirement_set_id,
        requirement_id, key
    )
);

CREATE TABLE links (
    from_requirement_set_id TEXT NOT NULL,
    from_requirement_id TEXT NOT NULL,
    to_requirement_set_id TEXT NOT NULL,
    to_requirement_id TEXT NOT NULL,
    placement_order  INTEGER NOT NULL,
    PRIMARY KEY (
        from_requirement_set_id,
        from_requirement_id,
        to_requirement_set_id,
        to_requirement_id
    )
);

