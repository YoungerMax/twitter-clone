# Host Postgres using Docker

Replace `$PASSWORD` with your password of choice

```bash
$ docker run -p 5432:5432 -e POSTGRES_PASSWORD=$PASSWORD postgres:latest
```
