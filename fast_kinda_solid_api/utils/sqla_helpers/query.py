from sqlalchemy import Column, Select, and_, asc, desc, or_, select


def select_with_cursor_pagination(
    stmt: Select,
    sort_col: Column,
    unique_col: Column,
    ascending: bool = True,
    last_sort_value=None,
    last_unique_value=None,
    page_size: int = 10,
):
    subquery = stmt.subquery()
    sort_order = asc if ascending else desc

    subquery_sort_col = subquery.c[sort_col.name]
    subquery_unique_col = subquery.c[unique_col.name]

    pagination_stmt = select(subquery).order_by(sort_order(subquery_sort_col), sort_order(subquery_unique_col))

    if last_sort_value is not None and last_unique_value is not None:
        condition = or_(
            (subquery_sort_col > last_sort_value if ascending else subquery_sort_col < last_sort_value),
            and_(
                subquery_sort_col == last_sort_value,
                (subquery_unique_col > last_unique_value if ascending else subquery_unique_col < last_unique_value),
            ),
        )
        pagination_stmt = pagination_stmt.where(condition)

    return pagination_stmt.limit(page_size)


__all__ = [
    "select_with_cursor_pagination",
]
