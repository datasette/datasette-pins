.mode box
.header on
.bail on
create table pinned as
  select
    value ->> 'id' as id,
    value ->> 'title' as title,
    rowid as order_idx
  from json_each('[
    {"id": "a", "title": "xxx"},
    {"id": "b", "title": "yyy"},
    {"id": "c", "title": "zzz"}
  ]');


select * from pinned;

with x as (
  select
    value ->> 'id' as id,
    value ->> 'new_order_idx' as new_order_idx,
    rowid as order_idx
  from json_each('[
    {"id": "a", "new_order_idx": 2},
    {"id": "b", "new_order_idx": 3},
    {"id": "c", "new_order_idx": 1},
    {"id": "not_exist", "new_order_idx": 4}
  ]')
)
update pinned
  set order_idx = new_order_idx
  from x
  where pinned.id = x.id;

select * from pinned;
