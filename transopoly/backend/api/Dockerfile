# Rails API for Transopoly (development image)
FROM ruby:3.4-slim

# build-essential: compiles native gems (pg, bcrypt)
# libpq-dev: lets the pg gem talk to Postgres
# libyaml-dev: needed by the psych gem (YAML)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends build-essential libpq-dev libyaml-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install gems   first so Docker can cache this layer
COPY Gemfile Gemfile.lock ./
RUN bundle install

COPY . .

# Run as a normal user (uid 1000 = your WSL user, so files created via the
# bind mount, e.g. migrations, are owned by you and not root)
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 3000

# db:prepare creates the database if missing, then runs pending migrations
CMD ["bash", "-c", "rm -f tmp/pids/server.pid && bin/rails db:prepare && bin/rails server -b 0.0.0.0 -p 3000"]
