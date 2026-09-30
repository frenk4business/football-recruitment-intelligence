from typing import Protocol

from football_intelligence.data.schema import TABLES, canonical_id


class Adapter(Protocol):
    provider: str

    def normalise(self, raw: dict, provenance_id: str) -> dict[str, list[dict]]: ...


class Rows:
    def __init__(self, provider: str, provenance_id: str, observed_on: str):
        self.provider = provider
        self.provenance_id = provenance_id
        self.observed_on = observed_on
        self.tables: dict[str, dict[str, dict]] = {t: {} for t in TABLES}

    def id(self, entity: str, value: str | int) -> str:
        return canonical_id(self.provider, entity, value)

    def add(self, table: str, provider_id: str | int, **fields) -> str:
        key = self.id(table, provider_id)
        row = dict(
            id=key,
            provider=self.provider,
            provider_id=str(provider_id),
            provenance_id=self.provenance_id,
            observed_on=self.observed_on,
            **fields,
        )
        if key in self.tables[table] and self.tables[table][key] != row:
            raise ValueError(f"Conflicting duplicate {table}: {provider_id}")
        self.tables[table][key] = row
        self.tables["provider_entity_map"][key] = dict(
            canonical_id=key,
            provider=self.provider,
            provider_entity_type=table,
            provider_entity_id=str(provider_id),
            provider_name=fields.get("name"),
        )
        return key

    def result(self):
        return {t: list(rows.values()) for t, rows in self.tables.items()}
