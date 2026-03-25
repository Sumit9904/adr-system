# Production Deployment Guide

Complete guide for deploying the ADR Management System to production.

## Pre-Deployment Checklist

### Security
- [ ] Change all default passwords
- [ ] Generate strong JWT_SECRET (min 32 characters)
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set secure cookie flags
- [ ] Enable rate limiting
- [ ] Review and tighten RLS policies
- [ ] Set up database backups
- [ ] Enable audit logging
- [ ] Configure firewall rules

### Configuration
- [ ] Set NODE_ENV=production
- [ ] Configure production database
- [ ] Set up email service (SendGrid, AWS SES, etc.)
- [ ] Configure file storage (AWS S3, Cloudinary)
- [ ] Set up monitoring (Sentry, New Relic)
- [ ] Configure logging service
- [ ] Set up CI/CD pipeline

## Deployment Options

### Option 1: Heroku (Recommended for Quick Start)

#### Backend Deployment

```bash
cd backend

# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create new app
heroku create adr-backend-api

# Add PostgreSQL (if not using Supabase)
# heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set NODE_ENV=production
heroku config:set SUPABASE_URL=your_supabase_url
heroku config:set SUPABASE_ANON_KEY=your_anon_key
heroku config:set SUPABASE_SERVICE_ROLE_KEY=your_service_key
heroku config:set JWT_SECRET=your_super_secret_key_min_32_chars
heroku config:set JWT_EXPIRE=7d
heroku config:set SMTP_HOST=smtp.sendgrid.net
heroku config:set SMTP_PORT=587
heroku config:set SMTP_USER=apikey
heroku config:set SMTP_PASSWORD=your_sendgrid_api_key
heroku config:set SMTP_FROM="ADR System <noreply@your-domain.com>"
heroku config:set FRONTEND_URL=https://your-frontend-domain.vercel.app

# Deploy
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a adr-backend-api
git push heroku main

# Check logs
heroku logs --tail

# Open app
heroku open
```

#### Frontend Deployment (Vercel)

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Follow prompts:
# - Setup and deploy: Yes
# - Which scope: Your account
# - Link to existing project: No
# - Project name: adr-frontend
# - Directory: ./
# - Override settings: No

# Set environment variables in Vercel dashboard:
# REACT_APP_API_URL=https://adr-backend-api.herokuapp.com/api

# For production deployment
vercel --prod
```

### Option 2: AWS (Enterprise)

#### Backend on AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
cd backend
eb init -p node.js-16 adr-backend

# Create environment
eb create adr-production

# Set environment variables
eb setenv NODE_ENV=production \
  SUPABASE_URL=your_url \
  SUPABASE_SERVICE_ROLE_KEY=your_key \
  JWT_SECRET=your_secret \
  SMTP_HOST=email-smtp.us-east-1.amazonaws.com \
  SMTP_PORT=587 \
  SMTP_USER=your_ses_user \
  SMTP_PASSWORD=your_ses_password

# Deploy
eb deploy

# Check status
eb status

# View logs
eb logs
```

#### Frontend on AWS S3 + CloudFront

```bash
cd frontend

# Build for production
npm run build

# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create S3 bucket
aws s3 mb s3://adr-frontend

# Enable static website hosting
aws s3 website s3://adr-frontend \
  --index-document index.html \
  --error-document index.html

# Upload build files
aws s3 sync build/ s3://adr-frontend --acl public-read

# Create CloudFront distribution for HTTPS and caching
aws cloudfront create-distribution \
  --origin-domain-name adr-frontend.s3.amazonaws.com
```

### Option 3: DigitalOcean

#### Create Droplet

```bash
# SSH into droplet
ssh root@your_droplet_ip

# Update system
apt update && apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install PM2 for process management
npm install -g pm2

# Install Nginx
apt install -y nginx

# Clone repository
git clone https://github.com/your-repo/adr-system.git
cd adr-system
```

#### Setup Backend

```bash
cd backend
npm install

# Create .env file
nano .env
# Add all production environment variables

# Start with PM2
pm2 start server.js --name adr-backend
pm2 save
pm2 startup
```

#### Setup Frontend

```bash
cd ../frontend
npm install
npm run build

# Copy build to Nginx
cp -r build/* /var/www/adr-frontend/
```

#### Configure Nginx

```bash
nano /etc/nginx/sites-available/adr-system
```

```nginx
# Backend
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Frontend
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    root /var/www/adr-frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/adr-system /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

#### Setup SSL with Let's Encrypt

```bash
apt install -y certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com -d www.your-domain.com -d api.your-domain.com

# Auto-renewal is set up automatically
```

### Option 4: Docker Deployment

#### Create Dockerfiles

**backend/Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 5000

CMD ["node", "server.js"]
```

