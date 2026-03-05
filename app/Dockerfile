# Multi-stage Dockerfile for Laravel 12 with Inertia.js, React, and Reverb
# Optimized for production with Octane (FrankenPHP)

# ============================================================================
# Stage 1: PHP Dependencies
# ============================================================================
FROM composer:2 AS composer-deps

WORKDIR /app

# Copy composer files
COPY composer.json composer.lock ./

# Install PHP dependencies (no dev dependencies for production)
# --ignore-platform-reqs: composer:2 uses PHP 8.5 which breaks some packages
# that haven't declared PHP 8.5 support yet (e.g. nette/schema); the actual
# runtime is FrankenPHP PHP 8.3 which satisfies all requirements at run time.
RUN composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist \
    --optimize-autoloader \
    --ignore-platform-reqs

# ============================================================================
# Stage 2: Node.js Build
# ============================================================================
FROM node:20-alpine AS node-builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install Node dependencies
RUN npm ci

# Copy source files needed for build
COPY resources/ resources/
COPY public/ public/
COPY vite.config.ts tsconfig.json ./
COPY components.json ./

# Copy vendor packages needed by Vite for Filament theme compilation.
# The filament-awin-theme CSS entry point chains through multiple filament
# sub-packages (filament/support, filament/actions, filament/forms, etc.).
# Copying the full vendor/filament (~27MB) and vendor/resma directories is the
# simplest way to satisfy all transitive CSS imports without brittle file-level
# selectors.
COPY --from=composer-deps /app/vendor/filament vendor/filament
COPY --from=composer-deps /app/vendor/resma vendor/resma

# Build frontend assets
RUN npm run build

# ============================================================================
# Stage 3: Production Runtime
# ============================================================================
FROM dunglas/frankenphp:latest-php8.3 AS production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libzip-dev \
    zip \
    unzip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd zip intl

# Install Redis extension
RUN pecl install redis && docker-php-ext-enable redis

# Increase PHP upload limits to match Laravel validation rules (25MB processed / 50MB raw)
RUN printf 'upload_max_filesize = 50M\npost_max_size = 60M\n' \
    > /usr/local/etc/php/conf.d/uploads.ini

WORKDIR /app

# Copy application code
COPY --chown=www-data:www-data . .

# Copy built assets from node-builder stage
COPY --from=node-builder --chown=www-data:www-data /app/public/build /app/public/build

# Copy composer dependencies from composer-deps stage
COPY --from=composer-deps --chown=www-data:www-data /app/vendor /app/vendor

# Bring in composer binary to generate the optimized autoloader, then remove it
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Generate optimized autoloader
RUN composer dump-autoload --optimize

# Set permissions
RUN chown -R www-data:www-data /app/storage /app/bootstrap/cache \
    && chmod -R 775 /app/storage /app/bootstrap/cache

# Expose port
EXPOSE 8000

# Health check - use Laravel's built-in /up endpoint (available in Laravel 11+)
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -sf http://localhost:8000/up || exit 1

# Switch to www-data user
USER www-data

# Start Laravel Octane with FrankenPHP
CMD ["php", "artisan", "octane:frankenphp", "--host=0.0.0.0", "--port=8000"]

# ============================================================================
# Stage 4: Development
# ============================================================================
FROM dunglas/frankenphp:latest-php8.3 AS development

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    libzip-dev \
    zip \
    unzip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd zip intl

# Install Redis extension
RUN pecl install redis && docker-php-ext-enable redis

# Increase PHP upload limits to match Laravel validation rules (25MB processed / 50MB raw)
RUN printf 'upload_max_filesize = 50M\npost_max_size = 60M\n' \
    > /usr/local/etc/php/conf.d/uploads.ini

# Install Xdebug for development
RUN pecl install xdebug && docker-php-ext-enable xdebug

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Expose ports
EXPOSE 8000 8080

# Development command (will be overridden by docker-compose)
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000"]
