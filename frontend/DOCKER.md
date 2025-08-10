# Frontend Dockerfile - Next.js Configuration

This Dockerfile has been configured for Next.js (converted from Vite-based setup) following best practices.

## Key Features

### Next.js Specific Commands
- **Build Phase**: Uses `npm run build` which executes `next build`
- **Production Phase**: Uses `npm start` which executes `next start`

### Docker Best Practices
- **Multi-stage build** for optimal image size
- **Production dependencies only** in final stage
- **Non-root user** for security
- **Port 3000** exposed as required

### Build Artifacts
The Dockerfile correctly copies Next.js specific artifacts:
- `.next/` - Built Next.js application
- `public/` - Static assets
- `next.config.js` - Next.js configuration

### Usage
```bash
# Build the image
docker build -t leadgen-frontend .

# Run the container
docker run -p 3000:3000 leadgen-frontend
```

The application will be available at http://localhost:3000

## Package.json Scripts
The package.json already includes the necessary Next.js scripts:
- `"build": "next build"` - Build the application
- `"start": "next start"` - Start production server
- `"dev": "next dev"` - Development server