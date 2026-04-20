from app import app
from sql_generator import generate_sql_script


def test_generate_sql_script_creates_tables_and_foreign_keys() -> None:
    schema = {
        "tables": [
            {
                "id": "users",
                "name": "users",
                "columns": [
                    {"name": "id", "type": "INT", "primaryKey": True, "autoIncrement": True, "nullable": False},
                    {"name": "email", "type": "VARCHAR(255)", "unique": True, "nullable": False},
                ],
            },
            {
                "id": "posts",
                "name": "posts",
                "columns": [
                    {"name": "id", "type": "INT", "primaryKey": True, "autoIncrement": True, "nullable": False},
                    {"name": "user_id", "type": "INT", "nullable": False},
                ],
            },
        ],
        "relationships": [
            {
                "fromTableId": "posts",
                "toTableId": "users",
                "fromColumn": "user_id",
                "toColumn": "id",
                "onDelete": "CASCADE",
                "onUpdate": "CASCADE",
            }
        ],
    }

    sql = generate_sql_script(schema)

    assert "CREATE TABLE `users`" in sql
    assert "CREATE TABLE `posts`" in sql
    assert "FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)" in sql


def test_generate_sql_endpoint() -> None:
    client = app.test_client()

    response = client.post(
        "/api/generate-sql",
        json={
            "tables": [
                {
                    "id": "items",
                    "name": "items",
                    "columns": [{"name": "id", "type": "INT", "primaryKey": True, "autoIncrement": True}],
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert "CREATE TABLE `items`" in payload["sql"]


def test_generate_sql_endpoint_requires_table() -> None:
    client = app.test_client()

    response = client.post("/api/generate-sql", json={"tables": []})

    assert response.status_code == 400


def test_generate_sql_endpoint_rejects_invalid_column_type() -> None:
    client = app.test_client()

    response = client.post(
        "/api/generate-sql",
        json={
            "tables": [
                {
                    "id": "items",
                    "name": "items",
                    "columns": [{"name": "id", "type": "INT); DROP TABLE users; --"}],
                }
            ]
        },
    )

    assert response.status_code == 400
