def sql_insert(table: str, data: dict) -> str:
    columns = "`, `".join(data.keys())
    values = ", ".join(f":{key}" for key in data)
    return f"INSERT INTO `{table}` (`{columns}`) VALUES ({values})"

def sql_update(table: str, data: dict, condition: str | None = None, id_name: str | None = None) -> str:
    set_clause = ", ".join(f"`{key}` = :{key}" for key in data if key != id_name)
    if id_name is not None:
        id_condition = f"`{id_name}` = :{id_name}"
        if condition is not None:
            condition = f"{condition} AND {id_condition}"
        else:
            condition = id_condition
    return f"UPDATE `{table}` SET {set_clause} WHERE {condition}"

