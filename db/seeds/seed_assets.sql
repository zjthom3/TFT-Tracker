insert into assets (id, ticker, name, type, exchange, created_at, updated_at)
values
    (gen_random_uuid(), 'NVDA', 'NVIDIA Corporation', 'stock', 'NASDAQ', now(), now())
on conflict do nothing;

insert into assets (id, ticker, name, type, exchange, created_at, updated_at)
values
    (gen_random_uuid(), 'BTC-USD', 'Bitcoin / USD', 'crypto', 'CRYPTO', now(), now())
on conflict do nothing;
