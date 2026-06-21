# fastapi-nginx-demo

Small Tasks API behind an nginx reverse proxy — built to *feel* nginx
in front of FastAPI, not just read about it.

## Stack
- FastAPI + uvicorn, dependency-managed with `uv`
- nginx as reverse proxy (rate limiting, security headers, proxy headers)
- Docker Compose wiring it together

## Run locally without Docker (fast iteration)
```bash
uv sync
uv run uvicorn app.main:app --reload
```
Visit http://localhost:8000/docs

## Run the full stack (app + nginx) with Docker
```bash
docker compose up --build
```
Now nginx is the only exposed port. Hit the API **through nginx**, not
the app container directly:
```bash
curl -X POST http://localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"Learn nginx"}'
curl http://localhost:8080/tasks
curl http://localhost:8080/health
```

## Things to actually go verify yourself (this is the point of the exercise)
1. `docker compose ps` — confirm only `nginx-proxy` has a port mapped to
   your host. `tasks-api` should only show `8000/tcp` with no host
   binding. Try `curl http://localhost:8000/health` directly — it
   should fail to connect. That's the proxy doing its job: the app is
   never reachable except through nginx.
2. Rate limit test — fire 30 requests fast and watch some come back
   `429`:
   ```bash
   for i in $(seq 1 30); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/tasks; done
   ```
3. `docker compose logs nginx` vs `docker compose logs app` — see how
   nginx logs every request (access log) while the app only logs
   business events (task created/deleted). That separation is
   intentional.
4. Kill the app container (`docker compose stop app`) and curl nginx
   again — you'll get a 502. This is what "upstream down" looks like
   in production, and why the `depends_on: condition: service_healthy`
   matters.

## Next step (not done here — your homework)
SSL/TLS termination at nginx. Generate a self-signed cert with
`openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem`,
add a `listen 443 ssl;` server block, and redirect port 80 → 443. That's
the natural next layer on top of what's here.