**frontend/Dockerfile:**
```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - NODE_ENV=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - FRONTEND_URL=${FRONTEND_URL}
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

#### Deploy with Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Email Service Setup

### SendGrid (Recommended)

```bash
# Sign up at https://sendgrid.com
# Create API key
# Set environment variables:
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
```

### AWS SES

```bash
# Verify domain in AWS SES
# Create SMTP credentials
# Set environment variables:
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your_ses_smtp_username
SMTP_PASSWORD=your_ses_smtp_password
```

### Gmail (Development Only)

```bash
# Enable 2FA on Gmail account
# Generate App Password
# Set environment variables:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Monitoring & Logging

### Sentry for Error Tracking

```bash
npm install @sentry/node @sentry/tracing

# backend/server.js
const Sentry = require("@sentry/node");
const Tracing = require("@sentry/tracing");

Sentry.init({
  dsn: "your_sentry_dsn",
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});

app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.errorHandler());
```

### PM2 Monitoring

```bash
# Install PM2 Plus
pm2 install pm2-logrotate

# Configure log rotation
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7

# Monitor
pm2 monit
```

## Database Backup

### Supabase Backup

```bash
# Supabase automatically backs up your database
# Download manual backup:
pg_dump "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres" > backup.sql

# Restore:
psql "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres" < backup.sql
```

### Automated Backups

```bash
# Create backup script
nano /root/backup-db.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres" > /backups/adr_$DATE.sql
find /backups -name "adr_*.sql" -mtime +7 -delete
```

```bash
chmod +x /root/backup-db.sh

# Schedule with cron (daily at 2 AM)
crontab -e
0 2 * * * /root/backup-db.sh
```

## Performance Optimization

### Backend

1. **Enable Compression**
```javascript
const compression = require('compression');
app.use(compression());
```

2. **Enable Caching**
```javascript
const redis = require('redis');
const client = redis.createClient();
```

3. **Database Indexes**
```sql
-- Already created in migration, verify they exist
SELECT * FROM pg_indexes WHERE tablename = 'adr_reports';
```

### Frontend

1. **Code Splitting**
```javascript
const AdminDashboard = React.lazy(() => import('./pages/admin/Dashboard'));
```

2. **Image Optimization**
- Use WebP format
- Implement lazy loading
- Use CDN for static assets

3. **Bundle Optimization**
```bash
npm run build
npx webpack-bundle-analyzer build/static/js/*.js
```

## Security Hardening

### Rate Limiting

```bash
npm install express-rate-limit

# backend/server.js
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP'
});

app.use('/api/', limiter);
```

### Helmet for Security Headers

```bash
npm install helmet

# backend/server.js
const helmet = require('helmet');
app.use(helmet());
```

### HTTPS Enforcement

```javascript
app.use((req, res, next) => {
  if (req.header('x-forwarded-proto') !== 'https' && process.env.NODE_ENV === 'production') {
    res.redirect(`https://${req.header('host')}${req.url}`);
  } else {
    next();
  }
});
```

## Health Checks

```javascript
// backend/routes/health.js
router.get('/health', async (req, res) => {
  try {
    await supabase.from('users').select('count').limit(1);
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime()
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});
```

## Rollback Procedure

```bash
# If deployment fails, rollback:

# Heroku
heroku rollback

# AWS Elastic Beanstalk
eb deploy --version previous-version

# PM2
pm2 reload adr-backend --update-env

# Docker
docker-compose down
docker-compose up -d --build --force-recreate
```

## Post-Deployment Verification

1. **Check API Health**
```bash
curl https://api.your-domain.com/api/health
```

2. **Test Authentication**
```bash
curl -X POST https://api.your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@adr-system.com","password":"Admin@123"}'
```

3. **Verify Database Connection**
```bash
curl https://api.your-domain.com/api/drugs
```

4. **Test Email Notifications**
- Create test user
- Submit test report
- Verify email received

5. **Check Logs**
```bash
# Heroku
heroku logs --tail

# PM2
pm2 logs

# Docker
docker-compose logs -f
```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check system resources
- Review security alerts

**Weekly:**
- Review audit logs
- Check database performance
- Update dependencies
- Backup verification

**Monthly:**
- Security updates
- Performance review
- Cost optimization
- User feedback review

## Support & Troubleshooting

### Common Issues

**502 Bad Gateway:**
- Check if backend is running
- Verify PM2 process status
- Check Nginx configuration

**Database Connection Failed:**
- Verify Supabase credentials
- Check network connectivity
- Review RLS policies

**Email Not Sending:**
- Verify SMTP credentials
- Check spam folder
- Review email service logs

### Getting Help

- Check logs first
- Review documentation
- Search GitHub issues
- Contact support

## Conclusion

Your ADR Management System is now deployed and ready for production use. Monitor the system regularly and keep all components up to date for optimal security and performance.
