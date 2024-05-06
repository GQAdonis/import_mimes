# Import MIME Types

This script imports all known MIME Types from https://mimetype.io/all-types and inserts
them into the `mime_type` table in a Supabase database having 
the following schema:

```sql
create table
  public.mime_type (
    id uuid not null default gen_random_uuid (),
    mime text not null,
    name text null,
    extensions text[] not null,
    created_at timestamp with time zone not null default now(),
    constraint mime_type_pkey primary key (id),
    constraint mime_type_mime_key unique (mime)
  );
```

